from app.metadata import metadata_provider
from app.models import MessageData
from app.logger import logger
from app.monitor import monitor

class MessageProcessor:
    """消息处理流水线，负责增强、过滤和检查"""
    
    @staticmethod
    async def process(msg: MessageData) -> MessageData:
        # 1. 标题增强 (Active Discovery)
        if not msg.title and msg.url:
            active_title = await metadata_provider.fetch_title(msg.url)
            if active_title:
                msg.title = active_title
                
        # 这里可以扩展更多处理器：
        # - AI 摘要
        # - 标签提取
        # - 自动分类
        
        return msg

    @staticmethod
    def is_match(task, msg: MessageData) -> bool:
        """检查消息是否匹配任务关键词"""
        if not task.keywords: return True
        content = msg.content.lower()
        return any(kw.lower() in content for kw in task.keywords)
