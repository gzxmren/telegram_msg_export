import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
import yaml

from app.monitor import monitor
from app.config import AppConfig as Config

# --- 安全配置 ---
SECRET_KEY = os.getenv("WEB_SECRET_KEY", secrets.token_hex(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # 24小时
ADMIN_PASSWORD_HASH = os.getenv("WEB_PASSWORD_HASH") # 这里需要初始设置

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI(title="TG-Link-Dispatcher Admin")

class Token(BaseModel):
    access_token: str
    token_type: str

# --- 辅助函数 ---
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None: raise credentials_exception
    except JWTError:
        raise credentials_exception
    return username

# --- 路由 ---

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    # 简单的单用户模式：
    # 如果环境变量没设哈希，默认密码为 'admin' (仅用于演示，强烈建议引导用户设置)
    env_hash = os.getenv("WEB_ADMIN_PASSWORD_HASH")
    if not env_hash:
        # 默认密码 admin 的哈希
        env_hash = "$2b$12$6qg6G08pXg5o8D8o8X8o8Oe8Q8Q8Q8Q8Q8Q8Q8Q8Q8Q8Q8Q8Q8Q8G" 
        # 本地测试方便，实际在 .env 中设置
    
    # 获取 .env 里的密码原文进行校验
    correct_password = Config.WEB_PASSWORD
    
    if form_data.username != "admin" or form_data.password != correct_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": form_data.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/stats")
async def get_stats(user: str = Depends(get_current_user)):
    return monitor.to_dict()

@app.get("/api/rules")
async def get_rules(user: str = Depends(get_current_user)):
    with open("rules.yaml", 'r', encoding='utf-8') as f:
        return f.read()

@app.post("/api/rules")
async def save_rules(data: dict, user: str = Depends(get_current_user)):
    try:
        content = data.get("content")
        # 验证 YAML 格式
        yaml.safe_load(content)
        with open("rules.yaml", 'w', encoding='utf-8') as f:
            f.write(content)
        monitor.add_log("⚙️ 链接清洗规则 (rules.yaml) 已更新")
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/config")
async def get_config(user: str = Depends(get_current_user)):
    with open("config.yaml", 'r', encoding='utf-8') as f:
        return f.read() # 改为返回原始文本，方便前端编辑器展示

@app.post("/api/config")
async def save_config(data: dict, user: str = Depends(get_current_user)):
    try:
        content = data.get("content")
        yaml.safe_load(content)
        with open("config.yaml", 'w', encoding='utf-8') as f:
            f.write(content)
        # 强制通知 Config 模块发现变动
        Config.load()
        monitor.add_log("⚙️ 任务配置文件 (config.yaml) 已更新，下个周期将应用")
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/", response_class=HTMLResponse)
async def index():
    # 返回简易的前端代码 (将在后面细化为美观的版本)
    with open("app/static/index.html", "r", encoding="utf-8") as f:
        return f.read()

# 确保文件夹存在
os.makedirs("app/static", exist_ok=True)
