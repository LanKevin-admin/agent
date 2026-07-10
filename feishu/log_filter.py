"""RPA日志消息过滤器 - 区分RPA日志和闲聊"""
import re
from typing import List
from config.settings import config


class LogFilter:
    """日志过滤器 - 精准识别RPA运行日志"""

    def __init__(self):
        self.markers = config.RPA_LOG_MARKERS

    def filter_rpa_logs(self, messages: List[str]) -> List[str]:
        """
        从群消息中筛选RPA运行日志
        规则：消息中包含任一RPA日志标识关键词即认为是RPA日志
        """
        rpa_logs = []
        for msg in messages:
            if self._is_rpa_log(msg):
                rpa_logs.append(msg)

        print(f"[LogFilter] 筛选出 {len(rpa_logs)} 条RPA日志（共 {len(messages)} 条消息）")
        return rpa_logs

    def _is_rpa_log(self, message: str) -> bool:
        """判断单条消息是否为RPA日志"""
        # 规则1：包含RPA日志关键标识
        marker_count = sum(1 for marker in self.markers if marker in message)
        if marker_count >= 2:
            return True

        # 规则2：包含文件路径格式（C:\xxx 或 D:\xxx）
        if re.search(r'[A-Z]:\\[^\s]+', message):
            return True

        # 规则3：包含账号+状态的典型组合
        if re.search(r'.{2,}账号', message) and any(s in message for s in ['成功', '失败']):
            return True

        return False

    def group_by_task(self, rpa_logs: List[str]) -> List[str]:
        """
        将日志按RPA任务分组
        每条完整的RPA日志通常是一个账号从登录到退出的完整流程
        飞书群里一般一条消息就是一个完整流程的日志
        """
        # 如果每条消息已经是完整的流程日志，直接返回
        # 如果是分条发送的，需要按账号合并
        grouped = []
        current_log = []

        for log in rpa_logs:
            # 如果包含"账号"关键词，说明是一个新流程的开始
            if "账号" in log and current_log:
                grouped.append("\n".join(current_log))
                current_log = []
            current_log.append(log)

        if current_log:
            grouped.append("\n".join(current_log))

        return grouped
