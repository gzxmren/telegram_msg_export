import asyncio
import argparse
import uvicorn
from app.config import AppConfig as Config
from app.dispatcher import Dispatcher
from app.client import get_client
from app.logger import logger
from app.web import app
from app.monitor import monitor

async def run_web_server():
    """启动 Web 控制面板服务器"""
    config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="warning")
    server = uvicorn.Server(config)
    await server.serve()

async def main():
    parser = argparse.ArgumentParser(description="TG-Link-Dispatcher Daemon with Web UI")
    parser.add_argument("--daemon", action="store_true", help="以守护进程模式运行")
    parser.add_argument("--web", action="store_true", help="启动 Web 控制面板 (默认端口 8000)")
    parser.add_argument("--interval", type=int, help="轮询间隔 (秒)")
    args = parser.parse_args()

    try:
        Config.validate_env()
        interval = args.interval or Config.settings.loop_interval
        if interval < 300 and args.daemon:
            interval = 300

        dispatcher = Dispatcher()
        
        # 如果开启了 Web 模式，在后台任务中启动服务器
        if args.web:
            logger.info("🚀 正在启动 Web 控制面板: http://localhost:8000")
            asyncio.create_task(run_web_server())

        if not args.daemon:
            logger.info("执行单次同步任务...")
            await dispatcher.run_cycle()
            # 单次运行如果在 web 模式下，可能需要保持运行一段时间
            if args.web:
                logger.info("Web 面板保持运行中，按下 Ctrl+C 退出。")
                while True: await asyncio.sleep(3600)
            return

        # Daemon 模式
        logger.info(f"进入守护模式，间隔 {interval}s")
        monitor.update_stats(status="Idle")
        client = await get_client()
        
        try:
            while True:
                await dispatcher.run_cycle(client=client)
                logger.info(f"休眠中，等待下一次同步...")
                await asyncio.sleep(interval)
        except Exception as e:
            logger.error(f"守护进程异常: {e}")
            monitor.update_stats(status="Error")
        finally:
            if client: await client.disconnect()

    except Exception as e:
        logger.error(f"启动失败: {e}")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
