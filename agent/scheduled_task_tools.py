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
    创建定时任务（带验证）

    Args:
        task_name: 任务名称
        task_type: 任务类型（analyze/report/sync/custom）
        cron_expression: Cron表达式
        query_text: 执行指令
        description: 任务描述（可选）

    Returns:
        {"success": true/false, "message": "结果", "task": {...}, "verified": true/false}
    """
    db = SessionLocal()
    try:
        # 步骤1: 检查任务名是否已存在
        existing = db_ops.get_task_by_name(db, task_name)
        if existing:
            return {
                "success": False,
                "message": f"❌ 任务名称'{task_name}'已存在，请换个名字",
                "verified": False
            }

        # 步骤2: 验证Cron表达式
        try:
            from apscheduler.triggers.cron import CronTrigger
            # 尝试创建trigger验证表达式
            parts = cron_expression.split()
            if len(parts) == 5:
                minute, hour, day, month, day_of_week = parts
                CronTrigger(
                    minute=minute,
                    hour=hour,
                    day=day,
                    month=month,
                    day_of_week=day_of_week
                )
            else:
                raise ValueError(f"Cron表达式格式错误，应为5个字段: {cron_expression}")
        except Exception as e:
            return {
                "success": False,
                "message": f"❌ Cron表达式无效: {str(e)}",
                "verified": False
            }

        # 步骤3: 创建任务到数据库
        task = db_ops.create_task(
            db=db,
            task_name=task_name,
            task_type=task_type,
            cron_expression=cron_expression,
            query_text=query_text,
            description=description,
            enabled=True
        )
        logger.info(f"[ScheduledTask] 数据库创建成功: {task_name} (ID: {task.id})")

        # 步骤4: 验证数据库写入
        verify_task = db_ops.get_task(db, task.id)
        if not verify_task:
            return {
                "success": False,
                "message": f"❌ 数据库写入验证失败",
                "verified": False
            }

        # 步骤5: 添加到调度器
        scheduler_added = False
        scheduler_error = None
        try:
            import sys
            if 'scheduler.task_scheduler' in sys.modules:
                scheduler_module = sys.modules['scheduler.task_scheduler']
                if hasattr(scheduler_module, 'task_scheduler') and scheduler_module.task_scheduler:
                    scheduler_module.task_scheduler.add_task(task)
                    scheduler_added = True
                    logger.info(f"[ScheduledTask] 调度器添加成功: {task_name}")
                else:
                    scheduler_error = "调度器未初始化"
            else:
                scheduler_error = "调度器模块未导入"
        except Exception as e:
            scheduler_error = str(e)
            logger.error(f"[ScheduledTask] 调度器添加失败: {e}", exc_info=True)

        # 步骤6: 验证调度器中的任务
        if scheduler_added:
            try:
                import sys
                scheduler_module = sys.modules['scheduler.task_scheduler']
                scheduler = scheduler_module.task_scheduler

                # 检查任务是否在调度器中
                job_id = f"task_{task.id}"
                job = scheduler.scheduler.get_job(job_id)

                if not job:
                    scheduler_added = False
                    scheduler_error = "任务未在调度器中找到"
                    logger.warning(f"[ScheduledTask] 验证失败: 任务{task_name}未在调度器中")
            except Exception as e:
                scheduler_added = False
                scheduler_error = f"验证失败: {str(e)}"

        # 步骤7: 返回结果（根据验证结果）
        if scheduler_added:
            return {
                "success": True,
                "message": f"✅ 定时任务'{task_name}'创建成功！\n"
                          f"📋 任务ID: {task.id}\n"
                          f"⏰ 执行计划: {cron_expression}\n"
                          f"🎯 任务类型: {task_type}\n"
                          f"✓ 已加入调度器，将按时执行",
                "verified": True,
                "task": {
                    "id": task.id,
                    "task_name": task.task_name,
                    "task_type": task.task_type,
                    "cron_expression": task.cron_expression,
                    "query_text": task.query_text,
                    "description": task.description,
                    "enabled": task.enabled,
                    "in_scheduler": True
                }
            }
        else:
            # 任务创建了但调度器添加失败
            return {
                "success": True,
                "message": f"⚠️ 定时任务'{task_name}'已保存到数据库，但未能添加到调度器\n"
                          f"📋 任务ID: {task.id}\n"
                          f"❌ 调度器错误: {scheduler_error}\n"
                          f"💡 建议：重启程序后任务会自动加载",
                "verified": False,
                "task": {
                    "id": task.id,
                    "task_name": task.task_name,
                    "task_type": task.task_type,
                    "cron_expression": task.cron_expression,
                    "query_text": task.query_text,
                    "description": task.description,
                    "enabled": task.enabled,
                    "in_scheduler": False,
                    "error": scheduler_error
                }
            }

    except Exception as e:
        logger.error(f"[ScheduledTask] 创建任务失败: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"❌ 创建失败: {str(e)}",
            "verified": False,
            "error": str(e)
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
    删除定时任务（带验证）

    Args:
        task_name: 任务名称

    Returns:
        {"success": true/false, "message": "结果", "verified": true/false}
    """
    db = SessionLocal()
    try:
        # 步骤1: 查找任务
        task = db_ops.get_task_by_name(db, task_name)
        if not task:
            return {
                "success": False,
                "message": f"❌ 找不到任务'{task_name}'",
                "verified": False
            }

        task_id = task.id
        logger.info(f"[ScheduledTask] 准备删除任务: {task_name} (ID: {task_id})")

        # 步骤2: 从调度器移除
        scheduler_removed = False
        try:
            import sys
            if 'scheduler.task_scheduler' in sys.modules:
                scheduler_module = sys.modules['scheduler.task_scheduler']
                if hasattr(scheduler_module, 'task_scheduler') and scheduler_module.task_scheduler:
                    scheduler_module.task_scheduler.remove_task(task_id)
                    scheduler_removed = True
                    logger.info(f"[ScheduledTask] 已从调度器移除: {task_name}")
        except Exception as e:
            logger.warning(f"[ScheduledTask] 从调度器移除失败: {e}")

        # 步骤3: 从数据库删除
        db_ops.delete_task(db, task_id)
        logger.info(f"[ScheduledTask] 数据库删除成功: {task_name}")

        # 步骤4: 验证数据库删除
        verify_task = db_ops.get_task(db, task_id)
        if verify_task:
            return {
                "success": False,
                "message": f"❌ 数据库删除验证失败：任务仍然存在",
                "verified": False
            }

        # 步骤5: 验证调度器移除（如果之前成功移除）
        if scheduler_removed:
            try:
                import sys
                scheduler_module = sys.modules['scheduler.task_scheduler']
                scheduler = scheduler_module.task_scheduler
                job_id = f"task_{task_id}"
                job = scheduler.scheduler.get_job(job_id)

                if job:
                    return {
                        "success": True,
                        "message": f"⚠️ 任务'{task_name}'已从数据库删除，但调度器验证失败\\n"\
                                  f"建议重启程序清理调度器",
                        "verified": False,
                        "db_deleted": True,
                        "scheduler_verified": False
                    }
            except Exception as e:
                logger.warning(f"[ScheduledTask] 调度器验证失败: {e}")

        # 步骤6: 返回成功结果
        return {
            "success": True,
            "message": f"✅ 定时任务'{task_name}'已完全删除！\\n"\
                      f"📋 任务ID: {task_id}\\n"\
                      f"✓ 数据库已删除\\n"\
                      f"{'✓ 调度器已移除' if scheduler_removed else '⚠️  调度器未移除（可能未运行）'}",
            "verified": True,
            "task_id": task_id,
            "db_deleted": True,
            "scheduler_removed": scheduler_removed
        }

    except Exception as e:
        logger.error(f"[ScheduledTask] 删除任务失败: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"❌ 删除失败: {str(e)}",
            "verified": False,
            "error": str(e)
        }
    finally:
        db.close()
