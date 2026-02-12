import asyncio
import httpx
import subprocess
from app.client import get_client
from app.config import AppConfig

# 尝试连接本地 API 的配置
API_HOST = "http://127.0.0.1"
API_PORT = 8000 

def is_service_running():
    """检查 Systemd 服务是否正在运行"""
    try:
        # 检查名为 tg-export 的服务状态
        result = subprocess.run(['systemctl', 'is-active', '--quiet', 'tg-export'], capture_output=False)
        return result.returncode == 0
    except:
        return False

async def fetch_from_api():
    """尝试从运行中的主程序获取列表 (避免文件锁)"""
    url = f"{API_HOST}:{API_PORT}"
    
    async with httpx.AsyncClient(timeout=3.0, trust_env=False) as client:
        try:
            # 1. 登录获取 Token
            pwd = AppConfig.WEB_PASSWORD
            resp = await client.post(f"{url}/token", data={"username": "admin", "password": pwd})
            if resp.status_code != 200:
                return None
            
            token = resp.json().get("access_token")
            
            # 2. 获取列表
            resp = await client.get(f"{url}/api/chats", headers={"Authorization": f"Bearer {token}"})
            if resp.status_code == 200:
                return resp.json()
                
        except Exception:
            return None
            
    return None

async def main():
    print(f"[*] 正在获取对话列表...")
    
    # 1. 优先尝试通过 API 获取 (无锁风险)
    api_chats = await fetch_from_api()
    if api_chats:
        print("✅ 检测到主程序正在运行，已通过 API 获取列表。")
        print("\n" + "="*50)
        print(f"{ 'ID':<20} | {'类型':<10} | {'名称'}")
        print("="*50)
        for chat in api_chats:
            print(f"{chat['id']:<20} | {chat['type']:<10} | {chat['name']}")
        print("="*50)
        return

    # 2. 如果 API 不通，检查服务是否在运行
    if is_service_running():
        print("\n❌ 错误: 后台服务 'tg-export' 正在运行，锁定了 Session 数据库。")
        print("👉 请通过浏览器访问管理面板查看列表: http://<服务器IP>:8000")
        print("👉 或者先停止后台服务: ./manage.sh stop")
        return

    # 3. 只有在服务没运行的情况下，才尝试直接读取文件
    print("⚠️  主程序未运行，尝试直接读取 Session 文件...")
    try:
        client = await get_client()
        
        print("\n" + "="*50)
        print(f"{ 'ID':<20} | {'类型':<10} | {'名称'}")
        print("="*50)
        
        async for dialog in client.iter_dialogs():
            if dialog.is_group or dialog.is_channel:
                type_str = "群组" if dialog.is_group else "频道"
                print(f"{dialog.id:<20} | {type_str:<10} | {dialog.title}")
        print("="*50)
    except Exception as e:
        if "database is locked" in str(e):
            print("\n❌ 数据库仍被锁定。可能有其他残留进程在占用。")
            print("👉 尝试清理进程: pkill -f main_dispatcher.py")
        else:
            print(f"\n❌ 获取列表失败: {e}")

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
