"""
Skill管理器 - 参考OpenClaw设计
负责加载、注册、管理所有Skills
"""
import os
import logging
from typing import Dict, List, Any, Optional
from skills.base_skill import BaseSkill

logger = logging.getLogger(__name__)


class SkillManager:
    """Skill管理器"""
    
    def __init__(self):
        self.skills: Dict[str, BaseSkill] = {}
        self.enabled_skills: List[str] = []
    
    def register_skill(self, skill: BaseSkill):
        """注册Skill"""
        skill_name = skill.get_name()
        self.skills[skill_name] = skill
        if skill.enabled:
            self.enabled_skills.append(skill_name)
        logger.info(f"[SkillManager] 注册Skill: {skill_name} - {skill.get_description()}")
    
    def get_skill(self, skill_name: str) -> Optional[BaseSkill]:
        """获取Skill实例"""
        return self.skills.get(skill_name)
    
    def get_all_tools(self) -> List[Dict[str, Any]]:
        """
        获取所有已启用Skill的工具定义
        用于注册到Agent的tools参数
        """
        all_tools = []
        for skill_name in self.enabled_skills:
            skill = self.skills[skill_name]
            tools = skill.get_tools()
            all_tools.extend(tools)
        return all_tools
    
    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行工具调用，自动路由到对应的Skill
        """
        # 遍历所有Skill，找到提供该工具的Skill
        for skill_name in self.enabled_skills:
            skill = self.skills[skill_name]
            # 检查该Skill是否提供此工具
            for tool in skill.get_tools():
                if tool["function"]["name"] == tool_name:
                    logger.info(f"[SkillManager] 调用{skill_name}.{tool_name}")
                    return skill.execute_tool(tool_name, arguments)
        
        error_msg = f"未找到工具: {tool_name}"
        logger.error(f"[SkillManager] {error_msg}")
        return {"error": error_msg}
    
    def get_system_prompt(self, base_prompt_path: str = None) -> str:
        """
        构建完整的系统提示词
        从MD文件加载基础提示词，然后附加每个Skill的提示词片段
        
        Args:
            base_prompt_path: 基础提示词MD文件路径
            
        Returns:
            完整的系统提示词
        """
        # 加载基础提示词
        if base_prompt_path and os.path.exists(base_prompt_path):
            with open(base_prompt_path, 'r', encoding='utf-8') as f:
                base_prompt = f.read()
        else:
            base_prompt = "你是一个RPA运维监控Agent。"
        
        # 附加每个Skill的提示词片段
        skill_prompts = []
        for skill_name in self.enabled_skills:
            skill = self.skills[skill_name]
            fragment = skill.get_prompt_fragment()
            if fragment:
                skill_prompts.append(fragment)
        
        # 组合
        if skill_prompts:
            full_prompt = base_prompt + "\n\n" + "\n\n".join(skill_prompts)
        else:
            full_prompt = base_prompt
        
        return full_prompt
    
    def enable_skill(self, skill_name: str):
        """启用Skill"""
        if skill_name in self.skills:
            skill = self.skills[skill_name]
            skill.enabled = True
            if skill_name not in self.enabled_skills:
                self.enabled_skills.append(skill_name)
            skill.on_enable()
            logger.info(f"[SkillManager] 启用Skill: {skill_name}")
    
    def disable_skill(self, skill_name: str):
        """禁用Skill"""
        if skill_name in self.skills:
            skill = self.skills[skill_name]
            skill.enabled = False
            if skill_name in self.enabled_skills:
                self.enabled_skills.remove(skill_name)
            skill.on_disable()
            logger.info(f"[SkillManager] 禁用Skill: {skill_name}")
    
    def list_skills(self) -> List[Dict[str, Any]]:
        """列出所有Skill"""
        return [
            {
                "name": skill.get_name(),
                "description": skill.get_description(),
                "enabled": skill.enabled,
                "tools_count": len(skill.get_tools())
            }
            for skill in self.skills.values()
        ]
