import asyncio
from datetime import datetime
from typing import List

from telethon import TelegramClient, utils
from telethon.errors import FloodWaitError

from app.config import AppConfig as Config
from app.client import get_client
from app.parser import parse_message
from app.exporter import ExporterFactory
from app.checkpoint import CheckpointManager
from app.monitor import monitor
from app.logger import logger
from app.processor import MessageProcessor
from app.models import MessageData

class Dispatcher:
    """分发器核心：协调各个组件完成工作流"""

    def __init__(self):
        self.checkpoint = CheckpointManager()
        self.exporters = {} # {path: ExporterInstance}
        self.fieldnames = MessageData.get_csv_headers()

    async def run_cycle(self, client: TelegramClient = None):
        """主循环：加载配置 -> 发现源 -> 迭代处理"""
        if Config.load():
            logger.info("🔥 配置已重载")
            self.exporters.clear()

        if not Config.tasks: return

        active_client = client or await get_client()
        monitor.update_stats(status="Processing", tasks_active=len(Config.tasks))
        
        try:
            # 1. 发现需要扫描的所有实体
            entities = await self._discover_sources(active_client)
            monitor.update_stats(sources_active=len(entities))
            
            # 2. 预初始化导出器
            self._ensure_exporters()

            # 3. 遍历实体进行消息抓取
            msg = f"🔄 开始分发周期，扫描 {len(entities)} 个源"
            logger.info(msg) # MonitorLogHandler will pick this up
            for entity in entities:
                await self._sync_source(active_client, entity)

        finally:
            # 释放资源
            for exp in self.exporters.values(): exp.close()
            self.exporters.clear()
            if not client: await active_client.disconnect()
            
            monitor.update_stats(
                status="Idle", 
                cycles_completed=monitor.stats["cycles_completed"] + 1,
                last_sync_time=datetime.now().strftime("%H:%M:%S")
            )

    async def _discover_sources(self, client):
        """发现所有相关数据源"""
        explicit_ids, has_all = set(), False
        for task in Config.tasks:
            if "all" in task.sources: has_all = True
            for s in task.sources:
                if isinstance(s, (int, str)) and str(s).lstrip('-').isdigit():
                    explicit_ids.add(int(s))
        
        entities = []
        if has_all:
            async for dialog in client.iter_dialogs():
                if dialog.is_group or dialog.is_channel:
                    entities.append(dialog.entity)
        else:
            for sid in explicit_ids:
                try: entities.append(await client.get_entity(sid))
                except Exception as e: logger.error(f"无法获取源 {sid}: {e}")
        return entities

    def _ensure_exporters(self):
        """确保所有任务的导出器已准备就绪"""
        for task in Config.tasks:
            path = task.output.path
            if path not in self.exporters:
                exp = ExporterFactory.create(task.output.format, path, self.fieldnames)
                exp.open(mode='a')
                self.exporters[path] = exp

    async def _sync_source(self, client, entity):
        """同步单个数据源"""
        source_id = str(utils.get_peer_id(entity))
        group_title = getattr(entity, 'title', source_id)
        
        # 匹配对应此源的所有任务
        matched_tasks = [t for t in Config.tasks if self._match_source(entity, t.sources)]
        if not matched_tasks: return

        last_id = self.checkpoint.get(source_id, 0)
        logger.info(f"🔄 扫描: [{group_title}] 从 ID: {last_id}")

        new_max_id = last_id
        current_source_processed = 0
        total_fetched = 0

        try:
            async for message in client.iter_messages(entity, min_id=last_id, reverse=True):
                if message.id <= last_id: continue
                total_fetched += 1
                
                # 1. 核心解析与增强
                msg_data = await parse_message(message, group_title, source_id)
                msg_data = await MessageProcessor.process(msg_data)
                
                # 2. 路由到任务
                was_routed = False
                for task in matched_tasks:
                    if MessageProcessor.is_match(task, msg_data):
                        if await self._export_to_task(task, msg_data):
                            was_routed = True
                
                if was_routed: 
                    current_source_processed += 1
                    monitor.increment("urls_identified")

                if message.id > new_max_id: new_max_id = message.id

            # 3. 更新进度与计数
            if new_max_id > last_id:
                self.checkpoint.set(source_id, new_max_id)
            
            monitor.increment("messages_processed", total_fetched)
            
            if current_source_processed > 0:
                msg = f"✅ [{group_title}]: 新增 {current_source_processed} 条记录"
                logger.info(msg)
            elif total_fetched > 0:
                logger.info(f"ℹ️ [{group_title}]: 扫描 {total_fetched} 条消息，无匹配或均为重复")

        except FloodWaitError as e:
            logger.warning(f"触发限流，休眠 {e.seconds} 秒")
            await asyncio.sleep(e.seconds)
        except Exception as e:
            logger.error(f"同步 [{group_title}] 失败: {e}")

    async def _export_to_task(self, task, msg: MessageData) -> bool:
        """执行导出与去重检查"""
        exporter = self.exporters.get(task.output.path)
        if not exporter: return False
        
        if msg.url and exporter.is_duplicate(msg.url):
            msg_log = f"⏭️ 跳过重复 URL (任务: {task.name}, 源: {msg.source_group})"
            monitor.add_log(msg_log)
            return False

        exporter.write(msg.model_dump())
        return True

    def _match_source(self, entity, task_sources) -> bool:
        if "all" in task_sources: return True
        p_id, raw_id = str(utils.get_peer_id(entity)), str(entity.id)
        return any(str(s) in (p_id, raw_id) for s in task_sources)
