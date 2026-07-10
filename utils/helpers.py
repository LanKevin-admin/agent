"""工具函数"""
import os
from datetime import datetime


def get_today_str(fmt: str = "%Y-%m-%d") -> str:
    """获取今日日期字符串"""
    return datetime.now().strftime(fmt)


def ensure_dir(path: str):
    """确保目录存在"""
    os.makedirs(path, exist_ok=True)
