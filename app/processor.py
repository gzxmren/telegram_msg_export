from app.metadata import metadata_provider
from app.cleaner import cleaner
from app.models import MessageData
from app.logger import logger
from app.monitor import monitor

class MessageProcessor:
    """消息处理流水线，负责增强、过滤和检查"""
    
    @staticmethod
    async def process(msg: MessageData) -> MessageData:
        # 1. 标题增强 & 短链自动展开 (Active Discovery)
        if msg.url:
            # 判断是否需要抓取元数据：标题缺失，或者是需要展开的短链接
            is_short_url = any(domain in msg.url for domain in ["v.douyin.com", "t.co", "dwz.cn", "b23.tv"])
            
            if not msg.title or is_short_url:
                # 尝试获取标题和最终 URL (处理 v.douyin.com 等重定向)
                title, final_url = await metadata_provider.fetch_metadata(msg.url)
                
                # 补全标题 (仅在原标题为空时)
                if title and not msg.title:
                    msg.title = title
                
                # 更新 URL (如果发生了重定向，如短链变长链)
                if final_url and final_url != msg.url:
                    # 重要：新的长链接通常包含大量追踪参数，必须重新清洗
                    msg.url = cleaner.normalize(final_url)
                
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
