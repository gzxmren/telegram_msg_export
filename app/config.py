import os
import yaml
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

class TaskConfig:
    def __init__(self, name, enable, sources, keywords, output):
        self.name = name
        self.enable = enable
        self.sources = sources
        self.keywords = keywords
        self.output_path = output.get('path')
        self.output_format = output.get('format', 'csv')

class Config:
    API_ID = os.getenv("API_ID")
    API_HASH = os.getenv("API_HASH")
    PHONE = os.getenv("PHONE")
    
    # 之前 v0.3 的遗留配置，保留兼容性
    CHAT_ID = os.getenv("CHAT_ID")
    EXPORT_PATH = os.getenv("EXPORT_PATH", "output/messages.csv")
    FORCE_FULL_FETCH = os.getenv("FORCE_FULL_FETCH", "false").lower() == "true"
    
    # 新版 Dispatcher 配置
    TASKS = []
    SETTINGS = {}

    @classmethod
    def load_yaml_config(cls, path="config.yaml"):
        if not os.path.exists(path):
            return
        
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            cls.SETTINGS = data.get('settings', {})
            tasks_data = data.get('tasks', [])
            cls.TASKS = [
                TaskConfig(**t) for t in tasks_data if t.get('enable', True)
            ]

    @classmethod
    def validate(cls):
        """校验必要参数是否存在"""
        missing = []
        if not cls.API_ID: missing.append("API_ID")
        if not cls.API_HASH: missing.append("API_HASH")
        if not cls.PHONE: missing.append("PHONE")
        
        if missing:
            raise ValueError(f"缺少必要配置项: {', '.join(missing)}。请检查 .env 文件。")
        
        # 类型转换校验
        try:
            cls.API_ID = int(cls.API_ID)
        except ValueError:
            raise ValueError("API_ID 必须是数字，请检查 .env 文件。")

# 自动加载 YAML
Config.load_yaml_config()
