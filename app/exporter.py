import csv
import os

class CSVExporter:
    def __init__(self, file_path):
        self.file_path = file_path
        self.fieldnames = ['message_id', 'time', 'sender', 'content', 'reply_to']
        self.file = None
        self.writer = None

    def get_last_id(self):
        """获取文件中最大的 message_id，用于增量更新"""
        if not os.path.exists(self.file_path):
            return 0
        
        max_id = 0
        try:
            with open(self.file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        mid = int(row['message_id'])
                        if mid > max_id:
                            max_id = mid
                    except (ValueError, KeyError):
                        continue
        except Exception:
            return 0
        return max_id

    def open(self, mode='w'):
        """初始化文件流
        mode='w': 覆盖模式 (全量)
        mode='a': 追加模式 (增量)
        """
        # 确保输出目录存在
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        
        file_exists = os.path.exists(self.file_path)
        write_header = not file_exists or mode == 'w'

        # utf-8-sig 用于解决 Windows Excel 乱码
        self.file = open(self.file_path, mode, encoding='utf-8-sig', newline='')
        self.writer = csv.DictWriter(self.file, fieldnames=self.fieldnames)
        
        if write_header:
            self.writer.writeheader()

    def write_row(self, data):
        """写入单行数据"""
        if self.writer:
            self.writer.writerow(data)

    def close(self):
        """关闭文件"""
        if self.file:
            self.file.flush()
            self.file.close()
