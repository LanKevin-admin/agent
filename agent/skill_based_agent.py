"""
基于Skills架构的RPA Agent - 参考OpenClaw设计
"""
import os
import logging
from typing import List, Dict, Any
from datetime import datetime
from openai import OpenAI
from config.settings import config
from skills.skill_manager import SkillManager
from skills.feishu_skill import FeishuSkill
from skills.file_validation_skill import FileValidationSkill
from skills.database_skill import DatabaseSkill
from skills.notification_skill import NotificationSkill
from skills.report_skill import ReportSkill
from skills.config_skill import ConfigSkill

logger = logging.getLogger(__name__)


class SkillBasedAgent:
    """基于Skills的RPA Agent"""
    
    def __init__(self):
        self.client = OpenAI(
            api_key=config.ai.API_KEY,
            base_url=config.ai.API_BASE
        )
        self.model = config.ai.MODEL
        
        # 初始化Skill管理器
        self.skill_manager = SkillManager()
        self._register_skills()
        
        # 从MD文件加载系统提示词
        prompt_path = os.path.join(
            os.path.dirname(__file__), 
            '../prompts/system_prompt.md'
        )
        self.system_prompt_template = self.skill_manager.get_system_prompt(prompt_path)
        
        # 对话历史
        self.conversation_history: List[Dict] = []
        self.task_results: List[Dict] = []
    
    def _register_skills(self):
        """注册所有Skills"""
        self.skill_manager.register_skill(FeishuSkill())
        self.skill_manager.register_skill(FileValidationSkill())
        self.skill_manager.register_skill(DatabaseSkill())
        self.skill_manager.register_skill(NotificationSkill())
        self.skill_manager.register_skill(ReportSkill())
        self.skill_manager.register_skill(ConfigSkill())

        # 注册图灵测试Skill
        from skills.turing_test_skill import TuringTestSkill
        self.skill_manager.register_skill(TuringTestSkill())

        # 注册任务规划Skill
        from skills.task_planning_skill import TaskPlanningSkill
        self.skill_manager.register_skill(TaskPlanningSkill())

        # 注册定时任务管理Skill
        from skills.scheduled_task_skill import ScheduledTaskSkill
        self.skill_manager.register_skill(ScheduledTaskSkill())

        logger.info(f"[Agent] 已注册 {len(self.skill_manager.skills)} 个Skills")
    
    def run(self, user_input: str) -> str:
        """
        Agent主循环
        
        Args:
            user_input: 用户输入
            
        Returns:
            Agent最终回复
        """
        # 添加用户消息
        self.conversation_history.append({
            "role": "user",
            "content": user_input
        })
        
        # 构建系统提示词（注入当前日期）
        today = datetime.now().strftime("%Y-%m-%d")
        system_prompt = self.system_prompt_template.replace("{today}", today)
        
        # 准备消息历史（保留最近40条）
        history_window = self.conversation_history[-40:]
        messages = [
            {"role": "system", "content": system_prompt}
        ] + history_window
        
        # 获取所有工具定义
        tools = self.skill_manager.get_all_tools()
        
        max_iterations = 15
        
        for i in range(max_iterations):
            logger.info(f"[Agent] 第 {i+1} 轮思考...")
            
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=tools,
                    tool_choice="auto"
                )
            except Exception as e:
                error_msg = f"[Agent] 大模型调用失败: {e}"
                logger.error(error_msg)
                return error_msg
            
            message = response.choices[0].message
            
            # 如果没有工具调用，返回最终回复
            if not message.tool_calls:
                final_reply = message.content or "任务完成"
                self.conversation_history.append({
                    "role": "assistant",
                    "content": final_reply
                })
                return final_reply
            
            # 处理工具调用
            messages.append(message.model_dump())
            
            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                arguments = eval(tool_call.function.arguments)
                
                logger.info(f"[Agent] 调用工具: {tool_name}({arguments})")
                
                # 通过Skill管理器执行工具
                result = self.skill_manager.execute_tool(tool_name, arguments)
                
                # 添加工具结果到消息
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_name,
                    "content": str(result)
                })
                
                # 记录任务结果
                self.task_results.append({
                    "tool": tool_name,
                    "arguments": arguments,
                    "result": result
                })
        
        # 达到最大迭代次数
        final_msg = "任务执行完成（达到最大迭代次数）"
        self.conversation_history.append({
            "role": "assistant",
            "content": final_msg
        })
        return final_msg
    
    def get_task_results(self) -> List[Dict]:
        """获取任务执行结果"""
        return self.task_results
    
    def list_skills(self) -> List[Dict[str, Any]]:
        """列出所有Skills"""
        return self.skill_manager.list_skills()
    
    def enable_skill(self, skill_name: str):
        """启用Skill"""
        self.skill_manager.enable_skill(skill_name)
    
    def disable_skill(self, skill_name: str):
        """禁用Skill"""
        self.skill_manager.disable_skill(skill_name)
