import time
from datetime import datetime
from typing import Dict, List, Any

class Monitor:
    """系统运行状态监控器"""
    
    def __init__(self):
        self.stats = {
            "status": "Starting",
            "uptime": time.time(),
            "messages_processed": 0,
            "urls_identified": 0,
            "cycles_completed": 0,
            "last_sync_time": "Never",
            "tasks_active": 0,
            "sources_active": 0
        }
        self.logs: List[Dict[str, str]] = []

    def update_stats(self, **kwargs):
        """批量更新指标"""
        for key, value in kwargs.items():
            if key in self.stats:
                self.stats[key] = value

    def increment(self, key: str, count: int = 1):
        """递增计数器"""
        if key in self.stats:
            self.stats[key] += count

    def add_log(self, message: str):
        """添加系统实时流水"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.logs.insert(0, {"time": timestamp, "msg": message})
        # 仅保留最近 100 条日志
        if len(self.logs) > 100:
            self.logs = self.logs[:100]

    def to_dict(self) -> Dict[str, Any]:
        """导出为 Web 接口使用的格式"""
        res = self.stats.copy()
        res["uptime_str"] = self._format_uptime()
        res["logs"] = self.logs
        return res

    def _format_uptime(self) -> str:
        diff = int(time.time() - self.stats["uptime"])
        hours, rem = divmod(diff, 3600)
        minutes, seconds = divmod(rem, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

# 单例
monitor = Monitor()
