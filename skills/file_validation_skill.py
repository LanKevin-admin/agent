"""
文件校验技能 - 校验RPA生成的文件是否存在
"""
import logging
from typing import Dict, Any, List
from skills.base_skill import BaseSkill
from agent.tools import tool_validate_file, tool_validate_multiple_files

logger = logging.getLogger(__name__)


class FileValidationSkill(BaseSkill):
    """文件校验Skill"""
    
    def get_name(self) -> str:
        return "file_validation"
    
    def get_description(self) -> str:
        return "校验RPA生成的文件是否存在、时间是否正确、文件名日期是否匹配"
    
    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "validate_file",
                    "description": "校验单个文件",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "文件路径"
                            },
                            "description": {
                                "type": "string",
                                "description": "文件描述"
                            },
                            "expected_date_range": {
                                "type": "string",
                                "description": "预期的日期范围，格式：YYYY-MM-DD,YYYY-MM-DD"
                            }
                        },
                        "required": ["file_path", "description"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "validate_multiple_files",
                    "description": "批量校验多个文件",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_paths": {
                                "type": "array",
                                "description": "文件路径列表",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "path": {"type": "string"},
                                        "description": {"type": "string"},
                                        "expected_date_range": {"type": "string"}
                                    }
                                }
                            }
                        },
                        "required": ["file_paths"]
                    }
                }
            }
        ]
    
    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        try:
            if tool_name == "validate_file":
                return tool_validate_file(**arguments)
            elif tool_name == "validate_multiple_files":
                return tool_validate_multiple_files(**arguments)
            else:
                return {"error": f"未知工具: {tool_name}"}
        except Exception as e:
            logger.error(f"[FileValidationSkill] 执行{tool_name}失败: {e}")
            return {"error": str(e)}
