import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

class Config:
    API_ID = os.getenv("API_ID")
    API_HASH = os.getenv("API_HASH")
    PHONE = os.getenv("PHONE")
    CHAT_ID = os.getenv("CHAT_ID")
    EXPORT_PATH = os.getenv("EXPORT_PATH", "output/messages.csv")
    BATCH_LIMIT = int(os.getenv("BATCH_LIMIT", 100))
    # 是否强制全量拉取 (覆盖模式)
    FORCE_FULL_FETCH = os.getenv("FORCE_FULL_FETCH", "false").lower() == "true"

    @classmethod
    def validate(cls):
        """校验必要参数是否存在"""
        missing = []
        if not cls.API_ID: missing.append("API_ID")
        if not cls.API_HASH: missing.append("API_HASH")
        if not cls.PHONE: missing.append("PHONE")
        if not cls.CHAT_ID: missing.append("CHAT_ID")
        
        if missing:
            raise ValueError(f"缺少必要配置项: {', '.join(missing)}。请检查 .env 文件。")
        
        # 类型转换校验
        try:
            cls.API_ID = int(cls.API_ID)
        except ValueError:
            raise ValueError("API_ID 必须是数字，请检查 .env 文件。")
