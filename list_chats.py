import asyncio
from app.client import get_client

async def main():
    print("[*] 正在获取对话列表，请稍候...")
    client = await get_client()
    
    print("\n" + "="*50)
    print(f"{ 'ID':<20} | {'类型':<10} | {'名称'}")
    print("="*50)
    
    # 获取对话列表
    async for dialog in client.iter_dialogs():
        # 过滤掉私聊(User)，只显示群组(Chat)和频道(Channel)
        # 如果你也想看私聊，可以把 if 判断去掉
        if dialog.is_group or dialog.is_channel:
            type_str = "群组" if dialog.is_group else "频道"
            print(f"{dialog.id:<20} | {type_str:<10} | {dialog.title}")
            
    print("="*50)
    print("\n[?] 请找到你的目标群组，将对应的 ID (通常以 -100 开头) 复制到 .env 文件的 CHAT_ID 字段中。")

if __name__ == '__main__':
    asyncio.run(main())

