"""AI分析引擎 - 整合日志解析+文件校验，生成DailyReport"""
from datetime import datetime
from typing import List
from models.schemas import RPATaskLog, DailyReport, TaskStatus
from agent.log_parser import LogParser
from agent.file_validator import FileValidator


class Analyzer:
    """
    AI分析引擎
    职责：协调日志解析和文件校验，统计运行数据，输出结构化DailyReport
    """

    def __init__(self):
        self.log_parser = LogParser()
        self.file_validator = FileValidator()

    def analyze(self, rpa_log_texts: List[str]) -> DailyReport:
        """
        完整分析流程：
        1. 解析所有日志为结构化数据
        2. 校验所有文件路径
        3. 统计运行数据
        4. 输出DailyReport
        """
        today = datetime.now().strftime("%Y-%m-%d")

        # Step 1: 解析日志
        task_logs = self.log_parser.parse_all_logs(rpa_log_texts)
        print(f"[Analyzer] 解析完成，共 {len(task_logs)} 个RPA流程")

        # Step 2: 文件校验
        task_logs = self.file_validator.validate_all(task_logs)

        # Step 3: 统计
        total = len(task_logs)
        success = sum(1 for t in task_logs if t.overall_status == TaskStatus.SUCCESS)
        fail = total - success

        # Step 4: 组装报告
        error_tasks = [t for t in task_logs if t.overall_status == TaskStatus.FAILED]
        missing_files = self.file_validator.get_missing_files_summary(task_logs)

        report = DailyReport(
            date=today,
            total_tasks=total,
            success_count=success,
            fail_count=fail,
            task_logs=task_logs,
            has_error=(fail > 0),
            error_tasks=error_tasks,
            missing_files=missing_files
        )

        print(f"[Analyzer] 分析完成: 总计{total}, 成功{success}, 失败{fail}")
        return report
