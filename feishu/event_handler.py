"""
飞书事件处理器 - 实时接收飞书推送的消息事件
替代轮询模式，实现零延迟响应
"""
import json
import logging
import hashlib
import hmac
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class FeishuEventHandler:
    """飞书事件处理器"""
    
    def __init__(self, encrypt_key: Optional[str] = None, verification_token: Optional[str] = None):
        """
        初始化事件处理器
        
        Args:
            encrypt_key: 事件加密密钥（飞书开放平台获取）
            verification_token: 验证令牌（飞书开放平台获取）
        """
        self.encrypt_key = encrypt_key
        self.verification_token = verification_token
        
    def verify_signature(self, timestamp: str, nonce: str, encrypt_str: str, signature: str) -> bool:
        """
        验证飞书请求签名
        
        Args:
            timestamp: 时间戳
            nonce: 随机数
            encrypt_str: 加密字符串
            signature: 签名
            
        Returns:
            是否验证通过
        """
        if not self.encrypt_key:
            logger.warning("[EventHandler] 未配置加密密钥，跳过签名验证")
            return True
        
        # 拼接字符串
        str_to_sign = f"{timestamp}{nonce}{encrypt_str}{self.encrypt_key}"
        
        # 计算签名
        calculated_signature = hashlib.sha256(str_to_sign.encode()).hexdigest()
        
        return calculated_signature == signature
    
    def handle_url_verification(self, data: Dict) -> Dict:
        """
        处理URL验证请求（飞书配置Webhook时的验证）
        
        Args:
            data: 请求数据
            
        Returns:
            验证响应
        """
        challenge = data.get("challenge", "")
        token = data.get("token", "")
        
        # 验证token
        if self.verification_token and token != self.verification_token:
            logger.error(f"[EventHandler] Token验证失败: {token}")
            return {"error": "invalid token"}
        
        logger.info(f"[EventHandler] URL验证成功: {challenge}")
        return {"challenge": challenge}
    
    def parse_message_event(self, event: Dict) -> Optional[Dict]:
        """
        解析消息事件
        
        Args:
            event: 事件数据
            
        Returns:
            解析后的消息信息
        """
        try:
            # 提取消息信息
            message = event.get("message", {})
            sender = event.get("sender", {})
            
            message_id = message.get("message_id", "")
            chat_id = message.get("chat_id", "")
            message_type = message.get("message_type", "text")
            
            # 发送者信息
            sender_id = sender.get("sender_id", {}).get("open_id", "")
            
            # 消息内容
            content_str = message.get("content", "{}")
            try:
                content = json.loads(content_str) if isinstance(content_str, str) else content_str
            except:
                content = {}
            
            # 提取文本
            text = content.get("text", "")
            
            # @信息
            mentions = message.get("mentions", [])
            
            return {
                "message_id": message_id,
                "chat_id": chat_id,
                "message_type": message_type,
                "sender_id": sender_id,
                "content": text,
                "mentions": mentions,
                "raw_event": event
            }
            
        except Exception as e:
            logger.error(f"[EventHandler] 解析消息事件失败: {e}", exc_info=True)
            return None
    
    def is_mention_bot(self, parsed_message: Dict, bot_open_id: str) -> bool:
        """
        判断消息是否@了机器人
        
        Args:
            parsed_message: 解析后的消息
            bot_open_id: 机器人的open_id
            
        Returns:
            是否@了机器人
        """
        mentions = parsed_message.get("mentions", [])
        
        for mention in mentions:
            if not isinstance(mention, dict):
                continue
            
            # 检查多种可能的字段
            mention_id = mention.get("id", {})
            if isinstance(mention_id, dict):
                if mention_id.get("open_id") == bot_open_id:
                    return True
            elif isinstance(mention_id, str):
                if mention_id == bot_open_id:
                    return True
            
            # 也检查直接字段
            if mention.get("user_id") == bot_open_id or mention.get("open_id") == bot_open_id:
                return True
        
        return False


# 全局单例
event_handler = FeishuEventHandler()
