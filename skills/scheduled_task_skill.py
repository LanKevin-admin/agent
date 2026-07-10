"""
定时任务管理技能
让AI能够通过对话创建、查看、删除定时任务
"""
import logging
from typing import Dict, Any, List
from skills.base_skill import BaseSkill
from agent.scheduled_task_tools import (
    tool_create_scheduled_task,
    tool_list_scheduled_tasks,
    tool_delete_scheduled_task
)

logger = logging.getLogger(__name__)


class ScheduledTaskSkill(BaseSkill):
    """定时任务管理Skill"""
    
    def get_name(self) -> str:
        return "scheduled_task"
    
    def get_description(self) -> str:
        return "创建、查看、删除定时任务（如每天18点自动分析日志）"
    
    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "create_scheduled_task",
                    "description": "创建定时任务，让系统在指定时间自动执行某个操作",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "task_name": {
                                "type": "string",
                                "description": "任务名称，如：每日日志汇报"
                            },
                            "task_type": {
                                "type": "string",
                                "description": "任务类型：analyze（分析）/report（报告）/sync（同步）/custom（自定义）",
                                "enum": ["analyze", "report", "sync", "custom"]
                            },
                            "cron_expression": {
                                "type": "string",
                                "description": "Cron表达式，如：0 18 * * *（每天18:00）"
                            },
                            "query_text": {
                                "type": "string",
                                "description": "要执行的指令，如：分析今天的RPA日志并发送邮件给业务负责人"
                            },
                            "description": {
                                "type": "string",
                                "description": "任务描述（可选）"
                            }
                        },
                        "required": ["task_name", "task_type", "cron_expression", "query_text"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_scheduled_tasks",
                    "description": "列出所有已创建的定时任务",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "delete_scheduled_task",
                    "description": "删除指定的定时任务",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "task_name": {
                                "type": "string",
                                "description": "要删除的任务名称"
                            }
                        },
                        "required": ["task_name"]
                    }
                }
            }
        ]
    
    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        try:
            if tool_name == "create_scheduled_task":
                return tool_create_scheduled_task(**arguments)
            elif tool_name == "list_scheduled_tasks":
                return tool_list_scheduled_tasks()
            elif tool_name == "delete_scheduled_task":
                return tool_delete_scheduled_task(**arguments)
            else:
                return {"error": f"未知工具: {tool_name}"}
        except Exception as e:
            logger.error(f"[ScheduledTaskSkill] 执行{tool_name}失败: {e}")
            return {"error": str(e)}
