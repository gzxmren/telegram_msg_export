import csv
import os
from abc import ABC, abstractmethod

class BaseExporter(ABC):
    """导出器抽象基类"""
    def __init__(self, file_path):
        # 安全校验：防止路径穿越
        self.file_path = self._sanitize_path(file_path)
        self.file = None
        self.seen_data = set()

    def _sanitize_path(self, path: str) -> str:
        """确保路径安全，限制在项目 data 目录下"""
        # 获取绝对路径
        abs_path = os.path.abspath(path)
        # 获取当前项目的 data 目录绝对路径
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(project_root, "data")
        
        # 如果路径不在 data 目录下，强制修正
        if not abs_path.startswith(data_dir):
            filename = os.path.basename(path)
            # 即使传入了恶意路径，也强制将其保存到 data/safe_export/ 目录下
            safe_path = os.path.join(data_dir, "safe_export", filename)
            # print(f"🛡️ 安全审计：拦截到越权路径 {path}，已重定向至 {safe_path}")
            return safe_path
            
        return abs_path

    @abstractmethod
    def open(self, mode='a'):
        pass

    @abstractmethod
    def write(self, data):
        pass

    @abstractmethod
    def is_duplicate(self, key):
        pass

    def close(self):
        if self.file:
            self.file.flush()
            self.file.close()
            self.file = None

class CSVExporter(BaseExporter):
    def __init__(self, file_path, fieldnames):
        super().__init__(file_path)
        self.fieldnames = fieldnames
        self.writer = None

    def open(self, mode='a'):
        directory = os.path.dirname(self.file_path)
        if directory: os.makedirs(directory, exist_ok=True)
        
        file_exists = os.path.exists(self.file_path)
        
        # 核心改进：确保列对齐稳定性
        if mode == 'a' and file_exists:
            self._load_cache()
            # 读取现有文件的表头，如果存在则强制使用它，防止列错位
            try:
                with open(self.file_path, 'r', encoding='utf-8-sig') as f:
                    reader = csv.reader(f)
                    existing_header = next(reader, [])
                    if existing_header:
                        self.fieldnames = existing_header
            except Exception:
                pass

        self.file = open(self.file_path, mode, encoding='utf-8-sig', newline='')
        self.writer = csv.DictWriter(self.file, fieldnames=self.fieldnames, extrasaction='ignore')
        if not file_exists or mode == 'w':
            self.writer.writeheader()

    def _load_cache(self):
        """将已有 URL 放入内存集合"""
        try:
            with open(self.file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    u = row.get('url')
                    if u: self.seen_data.add(u)
        except Exception: pass

    def is_duplicate(self, url):
        return url in self.seen_data

    def write(self, data):
        if self.writer:
            u = data.get('url')
            if u: self.seen_data.add(u)
            # 过滤掉不在表头中的字段
            filtered = {k: v for k, v in data.items() if k in self.fieldnames}
            self.writer.writerow(filtered)
            self.file.flush()

class TXTExporter(BaseExporter):
    def open(self, mode='a'):
        directory = os.path.dirname(self.file_path)
        if directory: os.makedirs(directory, exist_ok=True)
        if mode == 'a' and os.path.exists(self.file_path):
            self._load_cache()
        self.file = open(self.file_path, mode, encoding='utf-8', newline='')

    def _load_cache(self):
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    self.seen_data.add(line.strip())
        except Exception: pass

    def is_duplicate(self, content):
        return content.strip() in self.seen_data

    def write(self, data):
        if self.file:
            val = data.get('url') or data.get('content', '')
            val = val.strip()
            if val and val not in self.seen_data:
                self.file.write(val + '\n')
                self.file.flush()
                self.seen_data.add(val)

class ExporterFactory:
    """导出器工厂"""
    @staticmethod
    def create(output_format, file_path, fieldnames):
        if output_format.lower() == 'txt':
            return TXTExporter(file_path)
        return CSVExporter(file_path, fieldnames)
