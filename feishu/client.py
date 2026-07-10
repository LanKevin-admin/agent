"""飞书API客户端 - Token管理"""
import time
import logging
import requests
from config.settings import config

logger = logging.getLogger(__name__)

# 请求超时时间（秒）
REQUEST_TIMEOUT = 30


class FeishuClient:
    """飞书开放平台API客户端"""

    def __init__(self):
        self.app_id = config.feishu.APP_ID
        self.app_secret = config.feishu.APP_SECRET
        self.base_url = config.feishu.BASE_URL
        self._tenant_access_token = None
        self._token_expire_time = 0

    @property
    def tenant_access_token(self) -> str:
        """获取tenant_access_token（自动续期）"""
        if time.time() >= self._token_expire_time:
            self._refresh_token()
        return self._tenant_access_token

    def _refresh_token(self):
        """刷新tenant_access_token，带重试"""
        url = f"{self.base_url}/auth/v3/tenant_access_token/internal"
        payload = {
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }

        for attempt in range(3):
            try:
                resp = requests.post(url, json=payload, timeout=REQUEST_TIMEOUT)
                data = resp.json()
                if data.get("code") == 0:
                    self._tenant_access_token = data["tenant_access_token"]
                    self._token_expire_time = time.time() + data.get("expire", 7200) - 300
                    return
                else:
                    logger.warning(f"获取Token失败(第{attempt+1}次): {data}")
            except requests.RequestException as e:
                logger.warning(f"获取Token网络异常(第{attempt+1}次): {e}")

            if attempt < 2:
                time.sleep(2 ** attempt)

        raise Exception("获取飞书Token失败，已重试3次")

    @property
    def headers(self) -> dict:
        """请求头（自动携带Token）"""
        return {
            "Authorization": f"Bearer {self.tenant_access_token}",
            "Content-Type": "application/json; charset=utf-8"
        }

    def get(self, endpoint: str, params: dict = None) -> dict:
        """GET请求"""
        url = f"{self.base_url}{endpoint}"
        try:
            resp = requests.get(url, headers=self.headers, params=params, timeout=REQUEST_TIMEOUT)
            return resp.json()
        except requests.RequestException as e:
            logger.error(f"GET请求失败 {endpoint}: {e}")
            return {"code": -1, "msg": str(e)}

    def post(self, endpoint: str, payload: dict = None) -> dict:
        """POST请求"""
        url = f"{self.base_url}{endpoint}"
        try:
            resp = requests.post(url, headers=self.headers, json=payload, timeout=REQUEST_TIMEOUT)
            return resp.json()
        except requests.RequestException as e:
            logger.error(f"POST请求失败 {endpoint}: {e}")
            return {"code": -1, "msg": str(e)}


# 全局单例
feishu_client = FeishuClient()
