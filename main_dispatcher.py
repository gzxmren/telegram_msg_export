import asyncio
import argparse
import uvicorn
from app.config import AppConfig as Config
from app.dispatcher import Dispatcher
from app.client import get_client
from app.logger import logger
from app.web import app
import app.web as web_app_module
from app.monitor import monitor
import logging

class MonitorLogHandler(logging.Handler):
    """将日志转发到 Monitor 的实时流水中"""
    def emit(self, record):
        try:
            msg = self.format(record)
            # 避免重复记录 (Dispatcher 可能会显式调用 monitor.add_log)
            # 这里均通过 logging 统一接管
            monitor.add_log(msg)
        except Exception:
            self.handleError(record)

async def run_web_server():
    """启动 Web 控制面板服务器"""
    # 禁用 Uvicorn 信号处理，防止干扰主程序守护进程
    config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="warning", loop="asyncio")
    server = uvicorn.Server(config)
    
    # 手动禁用信号处理
    server.install_signal_handlers = lambda: None
    
    try:
        await server.serve()
    except asyncio.CancelledError:
        logger.info("Web 服务器已停止")

async def main():
    parser = argparse.ArgumentParser(description="TG-Link-Dispatcher Daemon with Web UI")
    parser.add_argument("--daemon", action="store_true", help="以守护进程模式运行")
    parser.add_argument("--web", action="store_true", help="启动 Web 控制面板 (默认端口 8000)")
    parser.add_argument("--interval", type=int, help="轮询间隔 (秒)")
    args = parser.parse_args()

    try:
        Config.validate_env()
        
        # 配置日志转发到 Web UI
        mon_handler = MonitorLogHandler()
        mon_handler.setLevel(logging.INFO) # 仅转发 INFO 及以上
        logging.getLogger().addHandler(mon_handler)
        
        interval = args.interval or Config.settings.loop_interval
        interval = args.interval or Config.settings.loop_interval
        if interval < 300 and args.daemon:
            interval = 300

        dispatcher = Dispatcher()
        
        if args.web:
            logger.info("🚀 正在启动 Web 控制面板: http://localhost:8000")
            asyncio.create_task(run_web_server())

        if not args.daemon:
            logger.info("执行单次同步任务...")
            try:
                await dispatcher.run_cycle()
            except Exception as e:
                logger.error(f"同步失败: {e}")
            return

        # Daemon 模式
        logger.info(f"进入守护模式，间隔 {interval}s")
        monitor.update_stats(status="Idle")
        
        client = None
        while True:
            try:
                # 确保客户端在线
                if not client or not client.is_connected():
                    client = await get_client()
                    # 将客户端实例注入到 Web 模块，供 API 使用
                    web_app_module.telegram_client = client
                
                # 执行同步循环
                await dispatcher.run_cycle(client=client)
                
                logger.info(f"休眠中，等待下一次同步...")
                await asyncio.sleep(interval)
                
            except Exception as e:
                error_msg = str(e)
                logger.error(f"守护进程循环异常: {error_msg}")
                monitor.update_stats(status="Error")
                
                # 针对时间同步错误的特殊处理
                if "Security error" in error_msg or "very new message" in error_msg:
                    logger.warning("⚠️ 检测到系统时间严重偏差，将在 60 秒后尝试重连...")
                    if client:
                        try:
                            await client.disconnect()
                        except:
                            pass
                        client = None
                    await asyncio.sleep(60)
                
                # 网络连接中断处理
                elif isinstance(e, (ConnectionError, OSError, TimeoutError)) or "Connection reset by peer" in error_msg:
                    logger.warning(f"⚠️ 网络连接中断，将在 10 秒后重试: {e}")
                    if client:
                        try:
                            await client.disconnect()
                        except:
                            pass
                        client = None
                    await asyncio.sleep(10)

                else:
                    # 其他错误，简单重试
                    await asyncio.sleep(30)

    except Exception as e:
        logger.error(f"系统启动失败: {e}")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
