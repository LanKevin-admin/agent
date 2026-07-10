"""数据模型定义 - RPA日志结构化数据"""
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class LoginStatus(Enum):
    """登录状态"""
    SUCCESS = "登录成功"
    FAIL_PASSWORD = "密码错误"
    FAIL_TIMEOUT = "页面卡顿"
    FAIL_UNKNOWN = "未知错误"


class TaskStatus(Enum):
    """流程执行状态"""
    SUCCESS = "成功"
    FAILED = "失败"


@dataclass
class FileValidation:
    """文件校验结果"""
    file_path: str
    exists: bool
    file_description: str = ""  # 如：流水文件、余额截图等


@dataclass
class RPATaskLog:
    """单个RPA流程的解析结果"""
    account: str  # 账号
    login_status: LoginStatus  # 登录状态
    login_fail_reason: Optional[str] = None  # 登录失败原因

    # 业务操作记录
    operations: list = field(default_factory=list)  # 操作步骤列表

    # 流水查询
    query_range: Optional[str] = None  # 查询范围，如 "2026-05-01,2026-06-01"
    query_result: Optional[str] = None  # 查询结果描述

    # 文件校验
    file_validations: list = field(default_factory=list)  # FileValidation列表

    # 退出状态
    exit_status: str = ""

    # 整体状态
    overall_status: TaskStatus = TaskStatus.SUCCESS
    error_message: Optional[str] = None


@dataclass
class DailyReport:
    """每日汇总报告"""
    date: str
    total_tasks: int = 0
    success_count: int = 0
    fail_count: int = 0
    task_logs: list = field(default_factory=list)  # RPATaskLog列表
    has_error: bool = False
    error_tasks: list = field(default_factory=list)  # 异常任务列表
    missing_files: list = field(default_factory=list)  # 缺失文件列表
