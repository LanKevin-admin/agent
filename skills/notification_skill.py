"""
通知技能 - 发送邮件、企业微信消息
"""
import logging
from typing import Dict, Any, List
from skills.base_skill import BaseSkill
from agent.tools import tool_send_email, tool_send_wecom_message

logger = logging.getLogger(__name__)


class NotificationSkill(BaseSkill):
    """通知发送Skill"""
    
    def get_name(self) -> str:
        return "notification"
    
    def get_description(self) -> str:
        return "发送邮件、企业微信消息通知"
    
    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "send_email",
                    "description": "发送邮件报告（支持附件）",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "recipient_type": {
                                "type": "string",
                                "enum": ["business", "tech"],
                                "description": "收件人类型：business=业务负责人，tech=技术运维"
                            },
                            "subject": {
                                "type": "string",
                                "description": "邮件标题"
                            },
                            "body": {
                                "type": "string",
                                "description": "邮件正文"
                            },
                            "attachment_path": {
                                "type": "string",
                                "description": "附件文件路径（可选），如果有附件需要一起发送"
                            }
                        },
                        "required": ["recipient_type", "subject", "body"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "send_wecom_message",
                    "description": "发送消息到企业微信群",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "content": {
                                "type": "string",
                                "description": "消息内容，支持Markdown"
                            },
                            "msg_type": {
                                "type": "string",
                                "enum": ["markdown", "text"],
                                "description": "消息类型"
                            }
                        },
                        "required": ["content"]
                    }
                }
            }
        ]
    
    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        try:
            if tool_name == "send_email":
                return tool_send_email(**arguments)
            elif tool_name == "send_wecom_message":
                return tool_send_wecom_message(**arguments)
            else:
                return {"error": f"未知工具: {tool_name}"}
        except Exception as e:
            logger.error(f"[NotificationSkill] 执行{tool_name}失败: {e}")
            return {"error": str(e)}
