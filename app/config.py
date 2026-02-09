import os
import yaml
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, field_validator
from dotenv import load_dotenv

load_dotenv()

class ExporterSettings(BaseModel):
    path: str
    format: str = "csv"

class TaskModel(BaseModel):
    name: str
    enable: bool = True
    sources: List[Any] = []
    keywords: List[str] = []
    output: ExporterSettings

    @field_validator('sources', mode='before')
    @classmethod
    def normalize_sources(cls, v):
        # 兼容配置中写成单值的情况，自动转为列表
        return [v] if not isinstance(v, list) else v

class SystemSettings(BaseModel):
    loop_interval: int = 300
    web_port: int = 8000
    web_host: str = "0.0.0.0"

class AppConfig:
    """集中式配置管理"""
    
    # 核心环境变量
    API_ID: int = int(os.getenv("API_ID", 0))
    API_HASH: str = os.getenv("API_HASH", "")
    PHONE: str = os.getenv("PHONE", "")
    WEB_PASSWORD: str = os.getenv("WEB_PASSWORD", "admin")

    # 动态加载内容
    tasks: List[TaskModel] = []
    settings: SystemSettings = SystemSettings()
    
    _last_mtime: float = 0
    _config_path: str = "config.yaml"

    @classmethod
    def load(cls, path: str = "config.yaml"):
        cls._config_path = path
        if not os.path.exists(path):
            return False
            
        mtime = os.path.getmtime(path)
        if mtime <= cls._last_mtime:
            return False

        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
                
            # 使用 Pydantic 校验并解析内容
            cls.settings = SystemSettings(**data.get('settings', {}))
            
            raw_tasks = data.get('tasks', [])
            cls.tasks = [TaskModel(**t) for t in raw_tasks if t.get('enable', True)]
            
            cls._last_mtime = mtime
            return True
        except Exception as e:
            raise ValueError(f"配置文件格式错误: {e}")

    @classmethod
    def validate_env(cls):
        if not cls.API_ID or not cls.API_HASH or not cls.PHONE:
            raise ValueError("请在 .env 文件中完整配置 API_ID, API_HASH 和 PHONE")

# 初始加载
AppConfig.load()
