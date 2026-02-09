import os
import json
from app.logger import logger

class CheckpointManager:
    """负责消息进度（断点）的持久化管理"""
    def __init__(self, file_path="data/checkpoint.json"):
        self.file_path = file_path
        self.checkpoints = self._load()

    def _load(self):
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"加载断点文件失败: {e}")
        return {}

    def get(self, key, default=0):
        return self.checkpoints.get(str(key), default)

    def set(self, key, value):
        self.checkpoints[str(key)] = value
        self._save()

    def _save(self):
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self.checkpoints, f, indent=4)
        except Exception as e:
            logger.error(f"保存断点文件失败: {e}")
