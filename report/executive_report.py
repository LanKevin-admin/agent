"""
领导级汇报生成器
面向管理层的简洁、突出重点的RPA运行汇报
"""
import os
import logging
from datetime import datetime
from typing import Dict, List, Any
from collections import Counter
from config.settings import config

logger = logging.getLogger(__name__)


class ExecutiveReportGenerator:
    """领导级汇报生成器"""
    
    def __init__(self):
        self.output_dir = config.report.OUTPUT_DIR
        os.makedirs(self.output_dir, exist_ok=True)
    
    def generate_executive_summary(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成领导级汇报内容
        
        Args:
            analysis_result: Agent分析的原始结果
            
        Returns:
            包含summary(摘要文本), detail_file(失败详情文件路径), stats(统计数据)
        """
        # 提取关键统计数据
        total_count = analysis_result.get("total_count", 0)
        success_count = analysis_result.get("success_count", 0)
        failed_count = analysis_result.get("failed_count", 0)
        failed_items = analysis_result.get("failed_items", [])
        
        # 计算成功率
        success_rate = (success_count / total_count * 100) if total_count > 0 else 0
        
        # 分析失败原因
        failure_reasons = self._analyze_failure_reasons(failed_items)
        top_failure_reason = failure_reasons[0] if failure_reasons else ("无", 0)
        
        # 生成失败详情文件
        detail_file_path = None
        if failed_items:
            detail_file_path = self._generate_failure_detail_file(failed_items)
        
        # 生成领导级摘要文本
        summary = self._format_executive_summary(
            total_count, success_count, failed_count, 
            success_rate, top_failure_reason, detail_file_path
        )
        
        return {
            "summary": summary,
            "detail_file": detail_file_path,
            "stats": {
                "total": total_count,
                "success": success_count,
                "failed": failed_count,
                "success_rate": round(success_rate, 2),
                "top_failure": top_failure_reason[0],
                "top_failure_count": top_failure_reason[1]
            }
        }
    
    def _analyze_failure_reasons(self, failed_items: List[Dict]) -> List[tuple]:
        """
        分析失败原因，统计最常见的故障类型
        
        Returns:
            [(原因, 次数), ...] 按次数降序排列
        """
        reasons = []
        
        for item in failed_items:
            reason = item.get("failure_reason", "未知原因")
            
            # 归类常见故障
            if "文件不存在" in reason or "文件缺失" in reason:
                reasons.append("文件缺失")
            elif "日期不匹配" in reason or "日期范围" in reason:
                reasons.append("文件日期错误")
            elif "登录失败" in reason:
                reasons.append("登录异常")
            elif "查询失败" in reason:
                reasons.append("查询异常")
            elif "超时" in reason:
                reasons.append("系统超时")
            elif "密码错误" in reason:
                reasons.append("密码错误")
            else:
                reasons.append(reason)
        
        # 统计并排序
        reason_counts = Counter(reasons)
        return reason_counts.most_common()
    
    def _generate_failure_detail_file(self, failed_items: List[Dict]) -> str:
        """
        生成失败详情TXT文件
        
        Returns:
            文件路径
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"RPA失败详情_{timestamp}.txt"
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("=" * 60 + "\n")
            f.write(f"  RPA运行失败详情汇总\n")
            f.write(f"  生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 60 + "\n\n")
            
            for idx, item in enumerate(failed_items, 1):
                f.write(f"【失败 {idx}】 {item.get('account', '未知账号')}\n")
                f.write(f"{'─' * 50}\n")
                f.write(f"失败原因：{item.get('failure_reason', '未知')}\n")
                f.write(f"登录状态：{item.get('login_status', '未知')}\n")
                f.write(f"查询范围：{item.get('query_range', '未指定')}\n")
                f.write(f"文件路径：{item.get('file_path', '无')}\n")
                f.write(f"文件状态：{item.get('file_status', '未检查')}\n")
                
                if item.get('error_message'):
                    f.write(f"错误详情：{item['error_message']}\n")
                
                f.write("\n")
            
            f.write("=" * 60 + "\n")
            f.write(f"总计失败：{len(failed_items)} 个任务\n")
            f.write("=" * 60 + "\n")
        
        logger.info(f"[ExecutiveReport] 失败详情文件已生成：{filepath}")
        return filepath
    
    def _format_executive_summary(
        self,
        total: int,
        success: int,
        failed: int,
        success_rate: float,
        top_failure: tuple,
        detail_file: str
    ) -> str:
        """格式化简洁汇总文本（Markdown格式）"""

        date_str = datetime.now().strftime("%Y年%m月%d日")

        # 根据成功率选择状态标识
        if success_rate >= 95:
            status_icon = "✅"
        elif success_rate >= 80:
            status_icon = "⚠️"
        else:
            status_icon = "❌"

        summary = f"""# {status_icon} RPA运行汇总 - {date_str}

**总运行数：** {total}  |  **成功：** {success}  |  **失败：** {failed}  |  **成功率：** {success_rate:.1f}%

"""

        if failed == 0:
            summary += "✅ 所有任务正常运行"
        else:
            summary += f"❌ {failed}个任务失败，主要原因：{top_failure[0]}（{top_failure[1]}次）"

            if detail_file:
                filename = os.path.basename(detail_file)
                summary += f"\n\n📎 详细信息见附件：`{filename}`"

        return summary


# 全局单例
executive_report_generator = ExecutiveReportGenerator()
