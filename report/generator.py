"""报告生成模块 - 根据分析结果生成不同类型的报告文本"""
from models.schemas import DailyReport, TaskStatus


class ReportGenerator:
    """报告生成器 - 正常报告 / 异常报告"""

    def generate_group_message(self, report: DailyReport) -> str:
        """生成飞书群消息报告"""
        if report.has_error:
            return self._generate_error_report(report)
        else:
            return self._generate_normal_report(report)

    def generate_email_body(self, report: DailyReport) -> str:
        """生成邮件正文"""
        if report.has_error:
            return self._generate_error_email(report)
        else:
            return self._generate_normal_email(report)

    def _generate_normal_report(self, report: DailyReport) -> str:
        """正常运行 - 群消息报告"""
        lines = [
            "【RPA每日自动汇总报告】",
            f"📅 日期：{report.date}",
            f"今日运行总流程：{report.total_tasks}个",
            f"成功：{report.success_count} ｜ 失败：{report.fail_count}",
            "",
            "✅ 今日所有RPA流程运行正常，各项业务均已顺利执行完成。",
            "",
            "📁 本地结果文件核验：全部流程对应业务文件已正常生成、路径完整、文件存在。",
            "",
            "📧 今日运行日报已同步推送至业务负责人邮箱。"
        ]
        return "\n".join(lines)

    def _generate_error_report(self, report: DailyReport) -> str:
        """异常运行 - 群消息报告"""
        lines = [
            "【RPA运行异常汇总报告】",
            f"📅 日期：{report.date}",
            f"今日运行总流程：{report.total_tasks}个",
            f"成功：{report.success_count} ｜ 失败：{report.fail_count}",
            ""
        ]

        # 列出异常流程
        for task in report.error_tasks:
            lines.append(f"❌ 异常流程：{task.account}")
            lines.append(f"   报错原因：{task.error_message}")

        # 文件缺失信息
        if report.missing_files:
            lines.append("")
            lines.append("📁 本地结果文件核验：")
            for mf in report.missing_files:
                lines.append(f"   - {mf['account']} 的{mf['file_type']}缺失")
                lines.append(f"     路径：{mf['file_path']}")

        lines.append("")
        lines.append("📧 故障详细报告已推送至技术运维邮箱，请及时排查处理。")
        return "\n".join(lines)

    def _generate_normal_email(self, report: DailyReport) -> str:
        """正常运行 - 邮件正文（发给业务负责人）"""
        lines = [
            f"RPA每日运行日报 - {report.date}",
            "=" * 40,
            f"运行总流程：{report.total_tasks}个",
            f"全部成功：{report.success_count}个",
            "",
            "各流程执行详情：",
        ]
        for task in report.task_logs:
            lines.append(f"  • {task.account} - {task.login_status.value}")
            if task.query_range:
                lines.append(f"    查询范围：{task.query_range}")
            if task.query_result:
                lines.append(f"    查询结果：{task.query_result}")
            for fv in task.file_validations:
                status = "✓ 已生成" if fv.exists else "✗ 缺失"
                lines.append(f"    {fv.file_description}：{status}")

        lines.append("")
        lines.append("文件核验：全部通过")
        lines.append("=" * 40)
        return "\n".join(lines)

    def _generate_error_email(self, report: DailyReport) -> str:
        """异常运行 - 邮件正文（发给技术运维）"""
        lines = [
            f"⚠️ RPA故障排查报告 - {report.date}",
            "=" * 40,
            f"运行总流程：{report.total_tasks}个",
            f"成功：{report.success_count} | 失败：{report.fail_count}",
            "",
            "异常流程详细信息：",
        ]
        for task in report.error_tasks:
            lines.append(f"  ━━━━━━━━━━━━━━━━━━━━")
            lines.append(f"  账号：{task.account}")
            lines.append(f"  登录状态：{task.login_status.value}")
            if task.login_fail_reason:
                lines.append(f"  失败原因：{task.login_fail_reason}")
            lines.append(f"  错误信息：{task.error_message}")
            lines.append(f"  退出状态：{task.exit_status}")
            lines.append(f"  完整操作步骤：")
            for op in task.operations:
                lines.append(f"    > {op}")

        if report.missing_files:
            lines.append("")
            lines.append("缺失文件清单：")
            for mf in report.missing_files:
                lines.append(f"  • {mf['account']} - {mf['file_type']}")
                lines.append(f"    预期路径：{mf['file_path']}")

        lines.append("")
        lines.append("请及时排查处理。")
        return "\n".join(lines)
