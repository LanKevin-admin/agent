"""
图灵测试Skill - 让AI表现得更像人类
"""
import logging
import time
import random
from typing import Dict, Any, List
from skills.base_skill import BaseSkill

logger = logging.getLogger(__name__)


class TuringTestSkill(BaseSkill):
    """
    图灵测试Skill
    提供人性化响应功能，让AI回复更自然
    """
    
    def get_name(self) -> str:
        return "turing_test"
    
    def get_description(self) -> str:
        return "图灵测试：模拟人类运维专家的响应风格"
    
    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "human_like_delay",
                    "description": "模拟人类思考和打字延迟（内部工具，一般不需要显式调用）",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "action_type": {
                                "type": "string",
                                "enum": ["thinking", "typing", "checking"],
                                "description": "动作类型：thinking=思考，typing=打字，checking=检查"
                            },
                            "text_length": {
                                "type": "integer",
                                "description": "文本长度（用于计算打字时间）"
                            }
                        },
                        "required": ["action_type"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "humanize_response",
                    "description": "将机器式回复转换为人性化回复",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "machine_response": {
                                "type": "string",
                                "description": "机器式回复"
                            },
                            "emotion": {
                                "type": "string",
                                "enum": ["neutral", "positive", "concern", "urgent"],
                                "description": "情绪：neutral=中性，positive=积极，concern=担忧，urgent=紧急"
                            }
                        },
                        "required": ["machine_response"]
                    }
                }
            }
        ]
    
    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        try:
            if tool_name == "human_like_delay":
                return self._human_like_delay(**arguments)
            elif tool_name == "humanize_response":
                return self._humanize_response(**arguments)
            else:
                return {"error": f"未知工具: {tool_name}"}
        except Exception as e:
            logger.error(f"[TuringTestSkill] 执行{tool_name}失败: {e}")
            return {"error": str(e)}
    
    def _human_like_delay(self, action_type: str, text_length: int = 0) -> Dict[str, Any]:
        """
        模拟人类延迟
        
        Returns:
            {"delay_seconds": 1.5, "message": "思考中..."}
        """
        if action_type == "thinking":
            delay = random.uniform(0.5, 2.0)
            message = random.choice(["思考中...", "让我想想...", "稍等..."])
        elif action_type == "typing":
            # 人类打字速度：40-60字/分钟，约0.7-1字/秒
            delay = text_length / random.uniform(40, 60) * 60
            delay = min(delay, 5.0)  # 最多5秒
            message = "正在输入..."
        elif action_type == "checking":
            delay = random.uniform(1.0, 3.0)
            message = random.choice(["检查中...", "查一下...", "看看..."])
        else:
            delay = 0.5
            message = "处理中..."
        
        # 实际执行延迟（可选，看需求）
        # time.sleep(delay)
        
        return {
            "delay_seconds": round(delay, 2),
            "message": message
        }
    
    def _humanize_response(self, machine_response: str, emotion: str = "neutral") -> Dict[str, Any]:
        """
        将机器式回复转换为人性化回复
        
        示例：
        输入："总运行数12，成功10，失败2，成功率83.33%"
        输出："嗯，跑了12个任务，10个成功，2个挂了，成功率83%左右 ✅"
        """
        humanized = machine_response
        
        # 替换正式词汇为口语
        replacements = {
            "总运行数": "一共跑了",
            "成功数": "成功",
            "失败数": "失败",
            "失败": "挂了",
            "完成": "搞定",
            "执行": "跑",
            "查询": "查",
            "配置": "设置",
            "已": "",
            "请": "",
        }
        
        for old, new in replacements.items():
            humanized = humanized.replace(old, new)
        
        # 精确数字转约数
        import re
        # 83.33% → 83%左右
        humanized = re.sub(r'(\d+)\.\d+%', r'\1%左右', humanized)
        
        # 添加语气词和emoji
        prefixes = {
            "neutral": ["嗯，", "好的，", ""],
            "positive": ["不错，", "挺好，", "好消息，"],
            "concern": ["注意，", "有点问题，", "嗯..."],
            "urgent": ["紧急！", "注意！", ""]
        }
        
        suffixes = {
            "neutral": [" ✅", "", " 👌"],
            "positive": [" ✅", " 🎉", " 👍"],
            "concern": [" ⚠️", " 🤔", ""],
            "urgent": [" ❌", " ⚠️", " 🚨"]
        }
        
        prefix = random.choice(prefixes.get(emotion, prefixes["neutral"]))
        suffix = random.choice(suffixes.get(emotion, suffixes["neutral"]))
        
        humanized = prefix + humanized + suffix
        
        return {
            "original": machine_response,
            "humanized": humanized,
            "emotion": emotion
        }
