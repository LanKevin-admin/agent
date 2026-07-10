"""飞书群消息推送模块"""
import json
import logging
from feishu.client import feishu_client
from config.settings import config

logger = logging.getLogger(__name__)


class MessageSender:
    """群消息推送器"""

    def __init__(self):
        self.chat_id = config.feishu.TARGET_CHAT_ID

    def send_text(self, content: str) -> bool:
        """发送纯文本消息到目标群"""
        # 使用json.dumps确保内容安全序列化
        content_json = json.dumps({"text": content}, ensure_ascii=False)
        payload = {
            "receive_id": self.chat_id,
            "msg_type": "text",
            "content": content_json
        }
        resp = feishu_client.post(
            "/im/v1/messages?receive_id_type=chat_id",
            payload=payload
        )
        success = resp.get("code") == 0
        if not success:
            logger.error(f"[MessageSender] 发送失败: {resp}")
        return success

    def send_report(self, report_text: str) -> bool:
        """发送报告（富文本格式）"""
        content = {
            "zh_cn": {
                "title": "",
                "content": [[{"tag": "text", "text": report_text}]]
            }
        }
        payload = {
            "receive_id": self.chat_id,
            "msg_type": "post",
            "content": json.dumps(content, ensure_ascii=False)
        }
        resp = feishu_client.post(
            "/im/v1/messages?receive_id_type=chat_id",
            payload=payload
        )
        success = resp.get("code") == 0
        if not success:
            logger.error(f"[MessageSender] 发送报告失败: {resp}")
        return success
