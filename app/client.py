from telethon import TelegramClient
from app.config import AppConfig as Config
from app.logger import logger
import sys
import asyncio

async def get_client():
    """初始化并返回已连接的 Telegram 客户端"""
    # session 文件命名为 'tg_exporter'
    client = TelegramClient('tg_exporter', Config.API_ID, Config.API_HASH)
    
    logger.info(f"[*] 正在尝试连接 Telegram (手机号: {Config.PHONE})...")
    
    try:
        # start() 会处理登录和初始时间同步
        await client.start(phone=Config.PHONE)
    except Exception as e:
        logger.error(f"[!] 登录失败: {e}")
        if "Security error" in str(e):
            logger.error("❌ 检测到严重的时间同步问题！请确保您的服务器系统时间与北京时间一致。")
        raise e
        
    if not await client.is_user_authorized():
        logger.error("[!] 授权失败，请检查手机号或验证码。")
        sys.exit(1)
        
    me = await client.get_me()
    logger.info(f"[+] 登录成功! 当前账号: {me.first_name} (ID: {me.id})")
    return client
