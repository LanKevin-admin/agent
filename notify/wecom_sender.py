"""
企业微信群机器人消息推送
支持Markdown格式的消息推送到企业微信群
"""
import requests
import logging
from typing import Dict, Any
from config.settings import config

logger = logging.getLogger(__name__)


class WeComSender:
    """企业微信群机器人消息发送器"""
    
    def __init__(self):
        self.webhook_url = config.wecom.WEBHOOK_URL
        
    def send_markdown(self, content: str) -> bool:
        """
        发送Markdown格式消息到企业微信群
        
        Args:
            content: Markdown格式的消息内容
            
        Returns:
            bool: 发送成功返回True，失败返回False
        """
        if not self.webhook_url:
            logger.warning("[WeComSender] 企业微信Webhook未配置，跳过推送")
            return False
        
        payload = {
            "msgtype": "markdown",
            "markdown": {
                "content": content
            }
        }
        
        try:
            resp = requests.post(
                self.webhook_url, 
                json=payload, 
                timeout=10
            )
            resp_data = resp.json()
            
            if resp_data.get("errcode") == 0:
                logger.info("[WeComSender] 企业微信消息推送成功")
                return True
            else:
                logger.error(f"[WeComSender] 企业微信消息推送失败: {resp_data.get('errmsg')}")
                return False
                
        except Exception as e:
            logger.error(f"[WeComSender] 企业微信推送异常: {e}")
            return False
    
    def send_text(self, content: str) -> bool:
        """
        发送纯文本消息到企业微信群
        
        Args:
            content: 文本消息内容
            
        Returns:
            bool: 发送成功返回True，失败返回False
        """
        if not self.webhook_url:
            logger.warning("[WeComSender] 企业微信Webhook未配置，跳过推送")
            return False
        
        payload = {
            "msgtype": "text",
            "text": {
                "content": content
            }
        }
        
        try:
            resp = requests.post(
                self.webhook_url, 
                json=payload, 
                timeout=10
            )
            resp_data = resp.json()
            
            if resp_data.get("errcode") == 0:
                logger.info("[WeComSender] 企业微信消息推送成功")
                return True
            else:
                logger.error(f"[WeComSender] 企业微信消息推送失败: {resp_data.get('errmsg')}")
                return False
                
        except Exception as e:
            logger.error(f"[WeComSender] 企业微信推送异常: {e}")
            return False


# 全局单例
wecom_sender = WeComSender()
