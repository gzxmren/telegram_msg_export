import asyncio
import sys
import os
from tqdm import tqdm
from telethon.errors import FloodWaitError

from app.config import Config
from app.client import get_client
from app.parser import parse_message
from app.exporter import CSVExporter
from app.logger import logger

async def run_v03():
    # 1. 验证配置
    try:
        Config.validate()
    except ValueError as e:
        logger.error(f"配置错误: {e}")
        return

    # 2. 获取客户端
    client = await get_client()

    # 3. 搜索目标群组
    logger.info(f"正在搜索目标群组: {Config.CHAT_ID}")
    target_entity = None
    try:
        target_entity = await client.get_entity(Config.CHAT_ID)
    except Exception:
        async for dialog in client.iter_dialogs():
            if str(dialog.id) == str(Config.CHAT_ID):
                target_entity = dialog.entity
                break
                
    if not target_entity:
        logger.error("无法找到目标群组。")
        return

    group_title = getattr(target_entity, 'title', 'Unknown')
    logger.info(f"成功定位群组: {group_title}")

    # 4. 初始化导出器与模式判断
    exporter = CSVExporter(Config.EXPORT_PATH)
    
    # 决策逻辑: 强制全量 OR 文件不存在 -> 全量(w)
    # 否则 -> 增量(a)
    incremental_mode = False
    min_id = 0
    file_mode = 'w'

    if Config.FORCE_FULL_FETCH:
        logger.info("配置强制全量拉取，将覆盖现有文件。")
    elif not os.path.exists(Config.EXPORT_PATH):
        logger.info("未找到历史文件，将进行全量拉取。")
    else:
        incremental_mode = True
        file_mode = 'a'
        # 获取上次的断点
        min_id = exporter.get_last_id()
        logger.info(f"检测到历史文件，进入增量模式。上次最后一条消息 ID: {min_id}")

    # 获取消息总数用于进度条 (仅供参考)
    total_messages = 0
    try:
        # 这里的 total 是群组所有消息，不是本次要拉取的量
        # 增量模式下，这个数字主要用于显示总进度
        full_info = await client.get_messages(target_entity, limit=0)
        total_messages = full_info.total
    except Exception:
        pass

    exporter.open(mode=file_mode)
    logger.info(f"开始导出至: {Config.EXPORT_PATH} (模式: {file_mode})")

    # 5. 开始抓取与导出
    count = 0
    # 注意: 增量模式下很难预估确切的剩余消息数，所以 total 可能不准
    pbar = tqdm(total=total_messages if not incremental_mode else 0, 
                desc="正在抓取", unit="msg")
    
    try:
        while True:
            try:
                # 确定拉取限制 (CLI参数优先，否则无限制)
                fetch_limit = getattr(Config, 'CLI_LIMIT', None)
                
                # 关键修改: reverse=True (从旧到新)
                # 这样不管是全量还是增量，写入顺序都是时间正序，方便追加
                async for message in client.iter_messages(target_entity, limit=fetch_limit, min_id=min_id, reverse=True):
                    # 解析消息
                    data = await parse_message(message)
                    # 写入 CSV
                    exporter.write_row(data)
                    
                    count += 1
                    pbar.update(1)
                
                break

            except FloodWaitError as e:
                logger.warning(f"触发 Telegram 限流，需要等待 {e.seconds} 秒...")
                await asyncio.sleep(e.seconds)
                continue

        action_str = "更新" if incremental_mode else "导出"
        logger.info(f"{action_str}完成! 本次共{action_str} {count} 条消息。")

    except KeyboardInterrupt:
        logger.info(f"用户手动中断，已安全保存 {count} 条数据。")
    except Exception as e:
        logger.error(f"运行中发生未预期错误: {e}")
    finally:
        pbar.close()
        exporter.close()
        await client.disconnect()

if __name__ == '__main__':
    import argparse

    # 初始化命令行参数解析器
    parser = argparse.ArgumentParser(
        description="Telegram Group Message Exporter (TG-Exporter)",
        epilog="优先读取命令行参数，未指定则读取 .env 配置。",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument("-c", "--chat-id", help="目标群组 ID 或 Username (覆盖 .env)")
    parser.add_argument("-o", "--output", help="导出 CSV 路径 (覆盖 .env)")
    parser.add_argument("-f", "--force", action="store_true", help="强制全量拉取 (忽略历史文件)")
    parser.add_argument("-l", "--limit", type=int, help="限制拉取的消息数量 (用于测试)")

    args = parser.parse_args()

    # 将命令行参数应用到 Config (覆盖环境变量)
    if args.chat_id:
        Config.CHAT_ID = args.chat_id
    if args.output:
        Config.EXPORT_PATH = args.output
    if args.force:
        Config.FORCE_FULL_FETCH = True
    
    # 为了支持 limit 参数，我们需要稍微修改 run_v03 或者将 limit 存入 Config
    # 这里我们采用一种简单的 Monkey Patch 方式，或者修改 run_v03 签名
    # 鉴于 run_v03 直接引用 Config，我们可以把 limit 作为一个临时属性加进去
    Config.CLI_LIMIT = args.limit

    try:
        asyncio.run(run_v03())
    except KeyboardInterrupt:
        pass



