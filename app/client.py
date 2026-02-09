from telethon import TelegramClient
from app.config import AppConfig as Config
import sys

async def get_client():
    """初始化并返回已连接的 Telegram 客户端"""
    # session 文件命名为 'tg_exporter'，会在当前目录生成 tg_exporter.session
    client = TelegramClient('tg_exporter', Config.API_ID, Config.API_HASH)
    
    print(f"[*] 正在尝试连接 Telegram (手机号: {Config.PHONE})...")
    
    try:
        # start() 会处理登录：
        # 1. 如果有 session 文件，直接登录
        # 2. 如果没有，会提示输入手机验证码 (和两步验证密码)
        await client.start(phone=Config.PHONE)
    except Exception as e:
        print(f"[!] 登录失败: {e}")
        sys.exit(1)
        
    if not await client.is_user_authorized():
        print("[!] 授权失败，请检查手机号或验证码。")
        sys.exit(1)
        
    me = await client.get_me()
    print(f"[+] 登录成功! 当前账号: {me.first_name} (ID: {me.id})")
    return client
