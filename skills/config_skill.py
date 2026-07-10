"""
配置管理技能
"""
import logging
from typing import Dict, Any, List
from skills.base_skill import BaseSkill
from agent.config_tools import (
    tool_update_config,
    tool_save_analysis_template,
    tool_load_analysis_template,
    tool_list_templates
)

logger = logging.getLogger(__name__)


class ConfigSkill(BaseSkill):
    """配置管理Skill"""
    
    def get_name(self) -> str:
        return "config"
    
    def get_description(self) -> str:
        return "更新系统配置、保存/加载分析模板"
    
    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "update_config",
                    "description": "更新系统配置（飞书、AI、邮件等）",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "config_updates": {
                                "type": "string",
                                "description": "配置更新JSON字符串"
                            }
                        },
                        "required": ["config_updates"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "save_analysis_template",
                    "description": "保存分析模板",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "template_name": {"type": "string"},
                            "template_config": {"type": "string"}
                        },
                        "required": ["template_name", "template_config"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "load_analysis_template",
                    "description": "加载已保存的分析模板",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "template_name": {"type": "string"}
                        },
                        "required": ["template_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_templates",
                    "description": "列出所有已保存的模板",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            }
        ]
    
    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        try:
            if tool_name == "update_config":
                return tool_update_config(**arguments)
            elif tool_name == "save_analysis_template":
                return tool_save_analysis_template(**arguments)
            elif tool_name == "load_analysis_template":
                return tool_load_analysis_template(**arguments)
            elif tool_name == "list_templates":
                return tool_list_templates()
            else:
                return {"error": f"未知工具: {tool_name}"}
        except Exception as e:
            logger.error(f"[ConfigSkill] 执行{tool_name}失败: {e}")
            return {"error": str(e)}
