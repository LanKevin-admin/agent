"""
数据库模型定义
使用SQLAlchemy + SQLite实现持久化存储
"""
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import os
import sys

# 数据库路径（支持EXE打包）
def get_data_dir():
    """获取数据目录，兼容开发环境和EXE打包"""
    if getattr(sys, 'frozen', False):
        # EXE运行：使用EXE所在目录
        base_dir = os.path.dirname(sys.executable)
    else:
        # 开发环境：使用项目根目录
        base_dir = os.path.dirname(os.path.dirname(__file__))

    data_dir = os.path.join(base_dir, 'data')
    os.makedirs(data_dir, exist_ok=True)
    return data_dir

DB_DIR = get_data_dir()
DB_PATH = os.path.join(DB_DIR, 'rpa_monitor.db')

# 创建数据库引擎
engine = create_engine(f'sqlite:///{DB_PATH}', echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Conversation(Base):
    """对话记录表"""
    __tablename__ = 'conversations'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(100), index=True, comment='会话ID（用于区分不同对话）')
    user_message = Column(Text, nullable=False, comment='用户消息')
    ai_response = Column(Text, nullable=False, comment='AI回复')
    query_params = Column(Text, comment='查询参数（JSON格式）')
    report_file = Column(String(255), comment='生成的报告文件名')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    
    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'user_message': self.user_message,
            'ai_response': self.ai_response,
            'query_params': self.query_params,
            'report_file': self.report_file,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class ScheduledTask(Base):
    """定时任务表"""
    __tablename__ = 'scheduled_tasks'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_name = Column(String(100), unique=True, nullable=False, comment='任务名称')
    task_type = Column(String(50), nullable=False, comment='任务类型：analyze/report/sync等')
    description = Column(Text, comment='任务描述')
    cron_expression = Column(String(100), nullable=False, comment='Cron表达式')
    query_text = Column(Text, comment='查询指令（传给Agent）')
    enabled = Column(Boolean, default=True, comment='是否启用')
    last_run_at = Column(DateTime, comment='上次运行时间')
    next_run_at = Column(DateTime, comment='下次运行时间')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    # 关联任务执行记录
    executions = relationship("TaskExecution", back_populates="task", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            'id': self.id,
            'task_name': self.task_name,
            'task_type': self.task_type,
            'description': self.description,
            'cron_expression': self.cron_expression,
            'query_text': self.query_text,
            'enabled': self.enabled,
            'last_run_at': self.last_run_at.isoformat() if self.last_run_at else None,
            'next_run_at': self.next_run_at.isoformat() if self.next_run_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class TaskExecution(Base):
    """任务执行记录表"""
    __tablename__ = 'task_executions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey('scheduled_tasks.id'), nullable=False, comment='关联的任务ID')
    status = Column(String(20), nullable=False, comment='执行状态：running/success/failed')
    result = Column(Text, comment='执行结果或错误信息')
    started_at = Column(DateTime, default=datetime.now, comment='开始时间')
    completed_at = Column(DateTime, comment='完成时间')
    
    # 关联任务
    task = relationship("ScheduledTask", back_populates="executions")
    
    def to_dict(self):
        return {
            'id': self.id,
            'task_id': self.task_id,
            'task_name': self.task.task_name if self.task else None,
            'status': self.status,
            'result': self.result,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'duration': (self.completed_at - self.started_at).total_seconds() if self.completed_at and self.started_at else None
        }


def init_db():
    """初始化数据库（创建所有表）"""
    Base.metadata.create_all(bind=engine)
    print(f"✅ 数据库已初始化: {DB_PATH}")


def get_db():
    """获取数据库会话（用于FastAPI依赖注入）"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


if __name__ == '__main__':
    # 直接运行此文件可初始化数据库
    init_db()
    print("数据库表结构：")
    print("- conversations: 对话记录")
    print("- scheduled_tasks: 定时任务")
    print("- task_executions: 任务执行记录")
