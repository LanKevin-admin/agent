"""
数据库查询技能
"""
import logging
from typing import Dict, Any, List
from skills.base_skill import BaseSkill
from agent.db_tools import tool_query_rpa_database

logger = logging.getLogger(__name__)


class DatabaseSkill(BaseSkill):
    """数据库查询Skill"""
    
    def get_name(self) -> str:
        return "database"
    
    def get_description(self) -> str:
        return "从MySQL/PostgreSQL/SQLite数据库查询RPA运行记录"
    
    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "query_rpa_database",
                    "description": "从数据库查询RPA运行日志",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "db_config_json": {
                                "type": "string",
                                "description": "数据库配置JSON字符串"
                            },
                            "start_date": {
                                "type": "string",
                                "description": "开始日期 YYYY-MM-DD"
                            },
                            "end_date": {
                                "type": "string",
                                "description": "结束日期 YYYY-MM-DD"
                            },
                            "custom_query": {
                                "type": "string",
                                "description": "可选，自定义SQL"
                            },
                            "field_mapping": {
                                "type": "string",
                                "description": "可选，字段映射JSON"
                            }
                        },
                        "required": ["db_config_json", "start_date", "end_date"]
                    }
                }
            }
        ]
    
    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        try:
            if tool_name == "query_rpa_database":
                return tool_query_rpa_database(**arguments)
            else:
                return {"error": f"未知工具: {tool_name}"}
        except Exception as e:
            logger.error(f"[DatabaseSkill] 执行{tool_name}失败: {e}")
            return {"error": str(e)}
