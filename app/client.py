from telethon import TelegramClient
from app.config import AppConfig as Config
from app.logger import logger
import sys
import asyncio

async def get_client():
    """初始化并返回已连接的 Telegram 客户端"""
    # 配置代理
    proxy = None
    if Config.PROXY_HOST and Config.PROXY_PORT:
        try:
            import python_socks
        except ImportError:
            logger.error("❌ 未找到 python-socks 库，无法使用代理。请运行: pip install python-socks[asyncio]")
            sys.exit(1)
        
        p_type = python_socks.ProxyType.SOCKS5
        if Config.PROXY_TYPE and Config.PROXY_TYPE.upper() == "HTTP":
            p_type = python_socks.ProxyType.HTTP

        proxy = (p_type, Config.PROXY_HOST, Config.PROXY_PORT, True, Config.PROXY_USER or None, Config.PROXY_PASS or None)
        logger.info(f"[*] 使用代理: {Config.PROXY_TYPE or 'SOCKS5'}://{Config.PROXY_HOST}:{Config.PROXY_PORT}")

    # session 文件命名为 'tg_exporter'
    client = TelegramClient('tg_exporter', Config.API_ID, Config.API_HASH, proxy=proxy)
    
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
