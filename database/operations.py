"""
数据库操作封装
提供CRUD操作的便捷函数
"""
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from database.models import Conversation, ScheduledTask, TaskExecution
import json


# ==================== 对话记录 ====================

def save_conversation(db: Session, session_id: str, user_message: str, ai_response: str, 
                     query_params: dict = None, report_file: str = None) -> Conversation:
    """保存对话记录"""
    conv = Conversation(
        session_id=session_id,
        user_message=user_message,
        ai_response=ai_response,
        query_params=json.dumps(query_params, ensure_ascii=False) if query_params else None,
        report_file=report_file
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


def get_conversation_history(db: Session, session_id: str, limit: int = 50) -> List[Conversation]:
    """获取会话的对话历史"""
    return db.query(Conversation)\
        .filter(Conversation.session_id == session_id)\
        .order_by(Conversation.created_at.desc())\
        .limit(limit)\
        .all()


def get_all_sessions(db: Session, limit: int = 100) -> List[dict]:
    """获取所有会话列表（最新消息）"""
    # 使用子查询获取每个session的最新记录
    from sqlalchemy import func
    subquery = db.query(
        Conversation.session_id,
        func.max(Conversation.created_at).label('latest')
    ).group_by(Conversation.session_id).subquery()
    
    conversations = db.query(Conversation)\
        .join(subquery, 
              (Conversation.session_id == subquery.c.session_id) & 
              (Conversation.created_at == subquery.c.latest))\
        .order_by(Conversation.created_at.desc())\
        .limit(limit)\
        .all()
    
    return [conv.to_dict() for conv in conversations]


def clear_session(db: Session, session_id: str):
    """清空指定会话的历史记录"""
    db.query(Conversation).filter(Conversation.session_id == session_id).delete()
    db.commit()


# ==================== 定时任务 ====================

def create_task(db: Session, task_name: str, task_type: str, cron_expression: str,
                query_text: str = None, description: str = None, enabled: bool = True) -> ScheduledTask:
    """创建定时任务"""
    task = ScheduledTask(
        task_name=task_name,
        task_type=task_type,
        description=description,
        cron_expression=cron_expression,
        query_text=query_text,
        enabled=enabled
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def get_task(db: Session, task_id: int) -> Optional[ScheduledTask]:
    """获取单个任务"""
    return db.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()


def get_task_by_name(db: Session, task_name: str) -> Optional[ScheduledTask]:
    """根据名称获取任务"""
    return db.query(ScheduledTask).filter(ScheduledTask.task_name == task_name).first()


def get_all_tasks(db: Session, enabled_only: bool = False) -> List[ScheduledTask]:
    """获取所有任务"""
    query = db.query(ScheduledTask)
    if enabled_only:
        query = query.filter(ScheduledTask.enabled == True)
    return query.order_by(ScheduledTask.created_at.desc()).all()


def update_task(db: Session, task_id: int, **kwargs) -> Optional[ScheduledTask]:
    """更新任务"""
    task = get_task(db, task_id)
    if task:
        for key, value in kwargs.items():
            if hasattr(task, key):
                setattr(task, key, value)
        db.commit()
        db.refresh(task)
    return task


def delete_task(db: Session, task_id: int):
    """删除任务"""
    task = get_task(db, task_id)
    if task:
        db.delete(task)
        db.commit()


def update_task_run_time(db: Session, task_id: int, last_run: datetime, next_run: datetime = None):
    """更新任务运行时间"""
    task = get_task(db, task_id)
    if task:
        task.last_run_at = last_run
        if next_run:
            task.next_run_at = next_run
        db.commit()


# ==================== 任务执行记录 ====================

def create_execution(db: Session, task_id: int, status: str = 'running') -> TaskExecution:
    """创建任务执行记录"""
    execution = TaskExecution(
        task_id=task_id,
        status=status
    )
    db.add(execution)
    db.commit()
    db.refresh(execution)
    return execution


def update_execution(db: Session, execution_id: int, status: str, result: str = None) -> Optional[TaskExecution]:
    """更新执行记录"""
    execution = db.query(TaskExecution).filter(TaskExecution.id == execution_id).first()
    if execution:
        execution.status = status
        execution.result = result
        execution.completed_at = datetime.now()
        db.commit()
        db.refresh(execution)
    return execution


def get_task_executions(db: Session, task_id: int, limit: int = 50) -> List[TaskExecution]:
    """获取任务的执行历史"""
    return db.query(TaskExecution)\
        .filter(TaskExecution.task_id == task_id)\
        .order_by(TaskExecution.started_at.desc())\
        .limit(limit)\
        .all()
