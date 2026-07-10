"""文件路径校验模块 - 核验RPA生成的业务文件是否真实存在"""
import os
from typing import List
from models.schemas import RPATaskLog, FileValidation, TaskStatus


class FileValidator:
    """
    文件校验器
    根据日志中的文件保存路径，核验对应文件是否真实存在于本地
    """

    def validate_task(self, task_log: RPATaskLog) -> RPATaskLog:
        """校验单个任务的所有文件"""
        all_exist = True
        for file_val in task_log.file_validations:
            file_val.exists = self._check_file_exists(file_val.file_path)
            if not file_val.exists:
                all_exist = False
                print(f"[FileValidator] 文件缺失: {file_val.file_path}")

        # 如果有文件缺失且之前状态是成功，标记为异常
        if not all_exist and task_log.overall_status == TaskStatus.SUCCESS:
            task_log.overall_status = TaskStatus.FAILED
            missing = [f.file_path for f in task_log.file_validations if not f.exists]
            task_log.error_message = f"文件缺失: {', '.join(missing)}"

        return task_log

    def validate_all(self, task_logs: List[RPATaskLog]) -> List[RPATaskLog]:
        """批量校验所有任务的文件"""
        validated = []
        for task_log in task_logs:
            validated.append(self.validate_task(task_log))

        total_files = sum(len(t.file_validations) for t in validated)
        missing_files = sum(
            1 for t in validated
            for f in t.file_validations if not f.exists
        )
        print(f"[FileValidator] 文件校验完成: 共{total_files}个文件, 缺失{missing_files}个")
        return validated

    def _check_file_exists(self, file_path: str) -> bool:
        """检查文件是否存在"""
        if not file_path:
            return False
        try:
            return os.path.exists(file_path)
        except (OSError, ValueError):
            return False

    def get_missing_files_summary(self, task_logs: List[RPATaskLog]) -> List[dict]:
        """获取所有缺失文件的汇总"""
        missing = []
        for task in task_logs:
            for file_val in task.file_validations:
                if not file_val.exists:
                    missing.append({
                        "account": task.account,
                        "file_type": file_val.file_description,
                        "file_path": file_val.file_path
                    })
        return missing
