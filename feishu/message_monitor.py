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

        # 会话上下文管理
        self.user_sessions = {}  # {user_id: {"last_mention_time": timestamp, "context": []}}
        self.session_timeout = 300  # 5分钟无交互则会话过期
        
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
            # 基本信息提取
            message_id = message.get("message_id", "")

            # sender可能是dict或str
            sender = message.get("sender", {})
            if isinstance(sender, dict):
                sender_id = sender.get("id", sender.get("sender_id", ""))
            else:
                sender_id = str(sender) if sender else ""

            chat_id = message.get("chat_id", "")
            create_time = message.get("create_time", "")
            msg_type = message.get("msg_type", "text")

            # body可能是dict或str
            body = message.get("body", {})
            if isinstance(body, str):
                try:
                    body = json.loads(body)
                except:
                    body = {}

            # mentions可能是list或str
            mentions = message.get("mentions", [])
            if isinstance(mentions, str):
                try:
                    mentions = json.loads(mentions)
                except:
                    mentions = []

            # 解析消息内容
            content_str = body.get("content", "{}")
            try:
                # content可能已经是dict，也可能是str
                if isinstance(content_str, str):
                    content_data = json.loads(content_str)
                else:
                    content_data = content_str if isinstance(content_str, dict) else {}
            except json.JSONDecodeError:
                content_data = {}

            # 提取文本内容
            text_content = ""
            if msg_type == "text":
                text_content = content_data.get("text", "")
            elif msg_type == "post":
                # 富文本消息
                post_content = content_data.get("content", {})
                if isinstance(post_content, dict):
                    zh_cn = post_content.get("zh_cn", {})
                    if isinstance(zh_cn, dict):
                        content_list = zh_cn.get("content", [])
                        if isinstance(content_list, list):
                            for item in content_list:
                                if isinstance(item, list):
                                    for sub_item in item:
                                        if isinstance(sub_item, dict) and sub_item.get("tag") == "text":
                                            text_content += sub_item.get("text", "")

            # 检查是否@了机器人
            is_mention_bot = False
            if self.bot_open_id and mentions and isinstance(mentions, list):
                for mention in mentions:
                    if not isinstance(mention, dict):
                        continue

                    # mention.id 可能是dict {"open_id": "xxx"} 或者直接是字符串 "ou_xxx"
                    mention_id = mention.get("id")

                    if isinstance(mention_id, dict):
                        # 字典格式：{"open_id": "xxx"}
                        if mention_id.get("open_id") == self.bot_open_id:
                            is_mention_bot = True
                            break
                    elif isinstance(mention_id, str):
                        # 字符串格式：直接比较
                        if mention_id == self.bot_open_id:
                            is_mention_bot = True
                            break

                    # 也可能直接在mention["user_id"]或mention["open_id"]
                    if mention.get("user_id") == self.bot_open_id or mention.get("open_id") == self.bot_open_id:
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
            logger.error(f"[MessageMonitor] 解析消息失败: {e}", exc_info=True)
            # 打印原始消息以便调试
            logger.debug(f"[MessageMonitor] 原始消息: {json.dumps(message, ensure_ascii=False, indent=2)}")
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
            新的@消息列表（包括@消息和同一用户的后续消息）
        """
        # 确保已获取机器人信息
        if not self.bot_open_id:
            self.get_bot_info()
            if not self.bot_open_id:
                return []

        # 获取最近1分钟的消息（因为10秒检查一次）
        messages = self.fetch_recent_messages(minutes=1)

        current_time = int(time.time())
        new_mentions = []

        for msg in messages:
            parsed = self.parse_message(msg)
            if not parsed:
                continue

            message_id = parsed["message_id"]
            sender_id = parsed["sender_id"]

            # 跳过已处理的消息
            if message_id in self.processed_message_ids:
                continue

            # 跳过机器人自己发的消息
            if sender_id == self.bot_open_id:
                self.processed_message_ids.add(message_id)
                continue

            # 情况1：直接@了机器人
            if parsed["is_mention_bot"] and parsed["content"]:
                new_mentions.append(parsed)
                self.processed_message_ids.add(message_id)

                # 更新用户会话
                self.user_sessions[sender_id] = {
                    "last_mention_time": current_time,
                    "context": []
                }
                logger.info(f"[MessageMonitor] 用户 {sender_id[:15]}... 发起新对话")

            # 情况2：同一用户在5分钟内的后续消息（没有@）
            elif sender_id in self.user_sessions:
                session = self.user_sessions[sender_id]
                time_diff = current_time - session["last_mention_time"]

                # 5分钟内的消息视为同一会话
                if time_diff <= self.session_timeout and parsed["content"]:
                    new_mentions.append(parsed)
                    self.processed_message_ids.add(message_id)
                    logger.info(f"[MessageMonitor] 用户 {sender_id[:15]}... 发送后续消息（距上次{time_diff}秒）")
                else:
                    # 会话已过期
                    if time_diff > self.session_timeout:
                        del self.user_sessions[sender_id]
                        logger.debug(f"[MessageMonitor] 用户 {sender_id[:15]}... 会话已过期")

        # 限制已处理消息记录大小
        if len(self.processed_message_ids) > self.max_history:
            # 保留最新的一半
            self.processed_message_ids = set(list(self.processed_message_ids)[-self.max_history//2:])

        if new_mentions:
            logger.info(f"[MessageMonitor] 发现 {len(new_mentions)} 条需要处理的消息")

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
