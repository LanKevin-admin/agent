"""
定时任务调度器 - 使用APScheduler实现真正的定时执行
"""
import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from database.models import SessionLocal
from database import operations as db_ops

logger = logging.getLogger(__name__)


class TaskScheduler:
    """定时任务调度器"""

    def __init__(self, agent):
        """
        初始化调度器

        Args:
            agent: RPA Agent实例，用于执行任务
        """
        self.agent = agent
        self.scheduler = BackgroundScheduler(timezone='Asia/Shanghai')
        self.scheduler.start()
        logger.info("[TaskScheduler] 调度器已启动")

    def load_tasks_from_db(self):
        """从数据库加载所有启用的任务并注册到调度器"""
        db = SessionLocal()
        try:
            tasks = db_ops.get_all_tasks(db, enabled_only=True)

            for task in tasks:
                try:
                    self._register_task(task)
                    logger.info(f"[TaskScheduler] 已加载任务: {task.task_name} ({task.cron_expression})")
                except Exception as e:
                    logger.error(f"[TaskScheduler] 加载任务失败 {task.task_name}: {e}")

            logger.info(f"[TaskScheduler] 已加载 {len(tasks)} 个定时任务")

        finally:
            db.close()

    def _register_task(self, task):
        """注册单个任务到调度器"""
        # 解析Cron表达式
        cron_parts = task.cron_expression.split()
        if len(cron_parts) != 5:
            raise ValueError(f"无效的Cron表达式: {task.cron_expression}")

        # 创建Cron触发器
        trigger = CronTrigger(
            minute=cron_parts[0],
            hour=cron_parts[1],
            day=cron_parts[2],
            month=cron_parts[3],
            day_of_week=cron_parts[4],
            timezone='Asia/Shanghai'
        )

        # 添加任务到调度器
        self.scheduler.add_job(
            func=self._execute_task,
            trigger=trigger,
            args=[task.id, task.task_name, task.query_text],
            id=f"task_{task.id}",
            name=task.task_name,
            replace_existing=True
        )

    def _execute_task(self, task_id: int, task_name: str, query_text: str):
        """执行单个定时任务"""
        logger.info(f"[TaskScheduler] 开始执行任务: {task_name}")

        db = SessionLocal()
        execution_id = None

        try:
            # 创建执行记录
            execution = db_ops.create_execution(db, task_id, status='running')
            execution_id = execution.id

            # 更新任务的上次运行时间
            db_ops.update_task_run_time(db, task_id, last_run=datetime.now())

            # 调用Agent执行任务
            result = self.agent.run(query_text)

            # 更新执行记录为成功
            db_ops.update_execution(db, execution_id, status='success', result=result[:500])  # 限制长度

            logger.info(f"[TaskScheduler] 任务执行成功: {task_name}")

        except Exception as e:
            logger.error(f"[TaskScheduler] 任务执行失败 {task_name}: {e}")

            # 更新执行记录为失败
            if execution_id:
                db_ops.update_execution(db, execution_id, status='failed', result=str(e))

        finally:
            db.close()

    def add_task(self, task):
        """动态添加新任务到调度器"""
        try:
            self._register_task(task)
            logger.info(f"[TaskScheduler] 动态添加任务: {task.task_name}")
        except Exception as e:
            logger.error(f"[TaskScheduler] 添加任务失败 {task.task_name}: {e}")
            raise

    def remove_task(self, task_id: int):
        """从调度器移除任务"""
        try:
            job_id = f"task_{task_id}"
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
                logger.info(f"[TaskScheduler] 移除任务: {job_id}")
        except Exception as e:
            logger.error(f"[TaskScheduler] 移除任务失败 {task_id}: {e}")

    def update_task(self, task):
        """更新调度器中的任务"""
        self.remove_task(task.id)
        if task.enabled:
            self.add_task(task)

    def get_all_jobs(self):
        """获取所有调度中的任务"""
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'name': job.name,
                'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None
            })
        return jobs

    def shutdown(self):
        """关闭调度器"""
        self.scheduler.shutdown()
        logger.info("[TaskScheduler] 调度器已关闭")


# 全局调度器实例
task_scheduler: TaskScheduler = None


def init_scheduler(agent):
    """初始化全局调度器"""
    global task_scheduler
    task_scheduler = TaskScheduler(agent)
    task_scheduler.load_tasks_from_db()
    return task_scheduler

