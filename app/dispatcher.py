import asyncio
from app.config import Config
from app.client import get_client
from app.parser import parse_message
from app.exporter import ExporterFactory
from app.checkpoint import CheckpointManager
from app.logger import logger
from telethon.errors import FloodWaitError
from telethon import utils

class Dispatcher:
    """分发器核心类：负责消息拉取、任务匹配与导出路由"""
    
    def __init__(self):
        self.tasks = Config.TASKS
        self.checkpoint = CheckpointManager()
        self.exporters = {} # {path: ExporterInstance}
        self.fieldnames = ['message_id', 'time', 'sender', 'url', 'content', 'source_group', 'source_id', 'reply_to']

    async def _init_task_exporters(self):
        """初始化本项目所有任务需要的导出器"""
        for task in self.tasks:
            if task.output_path not in self.exporters:
                exp = ExporterFactory.create(
                    task.output_format, 
                    task.output_path, 
                    self.fieldnames
                )
                exp.open(mode='a')
                self.exporters[task.output_path] = exp

    def _match_source(self, entity, task_sources) -> bool:
        """匹配数据源 ID (支持 PeerID 和 RawID)"""
        if "all" in task_sources: return True
        p_id = str(utils.get_peer_id(entity))
        raw_id = str(entity.id)
        return any(str(s) in (p_id, raw_id) for s in task_sources)

    async def _get_active_entities(self, client):
        """根据配置发现所有需要扫描的 Telegram 实体"""
        explicit_ids, has_all = set(), False
        for task in self.tasks:
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
                try:
                    entities.append(await client.get_entity(sid))
                except Exception as e:
                    logger.error(f"无法获取实体 {sid}: {e}")
        return entities

    async def run_cycle(self, client=None):
        """执行一个完整的分发周期"""
        if not self.tasks: return

        opened_client = None
        if not client:
            opened_client = await get_client()
            client = opened_client

        await self._init_task_exporters()
        entities = await self._get_active_entities(client)
        
        for entity in entities:
            await self._process_source(client, entity)

        # 周期结束，清理资源
        for exp in self.exporters.values(): exp.close()
        self.exporters.clear() # 确保下次 rebuild 以应用配置变更

        if opened_client:
            await opened_client.disconnect()
        logger.info("分发周期执行完毕。")

    async def _process_source(self, client, entity):
        """处理单个数据源的消息"""
        try:
            source_id = str(utils.get_peer_id(entity))
            group_title = getattr(entity, 'title', source_id)
            
            # 1. 预筛选与此源相关的任务
            active_tasks = [t for t in self.tasks if self._match_source(entity, t.sources)]
            if not active_tasks: return

            # 2. 获取进度断点
            last_id = self.checkpoint.get(source_id, 0)
            logger.info(f"🔄 扫描: {group_title} (ID: {source_id}) 自 ID: {last_id}")

            count, new_max_id = 0, last_id
            
            # 3. 拉取消息并分发
            async for message in client.iter_messages(entity, min_id=last_id, reverse=True):
                if message.id <= last_id: continue

                msg_data = await parse_message(message)
                msg_data['source_group'], msg_data['source_id'] = group_title, source_id
                
                # 路由到各个匹配的任务
                for task in active_tasks:
                    if self._is_task_match(task, msg_data):
                        exporter = self.exporters.get(task.output_path)
                        if exporter and not exporter.is_duplicate(msg_data.get('url')):
                            exporter.write(msg_data)
                            count += 1
                
                if message.id > new_max_id: new_max_id = message.id
            
            # 4. 更新断点
            if new_max_id > last_id:
                self.checkpoint.set(source_id, new_max_id)

            if count > 0: logger.info(f"✅ {group_title}: 成功路由 {count} 条消息")

        except FloodWaitError as e:
            logger.warning(f"触发限流，等待 {e.seconds} 秒")
            await asyncio.sleep(e.seconds)
        except Exception as e:
            logger.error(f"处理源 {source_id} 出错: {e}")

    def _is_task_match(self, task, msg_data) -> bool:
        """检查消息是否匹配任务关键词"""
        if not task.keywords: return True
        content = msg_data.get('content', '').lower()
        return any(kw.lower() in content for kw in task.keywords)
