import logging
import sys
from logging.handlers import RotatingFileHandler

def setup_logger():
    """配置全局日志"""
    logger = logging.getLogger("tg_exporter")
    logger.setLevel(logging.INFO)

    # 格式：时间 - 级别 - 内容
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    # 输出到控制台
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 输出到文件 (增加自动切片和大小限制)
    # 每个文件最大 10MB, 保留最近 5 个备份
    file_handler = RotatingFileHandler(
        "dispatcher.log", 
        maxBytes=10 * 1024 * 1024, 
        backupCount=5, 
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger

logger = setup_logger()
