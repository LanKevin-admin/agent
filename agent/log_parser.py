"""RPA日志结构化解析器 - Agent核心解析逻辑"""
import re
from typing import List, Optional
from models.schemas import RPATaskLog, LoginStatus, TaskStatus, FileValidation


class LogParser:
    """
    RPA日志解析器
    将飞书群中的日志文本解析为结构化数据

    日志格式示例：
    xxxx账号
    登录成功
    流水查询范围：2026-05-01,2026-06-01
    查询成功流水保存路径：C:\\xxxx-20260501-20260601-流水.xlsx
    退出成功
    """

    def parse_single_log(self, log_text: str) -> RPATaskLog:
        """解析单条RPA流程日志"""
        lines = [line.strip() for line in log_text.strip().split('\n') if line.strip()]

        task_log = RPATaskLog(
            account=self._extract_account(lines),
            login_status=self._extract_login_status(lines),
        )

        # 解析登录失败原因
        if task_log.login_status != LoginStatus.SUCCESS:
            task_log.login_fail_reason = self._extract_fail_reason(lines)
            task_log.overall_status = TaskStatus.FAILED
            task_log.error_message = f"登录失败: {task_log.login_fail_reason}"

        # 解析查询范围
        task_log.query_range = self._extract_query_range(lines)
        task_log.query_result = self._extract_query_result(lines)

        # 提取所有文件路径
        file_paths = self._extract_file_paths(lines)
        task_log.file_validations = [
            FileValidation(file_path=fp, exists=False, file_description=self._guess_file_type(fp))
            for fp in file_paths
        ]

        # 退出状态
        task_log.exit_status = self._extract_exit_status(lines)

        # 提取操作步骤
        task_log.operations = self._extract_operations(lines)

        return task_log

    def parse_all_logs(self, log_texts: List[str]) -> List[RPATaskLog]:
        """批量解析所有日志"""
        results = []
        for log_text in log_texts:
            try:
                task_log = self.parse_single_log(log_text)
                results.append(task_log)
            except Exception as e:
                print(f"[LogParser] 解析日志失败: {e}\n原文: {log_text[:100]}...")
        return results

    def _extract_account(self, lines: List[str]) -> str:
        """提取账号"""
        for line in lines:
            if "账号" in line:
                # 匹配 "xxxx账号" 格式
                match = re.match(r'(.+?)账号', line)
                if match:
                    return match.group(1).strip()
                return line.replace("账号", "").strip()
        return "未知账号"

    def _extract_login_status(self, lines: List[str]) -> LoginStatus:
        """提取登录状态"""
        for line in lines:
            if "登录成功" in line:
                return LoginStatus.SUCCESS
            elif "密码错误" in line:
                return LoginStatus.FAIL_PASSWORD
            elif "页面卡顿" in line or "超时" in line:
                return LoginStatus.FAIL_TIMEOUT
            elif "登录失败" in line:
                return LoginStatus.FAIL_UNKNOWN
        return LoginStatus.SUCCESS

    def _extract_fail_reason(self, lines: List[str]) -> str:
        """提取登录失败原因"""
        for line in lines:
            if "失败" in line and "原因" in line:
                return line.split("原因")[-1].strip().lstrip("：:").strip()
            if "密码错误" in line:
                return "密码错误"
            if "页面卡顿" in line:
                return "页面卡顿/加载超时"
        return "未知原因"

    def _extract_query_range(self, lines: List[str]) -> Optional[str]:
        """提取查询范围"""
        for line in lines:
            if "查询范围" in line:
                match = re.search(r'[\d]{4}-[\d]{2}-[\d]{2}.*?[\d]{4}-[\d]{2}-[\d]{2}', line)
                if match:
                    return match.group(0)
                return line.split("：")[-1].strip() if "：" in line else line.split(":")[-1].strip()
        return None

    def _extract_query_result(self, lines: List[str]) -> Optional[str]:
        """提取查询结果"""
        for line in lines:
            if "查询成功" in line:
                return "查询成功"
            if "查询失败" in line or "无数据" in line:
                return "查询失败/无数据"
        return None

    def _extract_file_paths(self, lines: List[str]) -> List[str]:
        """提取所有文件保存路径"""
        paths = []
        for line in lines:
            # 匹配 Windows路径格式 C:\xxx\xxx.xlsx
            matches = re.findall(r'[A-Z]:\\[^\s，,。]+', line)
            paths.extend(matches)
        return paths

    def _extract_exit_status(self, lines: List[str]) -> str:
        """提取退出状态"""
        for line in lines:
            if "退出成功" in line:
                return "退出成功"
            if "退出失败" in line:
                return "退出失败"
        return "未检测到退出状态"

    def _extract_operations(self, lines: List[str]) -> List[str]:
        """提取操作步骤"""
        return [line for line in lines if line.strip()]

    def _guess_file_type(self, file_path: str) -> str:
        """根据路径猜测文件类型"""
        path_lower = file_path.lower()
        if "流水" in path_lower:
            return "流水文件"
        elif "余额" in path_lower:
            return "余额截图"
        elif "截图" in path_lower or path_lower.endswith(('.png', '.jpg', '.jpeg')):
            return "截图文件"
        elif path_lower.endswith('.xlsx') or path_lower.endswith('.xls'):
            return "Excel文件"
        return "业务文件"
