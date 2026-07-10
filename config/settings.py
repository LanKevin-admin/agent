"""飞书AI RPA监控系统 - 全局配置"""
import os
import sys
from dotenv import load_dotenv


def get_base_dir():
    """获取基础目录，兼容开发环境和EXE打包"""
    if getattr(sys, 'frozen', False):
        # EXE运行：使用EXE所在目录
        return os.path.dirname(sys.executable)
    else:
        # 开发环境：使用项目根目录（向上一级）
        return os.path.dirname(os.path.dirname(__file__))


# 加载环境变量，优先外部.env
base_dir = get_base_dir()
external_env = os.path.join(base_dir, '.env')
if os.path.exists(external_env):
    load_dotenv(external_env, override=True)
else:
    # 回退到打包内的.env
    load_dotenv()


class FeishuConfig:
    """飞书应用配置"""
    APP_ID = os.getenv("FEISHU_APP_ID", "")
    APP_SECRET = os.getenv("FEISHU_APP_SECRET", "")
    # 目标群的chat_id
    TARGET_CHAT_ID = os.getenv("FEISHU_CHAT_ID", "")
    # 飞书API基础地址
    BASE_URL = "https://open.feishu.cn/open-apis"


class EmailConfig:
    """邮件配置"""
    SMTP_HOST = os.getenv("SMTP_HOST", "smtp.163.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
    SMTP_USER = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    # 业务负责人邮箱（正常日报推送）
    BUSINESS_EMAILS = os.getenv("BUSINESS_EMAILS", "").split(",")
    # 技术运维邮箱（故障报告推送）
    TECH_EMAILS = os.getenv("TECH_EMAILS", "").split(",")


class AIConfig:
    """AI大模型配置"""
    API_KEY = os.getenv("AI_API_KEY", "")
    API_BASE = os.getenv("AI_API_BASE", "https://api.openai.com/v1")
    MODEL = os.getenv("AI_MODEL", "gpt-4o-mini")


class SchedulerConfig:
    """定时任务配置"""
    # 每日执行时间（24小时制），确保所有RPA已执行完毕
    DAILY_RUN_HOUR = int(os.getenv("DAILY_RUN_HOUR", "20"))
    DAILY_RUN_MINUTE = int(os.getenv("DAILY_RUN_MINUTE", "0"))


class WeComConfig:
    """企业微信配置"""
    WEBHOOK_URL = os.getenv("WECOM_WEBHOOK", "")


class ReportConfig:
    """汇报输出配置"""
    # 使用基础目录下的reports文件夹
    OUTPUT_DIR = os.path.join(get_base_dir(), "reports")


class AppConfig:
    """应用全局配置"""
    feishu = FeishuConfig()
    email = EmailConfig()
    ai = AIConfig()
    scheduler = SchedulerConfig()
    wecom = WeComConfig()
    report = ReportConfig()
    # 日志标识前缀（用于精准匹配RPA日志消息）
    RPA_LOG_MARKERS = ["登录成功", "登录失败", "查询成功", "退出成功", "退出失败",
                       "流水查询范围", "余额查询", "保存路径"]


config = AppConfig()
