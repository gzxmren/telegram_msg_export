from datetime import datetime

def clean_content(msg):
    """提取消息内容，处理媒体类型"""
    if msg.text:
        return msg.text.strip()
    
    # 处理媒体类型
    if msg.media:
        if hasattr(msg.media, 'photo'):
            return '[图片]'
        elif hasattr(msg.media, 'document'):
            # 尝试获取文件名
            file_name = "未知文件"
            if hasattr(msg.media.document, 'attributes'):
                for attr in msg.media.document.attributes:
                    if hasattr(attr, 'file_name'):
                        file_name = attr.file_name
                        break
            return f'[文件] {file_name}'
        elif hasattr(msg.media, 'video'):
            return '[视频]'
        elif hasattr(msg.media, 'voice'):
            return '[语音消息]'
        elif hasattr(msg.media, 'poll'):
            return f'[投票] {msg.media.poll.poll.question}'
    
    if msg.sticker:
        return '[贴纸]'
        
    return '[非文本消息]'

async def parse_message(msg):
    """将 Telethon 消息对象转换为标准字典格式"""
    # 1. 获取发送者姓名
    sender = await msg.get_sender()
    if not sender:
        sender_name = "System/Unknown"
    else:
        # 优先取 username，没有则取 first_name + last_name
        sender_name = sender.username if hasattr(sender, 'username') and sender.username else \
                      f"{getattr(sender, 'first_name', '')} {getattr(sender, 'last_name', '')}".strip()
        if not sender_name:
            sender_name = str(sender.id)

    # 2. 格式化时间
    # msg.date 是带有时区的 UTC 时间
    local_time = msg.date.astimezone().strftime('%Y-%m-%d %H:%M:%S')

    return {
        'message_id': msg.id,
        'time': local_time,
        'sender': sender_name,
        'content': clean_content(msg),
        'reply_to': msg.reply_to.reply_to_msg_id if msg.reply_to else ""
    }
