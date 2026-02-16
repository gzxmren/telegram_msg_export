import os
import yaml
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, validator
from dotenv import load_dotenv

load_dotenv()

class ExporterSettings(BaseModel):
    path: str
    format: str = "csv"

class TaskModel(BaseModel):
    name: str
    enable: bool = True
    sources: List[Any] = []
    keywords: List[str] = []
    output: ExporterSettings

    @validator('sources', pre=True)
    @classmethod
    def normalize_sources(cls, v):
        # 兼容配置中写成单值的情况，自动转为列表
        return [v] if not isinstance(v, list) else v

class SystemSettings(BaseModel):
    loop_interval: int = 300
    web_port: int = 8000
    web_host: str = "0.0.0.0"

class AppConfig:
    """集中式配置管理"""
    
    # 核心环境变量
    API_ID: int = int(os.getenv("API_ID", 0))
    API_HASH: str = os.getenv("API_HASH", "")
    PHONE: str = os.getenv("PHONE", "")
    WEB_PASSWORD: str = os.getenv("WEB_PASSWORD", "admin")

    # 代理配置
    PROXY_TYPE: str = os.getenv("PROXY_TYPE", "")  # SOCKS5, HTTP
    PROXY_HOST: str = os.getenv("PROXY_HOST", "")
    PROXY_PORT: int = int(os.getenv("PROXY_PORT", 0))
    PROXY_USER: str = os.getenv("PROXY_USER", "")
    PROXY_PASS: str = os.getenv("PROXY_PASS", "")

    # 动态加载内容
    tasks: List[TaskModel] = []
    settings: SystemSettings = SystemSettings()
    
    _last_mtime: float = 0
    _config_path: str = "config.yaml"

    @classmethod
    def load(cls, path: str = "config.yaml"):
        from app.logger import logger  # 延迟导入避免循环引用

        cls._config_path = path
        if not os.path.exists(path):
            return False
            
        mtime = os.path.getmtime(path)
        if mtime <= cls._last_mtime:
            return False

        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
                
            # 使用 Pydantic 校验并解析内容
            # 先构建临时对象验证，成功后再赋值，保证原子性
            new_settings = SystemSettings(**data.get('settings', {}))
            
            raw_tasks = data.get('tasks', [])
            new_tasks = [TaskModel(**t) for t in raw_tasks if t.get('enable', True)]
            
            # 验证通过，更新状态
            cls.settings = new_settings
            cls.tasks = new_tasks
            cls._last_mtime = mtime
            return True

        except Exception as e:
            logger.error(f"❌ 配置文件重载失败 (保持旧配置): {e}")
            return False

    @classmethod
    def validate_env(cls):
        if not cls.API_ID or not cls.API_HASH or not cls.PHONE:
            raise ValueError("请在 .env 文件中完整配置 API_ID, API_HASH 和 PHONE")

# 初始加载
AppConfig.load()
