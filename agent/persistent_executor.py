"""
任务持续执行系统 - 让Agent持续工作直到任务完成
参考AutoGPT的持续执行模式
"""
import json
import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"           # 待执行
    IN_PROGRESS = "in_progress"   # 执行中
    COMPLETED = "completed"       # 已完成
    FAILED = "failed"             # 失败
    BLOCKED = "blocked"           # 阻塞（等待条件）


class Task:
    """任务对象"""
    
    def __init__(self, task_id: str, description: str, parent_id: str = None):
        self.task_id = task_id
        self.description = description
        self.parent_id = parent_id
        self.status = TaskStatus.PENDING
        self.result = None
        self.error = None
        self.subtasks: List['Task'] = []
        self.created_at = datetime.now()
        self.started_at = None
        self.completed_at = None
        self.retry_count = 0
        self.max_retries = 3
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "description": self.description,
            "parent_id": self.parent_id,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "subtasks": [t.to_dict() for t in self.subtasks],
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "retry_count": self.retry_count
        }


class PersistentExecutor:
    """持续执行器"""
    
    def __init__(self, agent, max_iterations: int = 100, save_interval: int = 5):
        """
        Args:
            agent: SkillBasedAgent实例
            max_iterations: 最大迭代次数（防止无限循环）
            save_interval: 每执行N次保存一次进度
        """
        self.agent = agent
        self.max_iterations = max_iterations
        self.save_interval = save_interval
        
        self.main_task: Optional[Task] = None
        self.task_queue: List[Task] = []
        self.completed_tasks: List[Task] = []
        self.iteration_count = 0
        
        self.checkpoint_file = "task_checkpoint.json"
    
    def execute_task(self, task_description: str) -> Dict[str, Any]:
        """
        持续执行任务，直到完成
        
        Args:
            task_description: 任务描述
            
        Returns:
            {
                "status": "completed|failed|max_iterations",
                "main_task": {...},
                "completed_tasks": [...],
                "iterations": 100,
                "total_time": 123.45
            }
        """
        logger.info(f"[PersistentExecutor] 开始执行任务: {task_description}")
        
        # 创建主任务
        self.main_task = Task("main", task_description)
        self.task_queue.append(self.main_task)
        
        start_time = time.time()
        
        # 主循环
        while self.iteration_count < self.max_iterations:
            self.iteration_count += 1
            
            logger.info(f"[PersistentExecutor] 第 {self.iteration_count} 次迭代")
            
            # 检查是否完成
            if self._is_completed():
                logger.info(f"[PersistentExecutor] 任务完成！")
                return self._generate_result("completed", start_time)
            
            # 执行下一个任务
            if not self._execute_next_task():
                # 没有可执行的任务了，但还没完成
                logger.warning(f"[PersistentExecutor] 任务队列为空但未完成，可能阻塞")
                return self._generate_result("blocked", start_time)
            
            # 定期保存进度
            if self.iteration_count % self.save_interval == 0:
                self._save_checkpoint()
        
        # 达到最大迭代次数
        logger.warning(f"[PersistentExecutor] 达到最大迭代次数 {self.max_iterations}")
        return self._generate_result("max_iterations", start_time)
    
    def _execute_next_task(self) -> bool:
        """执行下一个任务"""
        if not self.task_queue:
            return False
        
        # 获取队列中第一个待执行的任务
        current_task = None
        for task in self.task_queue:
            if task.status == TaskStatus.PENDING:
                current_task = task
                break
        
        if not current_task:
            return False
        
        # 标记为执行中
        current_task.status = TaskStatus.IN_PROGRESS
        current_task.started_at = datetime.now()
        
        logger.info(f"[PersistentExecutor] 执行任务: {current_task.description}")
        
        try:
            # 构建Agent提示
            prompt = self._build_agent_prompt(current_task)
            
            # 调用Agent执行
            response = self.agent.run(prompt)
            
            # 解析响应
            self._process_agent_response(current_task, response)
            
            return True
            
        except Exception as e:
            logger.error(f"[PersistentExecutor] 任务执行失败: {e}")
            current_task.error = str(e)
            current_task.retry_count += 1
            
            if current_task.retry_count >= current_task.max_retries:
                current_task.status = TaskStatus.FAILED
                current_task.completed_at = datetime.now()
            else:
                current_task.status = TaskStatus.PENDING
                logger.info(f"[PersistentExecutor] 任务重试 {current_task.retry_count}/{current_task.max_retries}")
            
            return True
    
    def _build_agent_prompt(self, task: Task) -> str:
        """构建Agent提示词"""
        prompt = f"""
当前任务：{task.description}

**重要提示**：
1. 如果这是一个复杂任务，请先分解为多个子任务
2. 每完成一个步骤，明确告诉我"已完成：XXX"
3. 如果发现无法完成，说明原因和需要什么条件
4. 如果需要人类输入，明确说明需要什么信息

**任务上下文**：
- 主任务：{self.main_task.description}
- 当前进度：已完成 {len(self.completed_tasks)} 个子任务
- 待处理：{len([t for t in self.task_queue if t.status == TaskStatus.PENDING])} 个任务

请执行这个任务。
"""
        return prompt
    
    def _process_agent_response(self, task: Task, response: str):
        """处理Agent响应"""
        # 简单的关键词识别
        if "已完成" in response or "搞定" in response or "OK了" in response:
            task.status = TaskStatus.COMPLETED
            task.result = response
            task.completed_at = datetime.now()
            self.completed_tasks.append(task)
            logger.info(f"[PersistentExecutor] 任务完成: {task.description}")
        
        elif "分解为" in response or "子任务" in response or "步骤" in response:
            # Agent建议分解任务
            logger.info(f"[PersistentExecutor] 任务需要分解")
            # 这里可以进一步解析子任务（简化版：标记为完成，让Agent继续）
            task.status = TaskStatus.COMPLETED
            task.result = response
            task.completed_at = datetime.now()
            self.completed_tasks.append(task)
        
        elif "无法完成" in response or "需要" in response or "阻塞" in response:
            task.status = TaskStatus.BLOCKED
            task.result = response
            logger.warning(f"[PersistentExecutor] 任务阻塞: {response}")
        
        else:
            # 继续执行
            task.status = TaskStatus.PENDING
            logger.info(f"[PersistentExecutor] 任务继续...")
    
    def _is_completed(self) -> bool:
        """检查是否完成"""
        # 主任务完成
        if self.main_task.status == TaskStatus.COMPLETED:
            return True
        
        # 所有任务都完成或失败
        pending_tasks = [t for t in self.task_queue if t.status == TaskStatus.PENDING]
        in_progress_tasks = [t for t in self.task_queue if t.status == TaskStatus.IN_PROGRESS]
        
        return len(pending_tasks) == 0 and len(in_progress_tasks) == 0
    
    def _generate_result(self, status: str, start_time: float) -> Dict[str, Any]:
        """生成结果"""
        total_time = time.time() - start_time
        
        return {
            "status": status,
            "main_task": self.main_task.to_dict() if self.main_task else None,
            "completed_tasks": [t.to_dict() for t in self.completed_tasks],
            "pending_tasks": [t.to_dict() for t in self.task_queue if t.status == TaskStatus.PENDING],
            "failed_tasks": [t.to_dict() for t in self.task_queue if t.status == TaskStatus.FAILED],
            "iterations": self.iteration_count,
            "total_time": round(total_time, 2)
        }
    
    def _save_checkpoint(self):
        """保存检查点"""
        try:
            checkpoint = {
                "main_task": self.main_task.to_dict() if self.main_task else None,
                "task_queue": [t.to_dict() for t in self.task_queue],
                "completed_tasks": [t.to_dict() for t in self.completed_tasks],
                "iteration_count": self.iteration_count,
                "timestamp": datetime.now().isoformat()
            }
            
            with open(self.checkpoint_file, 'w', encoding='utf-8') as f:
                json.dump(checkpoint, f, ensure_ascii=False, indent=2)
            
            logger.info(f"[PersistentExecutor] 进度已保存")
        except Exception as e:
            logger.error(f"[PersistentExecutor] 保存进度失败: {e}")
    
    def load_checkpoint(self) -> bool:
        """加载检查点，恢复任务"""
        try:
            with open(self.checkpoint_file, 'r', encoding='utf-8') as f:
                checkpoint = json.load(f)
            
            # 恢复任务（简化版）
            self.iteration_count = checkpoint.get('iteration_count', 0)
            logger.info(f"[PersistentExecutor] 从检查点恢复，迭代次数: {self.iteration_count}")
            return True
        except FileNotFoundError:
            logger.info(f"[PersistentExecutor] 没有找到检查点文件")
            return False
        except Exception as e:
            logger.error(f"[PersistentExecutor] 加载检查点失败: {e}")
            return False
