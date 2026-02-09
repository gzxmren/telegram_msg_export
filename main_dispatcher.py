import asyncio
import argparse
from app.config import Config
from app.dispatcher import Dispatcher
from app.client import get_client
from app.logger import logger

async def main():
    parser = argparse.ArgumentParser(description="TG-Link-Dispatcher Daemon")
    parser.add_argument("--daemon", action="store_true", help="以守护进程模式运行")
    parser.add_argument("--interval", type=int, help="轮询间隔 (秒)")
    args = parser.parse_args()

    try:
        Config.validate()
        interval = args.interval or Config.SETTINGS.get('loop_interval', 300)
        if interval < 300 and args.daemon:
            interval = 300

        dispatcher = Dispatcher()
        
        if not args.daemon:
            logger.info("执行单次同步任务...")
            await dispatcher.run_cycle()
            return

        # Daemon 模式：保持长连接以提高性能和稳定性
        logger.info(f"进入守护模式，间隔 {interval}s")
        client = await get_client()
        
        try:
            while True:
                await dispatcher.run_cycle(client=client)
                logger.info(f"休眠中，等待下一次同步...")
                await asyncio.sleep(interval)
        except Exception as e:
            logger.error(f"守护进程异常: {e}")
        finally:
            if client: await client.disconnect()

    except Exception as e:
        logger.error(f"启动失败: {e}")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
