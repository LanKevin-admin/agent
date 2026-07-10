"""邮件分发模块 - 差异化推送邮件"""
import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from typing import List, Optional
from config.settings import config
from models.schemas import DailyReport

logger = logging.getLogger(__name__)


class EmailSender:
    """
    智能邮件分发器
    - 正常运行：发送日报给业务负责人
    - 存在故障：发送故障报告给技术运维
    """

    def __init__(self):
        self.smtp_host = config.email.SMTP_HOST
        self.smtp_port = config.email.SMTP_PORT
        self.smtp_user = config.email.SMTP_USER
        self.smtp_password = config.email.SMTP_PASSWORD

    def _send(self, subject: str, body: str, recipients: List[str], attachment_path: Optional[str] = None) -> bool:
        """底层发送，所有发送操作都走这里"""
        recipients = [r.strip() for r in recipients if r.strip()]
        if not recipients:
            logger.warning("[EmailSender] 无有效收件人，跳过发送")
            return False

        try:
            msg = MIMEMultipart()
            msg['From'] = self.smtp_user
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain', 'utf-8'))

            # 如果有附件，添加附件
            if attachment_path and os.path.exists(attachment_path):
                with open(attachment_path, 'rb') as f:
                    attachment = MIMEApplication(f.read())
                    filename = os.path.basename(attachment_path)
                    attachment.add_header('Content-Disposition', 'attachment', filename=filename)
                    msg.attach(attachment)
                    logger.info(f"[EmailSender] 已添加附件: {filename}")

            with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, timeout=30) as server:
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.smtp_user, recipients, msg.as_string())

            logger.info(f"[EmailSender] 邮件发送成功 -> {recipients}")
            return True

        except smtplib.SMTPAuthenticationError:
            logger.error("[EmailSender] 邮件认证失败，请检查账号密码或授权码")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"[EmailSender] SMTP错误: {e}")
            return False
        except Exception as e:
            logger.error(f"[EmailSender] 发送异常: {e}")
            return False

    def send_direct(self, subject: str, body: str, recipients: List[str], attachment_path: Optional[str] = None) -> bool:
        """Agent工具直接调用：指定收件人发送"""
        return self._send(subject, body, recipients, attachment_path)

    def send_report(self, report: DailyReport, subject: str, body: str, recipients: List[str]) -> bool:
        """带report上下文的发送（pipeline模式兼容保留）"""
        return self._send(subject, body, recipients)

    def dispatch(self, report: DailyReport, email_body: str):
        """
        智能分发：
        - 无报错 → 发给业务负责人
        - 有报错 → 仅发给技术运维
        """
        if report.has_error:
            subject = f"⚠️ RPA故障排查报告 - {report.date}"
            recipients = config.email.TECH_EMAILS
        else:
            subject = f"RPA每日运行日报 - {report.date}"
            recipients = config.email.BUSINESS_EMAILS

        self._send(subject, email_body, recipients)
