"""
Skill基类 - 参考OpenClaw设计
每个功能封装成独立的Skill，便于扩展和维护
"""
import os
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod


class BaseSkill(ABC):
    """Skill基类"""

    def __init__(self):
        self.name = self.__class__.__name__
        self.enabled = True
        self._prompt_cache = None

    @abstractmethod
    def get_name(self) -> str:
        """返回Skill名称"""
        pass

    @abstractmethod
    def get_description(self) -> str:
        """返回Skill描述"""
        pass

    @abstractmethod
    def get_tools(self) -> List[Dict[str, Any]]:
        """
        返回Skill提供的工具定义（OpenAI function calling格式）

        Returns:
            [
                {
                    "type": "function",
                    "function": {
                        "name": "tool_name",
                        "description": "工具描述",
                        "parameters": {...}
                    }
                },
                ...
            ]
        """
        pass

    @abstractmethod
    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行工具调用

        Args:
            tool_name: 工具名称
            arguments: 工具参数

        Returns:
            工具执行结果
        """
        pass

    def get_prompt_fragment(self) -> str:
        """
        返回此Skill的提示词片段（从MD文件加载）
        子类可重写以自定义提示词加载逻辑
        """
        if self._prompt_cache:
            return self._prompt_cache

        # 尝试从prompts/skills/{skill_name}.md加载
        skill_name = self.get_name()
        prompt_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'prompts', 'skills', f'{skill_name}.md'
        )

        if os.path.exists(prompt_path):
            with open(prompt_path, 'r', encoding='utf-8') as f:
                self._prompt_cache = f.read()
                return self._prompt_cache

        return ""

    def validate_arguments(self, tool_name: str, arguments: Dict[str, Any]) -> bool:
        """
        验证工具参数是否合法

        Returns:
            True if valid, False otherwise
        """
        return True

    def on_enable(self):
        """Skill启用时的回调"""
        pass

    def on_disable(self):
        """Skill禁用时的回调"""
        pass
