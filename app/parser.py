from datetime import datetime
import pytz
from telethon import types
from app.cleaner import cleaner

async def parse_message(message):
    """解析 Telethon 消息对象，增加 URL 提取功能"""
    data = {
        'message_id': message.id,
        'time': '',
        'sender': '',
        'content': '',
        'reply_to': '',
        'url': '' # 新增字段
    }

    # 1. 转换时间为本地时区
    if message.date:
        local_tz = pytz.timezone('Asia/Shanghai')
        local_time = message.date.astimezone(local_tz)
        data['time'] = local_time.strftime('%Y-%m-%d %H:%M:%S')

    # 2. 获取发送者信息
    sender = await message.get_sender()
    if sender:
        data['sender'] = getattr(sender, 'username', '') or getattr(sender, 'title', 'Unknown')

    # 3. 处理回复
    if message.reply_to:
        data['reply_to'] = message.reply_to.reply_to_msg_id

    # 4. 提取内容（优先处理媒体，后处理文本）
    text = message.message or ""
    
    if message.media:
        media_type = "[媒体内容]"
        if isinstance(message.media, types.MessageMediaPhoto):
            media_type = "[图片]"
        elif isinstance(message.media, types.MessageMediaDocument):
            media_type = f"[文件/附件]"
        elif isinstance(message.media, types.MessageMediaWebPage):
            # 网页预览不视为独立媒体，仅作为文字处理
            pass
        else:
            media_type = f"[{type(message.media).__name__}]"
        
        if text:
            data['content'] = f"{media_type} {text}"
        else:
            data['content'] = media_type
    else:
        data['content'] = text

    # 5. 核心：提取并清洗 URL
    urls = cleaner.extract_urls(data['content'])
    if urls:
        # 取第一个识别到的链接进行标准化
        data['url'] = cleaner.normalize(urls[0])

    return data
