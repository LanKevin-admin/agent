"""
飞书消息监听器 - 定期检测@消息并自动回复
"""
import time
import json
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from feishu.client import feishu_client
from config.settings import config

logger = logging.getLogger(__name__)


class FeishuMessageMonitor:
    """飞书消息监听器"""
    
    def __init__(self):
        self.chat_id = config.feishu.TARGET_CHAT_ID
        self.bot_open_id = None  # 机器人的open_id
        self.last_check_time = None  # 上次检查时间
        self.processed_message_ids = set()  # 已处理的消息ID
        self.max_history = 1000  # 最多记录1000条已处理消息
        
    def get_bot_info(self) -> Optional[str]:
        """获取机器人信息（open_id）"""
        if self.bot_open_id:
            return self.bot_open_id
            
        try:
            resp = feishu_client.get("/bot/v3/info")
            if resp.get("code") == 0:
                bot_data = resp.get("bot", {})
                self.bot_open_id = bot_data.get("open_id")
                logger.info(f"[MessageMonitor] 获取机器人信息成功: {self.bot_open_id}")
                return self.bot_open_id
            else:
                logger.error(f"[MessageMonitor] 获取机器人信息失败: {resp}")
                return None
        except Exception as e:
            logger.error(f"[MessageMonitor] 获取机器人信息异常: {e}")
            return None
    
    def fetch_recent_messages(self, minutes: int = 1) -> List[Dict]:
        """
        获取最近N分钟的群消息
        
        Args:
            minutes: 获取最近多少分钟的消息
            
        Returns:
            消息列表
        """
        if not self.chat_id:
            logger.warning("[MessageMonitor] 未配置飞书群聊ID")
            return []
        
        # 计算时间范围
        end_time = int(time.time())
        start_time = int((datetime.now() - timedelta(minutes=minutes)).timestamp())
        
        messages = []
        page_token = ""
        has_more = True
        
        try:
            while has_more:
                params = {
                    "container_id_type": "chat",
                    "container_id": self.chat_id,
                    "start_time": str(start_time),
                    "end_time": str(end_time),
                    "sort_type": "ByCreateTimeDesc",  # 倒序，最新的在前
                    "page_size": 20,
                }
                if page_token:
                    params["page_token"] = page_token
                
                resp = feishu_client.get("/im/v1/messages", params=params)
                
                if resp.get("code") != 0:
                    logger.error(f"[MessageMonitor] 获取消息失败: {resp}")
                    break
                
                data = resp.get("data", {})
                items = data.get("items", [])
                messages.extend(items)
                
                has_more = data.get("has_more", False)
                page_token = data.get("page_token", "")
                
        except Exception as e:
            logger.error(f"[MessageMonitor] 获取消息异常: {e}")
        
        return messages
    
    def parse_message(self, message: Dict) -> Optional[Dict]:
        """
        解析消息，提取关键信息
        
        Args:
            message: 原始消息数据
            
        Returns:
            解析后的消息信息，包含：
            - message_id: 消息ID
            - sender_id: 发送者ID
            - chat_id: 群聊ID
            - create_time: 创建时间
            - message_type: 消息类型
            - content: 消息内容
            - mentions: @的用户列表
            - is_mention_bot: 是否@了机器人
        """
        try:
            message_id = message.get("message_id")
            sender = message.get("sender", {})
            sender_id = sender.get("id")
            chat_id = message.get("chat_id")
            create_time = message.get("create_time")
            msg_type = message.get("msg_type")
            body = message.get("body", {})
            mentions = message.get("mentions", [])
            
            # 解析消息内容
            content_str = body.get("content", "{}")
            try:
                content_data = json.loads(content_str)
            except json.JSONDecodeError:
                content_data = {}
            
            # 提取文本内容
            text_content = ""
            if msg_type == "text":
                text_content = content_data.get("text", "")
            elif msg_type == "post":
                # 富文本消息
                post_content = content_data.get("content", {})
                # 简单提取第一段文本
                zh_cn = post_content.get("zh_cn", {})
                content_list = zh_cn.get("content", [])
                if content_list:
                    for item in content_list:
                        if isinstance(item, list):
                            for sub_item in item:
                                if isinstance(sub_item, dict) and sub_item.get("tag") == "text":
                                    text_content += sub_item.get("text", "")
            
            # 检查是否@了机器人
            is_mention_bot = False
            if self.bot_open_id:
                for mention in mentions:
                    if mention.get("id", {}).get("open_id") == self.bot_open_id:
                        is_mention_bot = True
                        break
            
            return {
                "message_id": message_id,
                "sender_id": sender_id,
                "chat_id": chat_id,
                "create_time": create_time,
                "message_type": msg_type,
                "content": text_content.strip(),
                "mentions": mentions,
                "is_mention_bot": is_mention_bot
            }
        except Exception as e:
            logger.error(f"[MessageMonitor] 解析消息失败: {e}")
            return None
    
    def reply_message(self, message_id: str, reply_text: str) -> bool:
        """
        回复消息
        
        Args:
            message_id: 要回复的消息ID
            reply_text: 回复内容
            
        Returns:
            是否回复成功
        """
        try:
            payload = {
                "content": json.dumps({"text": reply_text}),
                "msg_type": "text"
            }
            
            resp = feishu_client.post(
                f"/im/v1/messages/{message_id}/reply",
                payload=payload
            )
            
            if resp.get("code") == 0:
                logger.info(f"[MessageMonitor] 回复消息成功: {message_id}")
                return True
            else:
                logger.error(f"[MessageMonitor] 回复消息失败: {resp}")
                return False
        except Exception as e:
            logger.error(f"[MessageMonitor] 回复消息异常: {e}")
            return False
    
    def check_new_mentions(self) -> List[Dict]:
        """
        检查新的@消息
        
        Returns:
            新的@消息列表
        """
        # 确保已获取机器人信息
        if not self.bot_open_id:
            self.get_bot_info()
            if not self.bot_open_id:
                return []
        
        # 获取最近1分钟的消息（因为10秒检查一次）
        messages = self.fetch_recent_messages(minutes=1)
        
        new_mentions = []
        for msg in messages:
            parsed = self.parse_message(msg)
            if not parsed:
                continue
            
            message_id = parsed["message_id"]
            
            # 跳过已处理的消息
            if message_id in self.processed_message_ids:
                continue
            
            # 跳过机器人自己发的消息
            if parsed["sender_id"] == self.bot_open_id:
                self.processed_message_ids.add(message_id)
                continue
            
            # 只处理@了机器人的消息
            if parsed["is_mention_bot"] and parsed["content"]:
                new_mentions.append(parsed)
                self.processed_message_ids.add(message_id)
        
        # 限制已处理消息记录大小
        if len(self.processed_message_ids) > self.max_history:
            # 保留最新的一半
            self.processed_message_ids = set(list(self.processed_message_ids)[-self.max_history//2:])
        
        if new_mentions:
            logger.info(f"[MessageMonitor] 发现 {len(new_mentions)} 条新@消息")
        
        return new_mentions
    
    def clean_mention_text(self, text: str) -> str:
        """
        清理@标记，提取实际内容
        
        Args:
            text: 原始文本，如 "@机器人 帮我分析日志"
            
        Returns:
            清理后的文本："帮我分析日志"
        """
        # 移除@标记 (格式: @_user_1 或 @机器人名称)
        import re
        text = re.sub(r'@[^\s]+\s*', '', text)
        return text.strip()


# 全局单例
message_monitor = FeishuMessageMonitor()
