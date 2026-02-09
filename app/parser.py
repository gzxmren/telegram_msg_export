from datetime import datetime
import pytz
from telethon import types
from app.cleaner import cleaner

from datetime import datetime
import pytz
from telethon import types
from app.cleaner import cleaner
from app.models import MessageData

async def parse_message(message, group_title: str, source_id: str) -> MessageData:
    """解析 Telethon 消息对象并转换为标准模型"""
    
    # 1. 基础信息
    time_str = ""
    if message.date:
        local_tz = pytz.timezone('Asia/Shanghai')
        time_str = message.date.astimezone(local_tz).strftime('%Y-%m-%d %H:%M:%S')

    # 2. 发送者
    sender_name = "Unknown"
    sender = await message.get_sender()
    if sender:
        sender_name = getattr(sender, 'username', '') or getattr(sender, 'title', 'Unknown')

    # 3. 内容处理
    raw_text = message.message or ""
    content = raw_text
    if message.media:
        media_type = f"[{type(message.media).__name__.replace('MessageMedia', '')}]"
        if isinstance(message.media, types.MessageMediaPhoto): media_type = "[图片]"
        elif isinstance(message.media, types.MessageMediaDocument): media_type = "[文件/附件]"
        elif isinstance(message.media, types.MessageMediaWebPage): media_type = ""
        
        content = f"{media_type} {raw_text}".strip() if media_type else raw_text

    # 4. URL 提取与清洗
    extracted_url = ""
    urls = cleaner.extract_urls(content)
    if urls:
        extracted_url = cleaner.normalize(urls[0])

    # 5. 标题提取 (Native)
    title = ""
    if message.media and isinstance(message.media, types.MessageMediaWebPage):
        wp = message.media.webpage
        if isinstance(wp, types.WebPage) and wp.title:
            title = wp.title

    return MessageData(
        message_id=message.id,
        time=time_str,
        sender=sender_name,
        title=title,
        url=extracted_url,
        content=content,
        source_group=group_title,
        source_id=source_id,
        reply_to=message.reply_to.reply_to_msg_id if message.reply_to else None
    )
