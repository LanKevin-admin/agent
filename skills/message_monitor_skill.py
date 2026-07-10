"""
飞书消息监听Skill - 自动检测并回复@消息
"""
import logging
from typing import Dict, Any
from skills.base_skill import BaseSkill

logger = logging.getLogger(__name__)


class MessageMonitorSkill(BaseSkill):
    """消息监听Skill - 不提供给AI调用，由后台定时任务驱动"""
    
    def get_name(self) -> str:
        return "message_monitor"
    
    def get_description(self) -> str:
        return "飞书消息监听（后台自动运行）"
    
    def get_tools(self):
        # 这个Skill不提供工具给AI，由后台任务驱动
        return []
    
    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        return {"error": "此Skill不提供工具调用"}
