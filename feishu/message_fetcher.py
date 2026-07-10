"""飞书群消息拉取模块"""
import time
from datetime import datetime, timedelta
from typing import List
from feishu.client import feishu_client
from config.settings import config


class MessageFetcher:
    """群消息拉取器 - 批量获取当日群聊消息"""

    def __init__(self):
        self.chat_id = config.feishu.TARGET_CHAT_ID

    def fetch_today_messages(self) -> List[dict]:
        """拉取当日所有群消息"""
        # 今日0点时间戳
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        start_time = str(int(today_start.timestamp()))
        end_time = str(int(time.time()))

        messages = []
        page_token = ""
        has_more = True

        while has_more:
            params = {
                "container_id_type": "chat",
                "container_id": self.chat_id,
                "start_time": start_time,
                "end_time": end_time,
                "sort_type": "ByCreateTimeAsc",
                "page_size": 50,
            }
            if page_token:
                params["page_token"] = page_token

            resp = feishu_client.get("/im/v1/messages", params=params)

            if resp.get("code") != 0:
                print(f"[MessageFetcher] 拉取消息失败: {resp}")
                break

            data = resp.get("data", {})
            items = data.get("items", [])
            messages.extend(items)

            has_more = data.get("has_more", False)
            page_token = data.get("page_token", "")

        print(f"[MessageFetcher] 今日共拉取 {len(messages)} 条消息")
        return messages

    def extract_text_content(self, messages: List[dict]) -> List[str]:
        """提取纯文本消息内容"""
        text_messages = []
        for msg in messages:
            msg_type = msg.get("msg_type", "")
            if msg_type == "text":
                import json
                body = msg.get("body", {})
                content = body.get("content", "{}")
                try:
                    text = json.loads(content).get("text", "")
                    if text.strip():
                        text_messages.append(text.strip())
                except json.JSONDecodeError:
                    continue
        return text_messages
