"""
Agent工具实现层 - 每个工具的实际执行逻辑
Agent通过大模型决定调用哪个工具，这里是工具的具体实现
"""
import os
import json
import time
import logging
from datetime import datetime
from typing import List, Dict, Any, Union

from config.settings import config

logger = logging.getLogger(__name__)


# ==================== 消息拉取工具 ====================

def tool_fetch_messages(start_date: str, end_date: str, start_time: str = None, end_time: str = None) -> Dict[str, Any]:
    """
    从飞书群拉取指定日期范围的消息
    Agent会根据用户指令（如"查最近7天"）自动传入日期参数

    Args:
        start_date: 起始日期，格式：YYYY-MM-DD
        end_date: 结束日期，格式：YYYY-MM-DD
        start_time: 起始时间（可选），格式：HH:MM，如 "14:00"
        end_time: 结束时间（可选），格式：HH:MM，如 "18:00"
    """
    from feishu.client import feishu_client

    # 解析起始日期+时间
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    if start_time:
        try:
            hour, minute = map(int, start_time.split(":"))
            start_dt = start_dt.replace(hour=hour, minute=minute, second=0)
        except:
            logger.warning(f"时间格式错误: {start_time}，使用默认00:00")

    # 解析结束日期+时间
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    if end_time:
        try:
            hour, minute = map(int, end_time.split(":"))
            end_dt = end_dt.replace(hour=hour, minute=minute, second=59)
        except:
            logger.warning(f"时间格式错误: {end_time}，使用默认23:59")
    else:
        end_dt = end_dt.replace(hour=23, minute=59, second=59)

    start_ts = str(int(start_dt.timestamp()))
    end_ts = str(int(end_dt.timestamp()))

    messages = []
    page_token = ""
    has_more = True
    max_pages = 50  # 防止死循环，最多拉50页(2500条)

    page_count = 0
    while has_more and page_count < max_pages:
        page_count += 1
        params = {
            "container_id_type": "chat",
            "container_id": config.feishu.TARGET_CHAT_ID,
            "start_time": start_ts,
            "end_time": end_ts,
            "sort_type": "ByCreateTimeAsc",
            "page_size": 50,
        }
        if page_token:
            params["page_token"] = page_token

        resp = feishu_client.get("/im/v1/messages", params=params)
        if resp.get("code") != 0:
            return {"success": False, "error": f"API错误: {resp.get('msg', '未知错误')}"}

        data = resp.get("data", {})
        items = data.get("items", [])

        for item in items:
            msg_type = item.get("msg_type", "")
            if msg_type == "text":
                try:
                    content = json.loads(item.get("body", {}).get("content", "{}"))
                    text = content.get("text", "").strip()
                    if text:
                        create_time = item.get("create_time", "")
                        messages.append({
                            "text": text,
                            "time": create_time,
                            "sender": item.get("sender", {}).get("id", "")
                        })
                except json.JSONDecodeError:
                    continue

        has_more = data.get("has_more", False)
        page_token = data.get("page_token", "")

    return {
        "success": True,
        "message_count": len(messages),
        "date_range": f"{start_date} ~ {end_date}",
        "messages": messages
    }


# ==================== 日志过滤工具 ====================

def tool_filter_rpa_logs(messages: List[Union[str, Dict]]) -> Dict[str, Any]:
    """
    智能过滤RPA日志 - 兼容字符串列表和对象列表两种输入
    Agent从fetch_messages拿到的是对象列表，也可以直接传字符串列表
    """
    import re

    rpa_keywords = ["账号", "登录成功", "登录失败", "查询成功", "查询失败",
                    "保存路径", "退出成功", "退出失败", "流水查询范围", "余额"]
    path_pattern = re.compile(r'[A-Z]:\\[^\s]+')

    rpa_logs = []
    non_rpa_count = 0

    for msg in messages:
        # 兼容两种格式：字符串 或 {"text": "...", "time": "..."}
        text = msg if isinstance(msg, str) else msg.get("text", "")
        if not text:
            continue

        keyword_hits = sum(1 for kw in rpa_keywords if kw in text)

        # 命中2个以上关键词 或 包含文件路径 → RPA日志
        if keyword_hits >= 2 or path_pattern.search(text):
            rpa_logs.append(text)
        else:
            non_rpa_count += 1

    return {
        "success": True,
        "rpa_log_count": len(rpa_logs),
        "filtered_out_count": non_rpa_count,
        "rpa_logs": rpa_logs
    }


# ==================== 文件校验工具 ====================

def tool_validate_file(file_path: str, description: str = "", expected_date_range: str = None) -> Dict[str, Any]:
    """
    校验单个文件是否存在

    Args:
        file_path: 文件完整路径
        description: 文件描述（如：流水文件、余额截图等）
        expected_date_range: 预期的日期范围，如 "2026-01-01,2026-01-31"，用于校验文件时间合理性
    """
    exists = os.path.exists(file_path)
    result = {
        "file_path": file_path,
        "description": description or _guess_file_type(file_path),
        "exists": exists,
        "warnings": []
    }

    if exists:
        stat = os.stat(file_path)
        file_mtime = datetime.fromtimestamp(stat.st_mtime)
        result["file_size"] = stat.st_size
        result["modified_time"] = file_mtime.strftime("%Y-%m-%d %H:%M:%S")

        # 新增：时间一致性校验
        # 检查1：文件修改时间是否是今天（如果是今天的RPA任务，应该今天生成文件）
        today = datetime.now().date()
        file_date = file_mtime.date()
        days_old = (today - file_date).days

        if days_old > 1:
            result["warnings"].append(
                f"文件修改时间为{days_old}天前（{file_date}），若是今日RPA任务产出，时间可能不符"
            )

        # 检查2：如果日志里有日期范围，验证文件名是否包含对应日期
        if expected_date_range:
            import re
            # 提取日期范围中的起止日期
            date_parts = re.findall(r'(\d{4})-?(\d{2})-?(\d{2})', expected_date_range)
            if date_parts and len(date_parts) >= 2:
                # 起始日期和结束日期（多种格式）
                start_date_full = f"{date_parts[0][0]}-{date_parts[0][1]}-{date_parts[0][2]}"  # 2026-01-01
                start_date_compact = f"{date_parts[0][0]}{date_parts[0][1]}{date_parts[0][2]}"  # 20260101

                end_date_full = f"{date_parts[1][0]}-{date_parts[1][1]}-{date_parts[1][2]}"
                end_date_compact = f"{date_parts[1][0]}{date_parts[1][1]}{date_parts[1][2]}"

                # 获取文件名（不含路径）
                filename = os.path.basename(file_path)
                filename_lower = filename.lower()

                # 检查文件名是否包含任一格式的日期
                has_start = (start_date_full in filename or start_date_compact in filename or
                            start_date_full in filename_lower or start_date_compact in filename_lower)
                has_end = (end_date_full in filename or end_date_compact in filename or
                          end_date_full in filename_lower or end_date_compact in filename_lower)

                if not (has_start or has_end):
                    result["warnings"].append(
                        f"文件名未包含查询日期（期望：{start_date_compact}-{end_date_compact} 或 {start_date_full}至{end_date_full}），"
                        f"实际文件名：{filename}。请确认文件是否对应该日期范围的查询结果"
                    )
                elif not (has_start and has_end):
                    result["warnings"].append(
                        f"文件名仅包含部分日期（起始/结束日期之一），建议检查完整性"
                    )

    return result


def tool_validate_multiple_files(file_paths: List[Dict]) -> Dict[str, Any]:
    """批量校验多个文件"""
    results = []
    all_exist = True

    for item in file_paths:
        path = item.get("path", "")
        desc = item.get("description", "")
        result = tool_validate_file(path, desc)
        results.append(result)
        if not result["exists"]:
            all_exist = False

    total = len(results)
    exist_count = sum(1 for r in results if r["exists"])
    missing_count = total - exist_count

    return {
        "success": True,
        "total_files": total,
        "exist_count": exist_count,
        "missing_count": missing_count,
        "all_exist": all_exist,
        "details": results
    }


# ==================== 飞书消息推送工具 ====================

def tool_send_feishu_message(content: str) -> Dict[str, Any]:
    """向飞书群发送消息"""
    from feishu.message_sender import MessageSender

    sender = MessageSender()
    success = sender.send_report(content)
    return {
        "success": success,
        "message": "消息已发送到飞书群" if success else "发送失败"
    }


# ==================== 邮件发送工具 ====================

def tool_send_email(recipient_type: str, subject: str, body: str, attachment_path: str = None) -> Dict[str, Any]:
    """发送邮件（支持附件）"""
    from notify.email_sender import EmailSender

    sender = EmailSender()
    recipients = (config.email.BUSINESS_EMAILS if recipient_type == "business"
                  else config.email.TECH_EMAILS)

    success = sender.send_direct(subject, body, recipients, attachment_path)

    result = {
        "success": success,
        "recipient_type": recipient_type,
        "recipients": recipients,
        "message": f"邮件已发送至{'业务负责人' if recipient_type == 'business' else '技术运维'}"
    }

    if attachment_path:
        result["attachment"] = attachment_path
        result["message"] += f"（含附件）"

    return result


# ==================== 企业微信推送工具 ====================

def tool_send_wecom_message(content: str, msg_type: str = "markdown") -> Dict[str, Any]:
    """
    发送消息到企业微信群

    Args:
        content: 消息内容
        msg_type: 消息类型，markdown或text
    """
    from notify.wecom_sender import wecom_sender

    if msg_type == "markdown":
        success = wecom_sender.send_markdown(content)
    else:
        success = wecom_sender.send_text(content)

    return {
        "success": success,
        "message": "消息已发送到企业微信群" if success else "发送失败（可能未配置Webhook）"
    }


# ==================== 领导汇报生成工具 ====================

def tool_generate_executive_report(analysis_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    生成领导级汇报

    Args:
        analysis_data: RPA分析结果数据，需包含：
            - total_count: 总数
            - success_count: 成功数
            - failed_count: 失败数
            - failed_items: 失败项列表 [{"account": "", "failure_reason": "", ...}]
    """
    from report.executive_report import executive_report_generator

    result = executive_report_generator.generate_executive_summary(analysis_data)

    return {
        "success": True,
        "summary": result["summary"],
        "detail_file": result["detail_file"],
        "stats": result["stats"],
        "message": f"领导汇报已生成，成功率{result['stats']['success_rate']}%"
    }


# ==================== 任务创建工具 ====================

def tool_create_task(task_type: str, task_params: Dict, priority: str = "medium") -> Dict[str, Any]:
    """
    创建任务 - Agent可以自主创建后续要执行的任务
    比如发现某个文件需要校验，就创建一个validate_file任务
    """
    task = {
        "task_id": f"task_{int(time.time())}_{task_type}",
        "task_type": task_type,
        "params": task_params,
        "priority": priority,
        "status": "created",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    # 立即执行任务
    if task_type == "validate_file":
        result = tool_validate_file(
            task_params.get("file_path", ""),
            task_params.get("description", "")
        )
        task["status"] = "completed"
        task["result"] = result
    elif task_type == "send_notification":
        task["status"] = "pending"
        task["message"] = "通知任务已创建，等待执行"
    elif task_type == "analyze_screenshot":
        # 预留：后续接入多模态AI分析截图
        task["status"] = "pending"
        task["message"] = "截图分析任务已创建（功能开发中）"
    elif task_type == "check_data":
        task["status"] = "pending"
        task["message"] = "数据校验任务已创建"

    return task


# ==================== 辅助函数 ====================

def _guess_file_type(file_path: str) -> str:
    """根据路径推断文件类型"""
    path_lower = file_path.lower()
    if "流水" in path_lower:
        return "流水文件"
    elif "余额" in path_lower:
        return "余额文件"
    elif path_lower.endswith(('.png', '.jpg', '.jpeg', '.bmp')):
        return "截图文件"
    elif path_lower.endswith(('.xlsx', '.xls', '.csv')):
        return "数据表格"
    return "业务文件"
