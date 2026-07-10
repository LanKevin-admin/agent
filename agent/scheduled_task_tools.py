"""
定时任务管理工具函数
通过对话创建、查看、删除定时任务
"""
import logging
from typing import Dict, Any
from database.models import SessionLocal
from database import operations as db_ops

logger = logging.getLogger(__name__)


def tool_create_scheduled_task(
    task_name: str,
    task_type: str,
    cron_expression: str,
    query_text: str,
    description: str = None
) -> Dict[str, Any]:
    """
    创建定时任务
    
    Args:
        task_name: 任务名称
        task_type: 任务类型（analyze/report/sync/custom）
        cron_expression: Cron表达式
        query_text: 执行指令
        description: 任务描述（可选）
        
    Returns:
        {"success": true/false, "message": "结果", "task": {...}}
    """
    db = SessionLocal()
    try:
        # 检查任务名是否已存在
        existing = db_ops.get_task_by_name(db, task_name)
        if existing:
            return {
                "success": False,
                "message": f"任务名称'{task_name}'已存在，请换个名字"
            }
        
        # 创建任务
        task = db_ops.create_task(
            db=db,
            task_name=task_name,
            task_type=task_type,
            cron_expression=cron_expression,
            query_text=query_text,
            description=description,
            enabled=True
        )

        logger.info(f"[ScheduledTask] 创建定时任务: {task_name}")

        # 同步到调度器
        try:
            from scheduler.task_scheduler import task_scheduler
            if task_scheduler:
                task_scheduler.add_task(task)
                logger.info(f"[ScheduledTask] 任务已添加到调度器: {task_name}")
        except Exception as e:
            logger.warning(f"[ScheduledTask] 添加到调度器失败: {e}")

        return {
            "success": True,
            "message": f"定时任务'{task_name}'已创建",
            "task": {
                "id": task.id,
                "task_name": task.task_name,
                "task_type": task.task_type,
                "cron_expression": task.cron_expression,
                "query_text": task.query_text,
                "enabled": task.enabled
            }
        }
        
    except Exception as e:
        logger.error(f"[ScheduledTask] 创建任务失败: {e}")
        return {
            "success": False,
            "message": f"创建任务失败: {str(e)}"
        }
    finally:
        db.close()


def tool_list_scheduled_tasks() -> Dict[str, Any]:
    """
    列出所有定时任务
    
    Returns:
        {"success": true, "tasks": [...]}
    """
    db = SessionLocal()
    try:
        tasks = db_ops.get_all_tasks(db)
        
        task_list = []
        for task in tasks:
            task_list.append({
                "id": task.id,
                "task_name": task.task_name,
                "task_type": task.task_type,
                "cron_expression": task.cron_expression,
                "query_text": task.query_text,
                "description": task.description,
                "enabled": task.enabled,
                "last_run_at": task.last_run_at.isoformat() if task.last_run_at else None,
                "next_run_at": task.next_run_at.isoformat() if task.next_run_at else None
            })
        
        return {
            "success": True,
            "tasks": task_list,
            "count": len(task_list)
        }
        
    except Exception as e:
        logger.error(f"[ScheduledTask] 列出任务失败: {e}")
        return {
            "success": False,
            "message": f"列出任务失败: {str(e)}",
            "tasks": []
        }
    finally:
        db.close()


def tool_delete_scheduled_task(task_name: str) -> Dict[str, Any]:
    """
    删除定时任务
    
    Args:
        task_name: 任务名称
        
    Returns:
        {"success": true/false, "message": "结果"}
    """
    db = SessionLocal()
    try:
        # 查找任务
        task = db_ops.get_task_by_name(db, task_name)
        if not task:
            return {
                "success": False,
                "message": f"找不到任务'{task_name}'"
            }
        
        # 删除任务
        db_ops.delete_task(db, task.id)
        
        logger.info(f"[ScheduledTask] 删除定时任务: {task_name}")
        
        return {
            "success": True,
            "message": f"定时任务'{task_name}'已删除"
        }
        
    except Exception as e:
        logger.error(f"[ScheduledTask] 删除任务失败: {e}")
        return {
            "success": False,
            "message": f"删除任务失败: {str(e)}"
        }
    finally:
        db.close()
