import asyncio
import httpx
from app.client import get_client
from app.config import AppConfig

# 尝试连接本地 API 的配置
API_HOST = "http://localhost"
API_PORT = 8000 

async def fetch_from_api():
    """尝试从运行中的主程序获取列表 (避免文件锁)"""
    url = f"{API_HOST}:{API_PORT}"
    print(f"[*] 尝试连接本地服务: {url} ...")
    
    async with httpx.AsyncClient(timeout=2.0, trust_env=False) as client:
        try:
            # 1. 登录获取 Token
            # 注意：这里假设默认密码或从配置读取。为了简化，这里先尝试默认。
            # 实际场景最好复用 AppConfig
            pwd = AppConfig.WEB_PASSWORD or "admin"
            resp = await client.post(f"{url}/token", data={"username": "admin", "password": pwd})
            if resp.status_code != 200:
                return None
            
            token = resp.json().get("access_token")
            
            # 2. 获取列表
            resp = await client.get(f"{url}/api/chats", headers={"Authorization": f"Bearer {token}"})
            if resp.status_code == 200:
                return resp.json()
                
        except (httpx.ConnectError, httpx.TimeoutException):
            return None
            
    return None

async def main():
    # 优先尝试 API 方式
    api_chats = await fetch_from_api()
    
    if api_chats:
        print("✅ 检测到主程序正在运行，通过 API 获取列表 (无文件锁风险)")
        print("\n" + "="*50)
        print(f"{ 'ID':<20} | {'类型':<10} | {'名称'}")
        print("="*50)
        for chat in api_chats:
            print(f"{chat['id']:<20} | {chat['type']:<10} | {chat['name']}")
    else:
        print("⚠️  主程序未运行或无法连接，尝试直接读取 Session 文件...")
        print("[*] 正在获取对话列表，请稍候...")
        
        # 降级到直接连接模式
        client = await get_client()
        
        print("\n" + "="*50)
        print(f"{ 'ID':<20} | {'类型':<10} | {'名称'}")
        print("="*50)
        
        async for dialog in client.iter_dialogs():
            if dialog.is_group or dialog.is_channel:
                type_str = "群组" if dialog.is_group else "频道"
                print(f"{dialog.id:<20} | {type_str:<10} | {dialog.title}")
            
    print("="*50)
    print("\n[?] 请找到你的目标群组，将对应的 ID (通常以 -100 开头) 复制到 .env 文件的 CHAT_ID 字段中。")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (ConnectionError, ConnectionResetError, asyncio.IncompleteReadError, OSError) as e:
        print(f"\n❌ 连接失败: {e}")
        if not AppConfig.PROXY_HOST:
            print("\n⚠️  检测到您可能没有配置代理。Telegram 通常需要翻墙才能连接。")
            print("👉 请运行脚本配置代理: bash setup_proxy.sh")
            print("   或者手动在 .env 文件中添加 PROXY_HOST, PROXY_PORT 等配置。")
        else:
            print("\n⚠️  代理配置可能无效，请检查您的代理设置。")
            print(f"   当前配置: {AppConfig.PROXY_TYPE}://{AppConfig.PROXY_HOST}:{AppConfig.PROXY_PORT}")

