"""
任务规划Skill - 让Agent能够分解复杂任务并持续执行
"""
import logging
from typing import Dict, Any, List
from skills.base_skill import BaseSkill

logger = logging.getLogger(__name__)


class TaskPlanningSkill(BaseSkill):
    """任务规划与执行Skill"""
    
    def get_name(self) -> str:
        return "task_planning"
    
    def get_description(self) -> str:
        return "任务规划：分解复杂任务为子任务，持续执行直到完成"
    
    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "create_task_plan",
                    "description": "创建任务计划，将复杂任务分解为多个子任务",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "task_description": {
                                "type": "string",
                                "description": "任务描述"
                            },
                            "subtasks": {
                                "type": "array",
                                "description": "子任务列表",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "id": {"type": "string"},
                                        "description": {"type": "string"},
                                        "dependencies": {
                                            "type": "array",
                                            "items": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        },
                        "required": ["task_description", "subtasks"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "mark_task_completed",
                    "description": "标记任务为已完成",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "task_id": {
                                "type": "string",
                                "description": "任务ID"
                            },
                            "result": {
                                "type": "string",
                                "description": "任务结果"
                            }
                        },
                        "required": ["task_id", "result"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "check_task_status",
                    "description": "检查任务执行状态",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "request_human_input",
                    "description": "请求人类输入（当任务无法自动完成时）",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "question": {
                                "type": "string",
                                "description": "需要询问的问题"
                            },
                            "reason": {
                                "type": "string",
                                "description": "为什么需要人类输入"
                            }
                        },
                        "required": ["question", "reason"]
                    }
                }
            }
        ]
    
    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        try:
            if tool_name == "create_task_plan":
                return self._create_task_plan(**arguments)
            elif tool_name == "mark_task_completed":
                return self._mark_task_completed(**arguments)
            elif tool_name == "check_task_status":
                return self._check_task_status()
            elif tool_name == "request_human_input":
                return self._request_human_input(**arguments)
            else:
                return {"error": f"未知工具: {tool_name}"}
        except Exception as e:
            logger.error(f"[TaskPlanningSkill] 执行{tool_name}失败: {e}")
            return {"error": str(e)}
    
    def _create_task_plan(self, task_description: str, subtasks: List[Dict]) -> Dict[str, Any]:
        """创建任务计划"""
        logger.info(f"[TaskPlanning] 创建任务计划: {task_description}")
        logger.info(f"[TaskPlanning] 子任务数量: {len(subtasks)}")
        
        # 存储任务计划（简化版：内存存储）
        if not hasattr(self, 'task_plans'):
            self.task_plans = {}
        
        plan_id = f"plan_{len(self.task_plans) + 1}"
        self.task_plans[plan_id] = {
            "description": task_description,
            "subtasks": subtasks,
            "status": "in_progress",
            "completed_subtasks": []
        }
        
        return {
            "success": True,
            "plan_id": plan_id,
            "subtasks_count": len(subtasks),
            "message": f"任务计划已创建，共{len(subtasks)}个子任务"
        }
    
    def _mark_task_completed(self, task_id: str, result: str) -> Dict[str, Any]:
        """标记任务完成"""
        logger.info(f"[TaskPlanning] 标记任务完成: {task_id}")
        
        if not hasattr(self, 'task_plans'):
            return {"success": False, "error": "没有任务计划"}
        
        # 找到对应的任务计划并标记完成（简化版）
        for plan_id, plan in self.task_plans.items():
            for subtask in plan['subtasks']:
                if subtask['id'] == task_id:
                    plan['completed_subtasks'].append(task_id)
                    
                    # 检查是否全部完成
                    all_completed = len(plan['completed_subtasks']) == len(plan['subtasks'])
                    if all_completed:
                        plan['status'] = 'completed'
                    
                    return {
                        "success": True,
                        "task_id": task_id,
                        "result": result,
                        "all_completed": all_completed,
                        "progress": f"{len(plan['completed_subtasks'])}/{len(plan['subtasks'])}"
                    }
        
        return {"success": False, "error": f"未找到任务: {task_id}"}
    
    def _check_task_status(self) -> Dict[str, Any]:
        """检查任务状态"""
        if not hasattr(self, 'task_plans') or not self.task_plans:
            return {
                "has_tasks": False,
                "message": "当前没有任务"
            }
        
        # 返回当前任务状态
        current_plan = list(self.task_plans.values())[-1]  # 最新的任务计划
        
        total = len(current_plan['subtasks'])
        completed = len(current_plan['completed_subtasks'])
        pending = total - completed
        
        return {
            "has_tasks": True,
            "status": current_plan['status'],
            "total_subtasks": total,
            "completed_subtasks": completed,
            "pending_subtasks": pending,
            "progress_percentage": round(completed / total * 100, 1) if total > 0 else 0,
            "message": f"进度: {completed}/{total} 已完成"
        }
    
    def _request_human_input(self, question: str, reason: str) -> Dict[str, Any]:
        """请求人类输入"""
        logger.info(f"[TaskPlanning] 请求人类输入: {question}")
        
        return {
            "requires_human_input": True,
            "question": question,
            "reason": reason,
            "message": f"需要人类输入：{question}\n原因：{reason}"
        }
