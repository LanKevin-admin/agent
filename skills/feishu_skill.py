"""
飞书消息技能 - 从飞书群拉取和过滤RPA日志
"""
import logging
from typing import Dict, Any, List
from skills.base_skill import BaseSkill
from agent.tools import tool_fetch_messages, tool_filter_rpa_logs, tool_send_feishu_message

logger = logging.getLogger(__name__)


class FeishuSkill(BaseSkill):
    """飞书消息处理Skill"""
    
    def get_name(self) -> str:
        return "feishu"
    
    def get_description(self) -> str:
        return "从飞书群拉取消息、过滤RPA日志、发送报告"
    
    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "fetch_messages",
                    "description": "从飞书群拉取指定时间范围的消息",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "start_date": {
                                "type": "string",
                                "description": "开始日期，格式：YYYY-MM-DD"
                            },
                            "end_date": {
                                "type": "string",
                                "description": "结束日期，格式：YYYY-MM-DD"
                            },
                            "start_time": {
                                "type": "string",
                                "description": "可选，开始时间HH:MM，如14:00"
                            },
                            "end_time": {
                                "type": "string",
                                "description": "可选，结束时间HH:MM，如23:59"
                            }
                        },
                        "required": ["start_date", "end_date"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "filter_rpa_logs",
                    "description": "从消息列表中过滤出RPA运行日志",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "messages": {
                                "type": "array",
                                "description": "消息列表",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "text": {"type": "string"},
                                        "time": {"type": "string"},
                                        "sender": {"type": "string"}
                                    }
                                }
                            }
                        },
                        "required": ["messages"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "send_feishu_message",
                    "description": "向飞书群发送报告消息",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "content": {
                                "type": "string",
                                "description": "要发送的消息内容"
                            }
                        },
                        "required": ["content"]
                    }
                }
            }
        ]
    
    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """执行工具"""
        try:
            if tool_name == "fetch_messages":
                return tool_fetch_messages(**arguments)
            elif tool_name == "filter_rpa_logs":
                return tool_filter_rpa_logs(**arguments)
            elif tool_name == "send_feishu_message":
                return tool_send_feishu_message(**arguments)
            else:
                return {"error": f"未知工具: {tool_name}"}
        except Exception as e:
            logger.error(f"[FeishuSkill] 执行{tool_name}失败: {e}")
            return {"error": str(e)}
