"""
报告生成技能
"""
import logging
from typing import Dict, Any, List
from skills.base_skill import BaseSkill
from agent.tools import tool_generate_executive_report

logger = logging.getLogger(__name__)


class ReportSkill(BaseSkill):
    """报告生成Skill"""
    
    def get_name(self) -> str:
        return "report"
    
    def get_description(self) -> str:
        return "生成简洁的RPA运行汇总报告（含成功率、失败原因、TXT附件）"
    
    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "generate_executive_report",
                    "description": "生成简洁汇总报告",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "analysis_data": {
                                "type": "object",
                                "description": "RPA分析数据",
                                "properties": {
                                    "total_count": {"type": "integer"},
                                    "success_count": {"type": "integer"},
                                    "failed_count": {"type": "integer"},
                                    "failed_items": {
                                        "type": "array",
                                        "items": {"type": "object"}
                                    }
                                }
                            }
                        },
                        "required": ["analysis_data"]
                    }
                }
            }
        ]
    
    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        try:
            if tool_name == "generate_executive_report":
                return tool_generate_executive_report(**arguments)
            else:
                return {"error": f"未知工具: {tool_name}"}
        except Exception as e:
            logger.error(f"[ReportSkill] 执行{tool_name}失败: {e}")
            return {"error": str(e)}
