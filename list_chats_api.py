import asyncio
import httpx
from app.config import AppConfig as Config

# 加载配置以获取端口和密码
Config.load()

API_URL = f"http://localhost:{Config.settings.web_port}"
USERNAME = "admin"
PASSWORD = Config.WEB_PASSWORD

async def get_token(client):
    """获取 API 访问令牌"""
    response = await client.post(f"{API_URL}/token", data={
        "username": USERNAME,
        "password": PASSWORD
    })
    
    if response.status_code != 200:
        print(f"❌ 登录失败: {response.status_code} - {response.text}")
        return None
        
    return response.json().get("access_token")

async def list_chats():
    print(f"[*] 正在尝试连接本地 API: {API_URL} ...")
    
    async with httpx.AsyncClient() as client:
        # 1. 获取 Token
        try:
            token = await get_token(client)
            if not token:
                return
        except httpx.ConnectError:
            print(f"❌ 无法连接到服务: {API_URL}")
            print("💡 请确保主程序 (main_dispatcher.py) 正在后台运行且开启了 --web")
            return

        # 2. 获取对话列表
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.get(f"{API_URL}/api/chats", headers=headers)
        
        if response.status_code != 200:
            if response.status_code == 503:
                print("⚠️  主程序尚未完成 Telegram 连接，请稍后再试。")
            else:
                print(f"❌ 获取列表失败: {response.status_code} - {response.text}")
            return

        chats = response.json()
        
        # 3. 打印结果
        print("
" + "="*50)
        print(f"{ 'ID':<20} | {'类型':<10} | {'名称'}")
        print("="*50)
        
        for chat in chats:
            print(f"{chat['id']:<20} | {chat['type']:<10} | {chat['name']}")
            
        print("="*50)
        print("
[?] 请找到你的目标群组，将对应的 ID (通常以 -100 开头) 复制到 .env 文件的 CHAT_ID 字段中。")

if __name__ == '__main__':
    asyncio.run(list_chats())
