"""
飞书消息监听后台任务
定期检测群消息中的@消息并自动回复
"""
import logging
import threading
import time
from feishu.message_monitor import message_monitor

logger = logging.getLogger(__name__)


class MessageMonitorTask:
    """消息监听后台任务"""
    
    def __init__(self, agent, interval: int = 10):
        """
        初始化消息监听任务
        
        Args:
            agent: RPA Agent实例，用于处理用户消息
            interval: 检查间隔（秒），默认10秒
        """
        self.agent = agent
        self.interval = interval
        self.running = False
        self.thread = None
        
    def start(self):
        """启动监听任务"""
        if self.running:
            logger.warning("[MessageMonitorTask] 监听任务已在运行")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        logger.info(f"[MessageMonitorTask] 消息监听任务已启动，间隔{self.interval}秒")
    
    def stop(self):
        """停止监听任务"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("[MessageMonitorTask] 消息监听任务已停止")
    
    def _run(self):
        """后台循环任务"""
        logger.info("[MessageMonitorTask] 开始监听飞书群消息...")
        
        while self.running:
            try:
                self._check_and_reply()
            except Exception as e:
                logger.error(f"[MessageMonitorTask] 检查消息异常: {e}", exc_info=True)
            
            # 休眠指定时间
            time.sleep(self.interval)
    
    def _check_and_reply(self):
        """检查新消息并回复"""
        # 检查新的@消息
        new_mentions = message_monitor.check_new_mentions()
        
        if not new_mentions:
            return
        
        logger.info(f"[MessageMonitorTask] 发现 {len(new_mentions)} 条新@消息")
        
        for mention in new_mentions:
            try:
                self._handle_mention(mention)
            except Exception as e:
                logger.error(f"[MessageMonitorTask] 处理消息失败: {e}", exc_info=True)
    
    def _handle_mention(self, mention: dict):
        """
        处理单条@消息
        
        Args:
            mention: 消息信息
        """
        message_id = mention["message_id"]
        content = mention["content"]
        sender_id = mention["sender_id"]
        
        # 清理@标记
        user_query = message_monitor.clean_mention_text(content)
        
        if not user_query:
            logger.warning(f"[MessageMonitorTask] 消息内容为空: {message_id}")
            return
        
        logger.info(f"[MessageMonitorTask] 处理用户消息: {user_query[:50]}...")
        
        try:
            # 使用Agent处理用户消息
            ai_response = self.agent.run(user_query)
            
            # 回复消息
            if ai_response:
                # 限制回复长度（飞书消息有长度限制）
                max_length = 4000
                if len(ai_response) > max_length:
                    ai_response = ai_response[:max_length] + "\n\n... (内容过长，已截断)"
                
                success = message_monitor.reply_message(message_id, ai_response)
                
                if success:
                    logger.info(f"[MessageMonitorTask] 已回复消息: {message_id}")
                else:
                    logger.error(f"[MessageMonitorTask] 回复消息失败: {message_id}")
            else:
                logger.warning(f"[MessageMonitorTask] AI未返回回复内容")
                
        except Exception as e:
            logger.error(f"[MessageMonitorTask] 处理消息失败: {e}", exc_info=True)
            # 回复错误提示
            error_msg = f"抱歉，处理你的消息时出现错误：{str(e)}"
            message_monitor.reply_message(message_id, error_msg)


# 全局监听任务实例（延迟初始化）
monitor_task: MessageMonitorTask = None


def start_message_monitor(agent, interval: int = 10):
    """
    启动消息监听任务
    
    Args:
        agent: RPA Agent实例
        interval: 检查间隔（秒）
    """
    global monitor_task
    
    if monitor_task is None:
        monitor_task = MessageMonitorTask(agent, interval)
    
    monitor_task.start()
    return monitor_task


def stop_message_monitor():
    """停止消息监听任务"""
    global monitor_task
    
    if monitor_task:
        monitor_task.stop()
