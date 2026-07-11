"""
RPA模板管理器 - 加载、保存、列表、删除模板
"""
import os
import json
import sys
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class TemplateManager:
    """RPA模板管理器"""
    
    def __init__(self):
        """初始化模板管理器"""
        # 获取模板目录路径
        if getattr(sys, 'frozen', False):
            # 打包后
            base_dir = os.path.dirname(sys.executable)
        else:
            # 开发环境
            base_dir = os.path.dirname(os.path.dirname(__file__))
        
        self.templates_dir = os.path.join(base_dir, "rpa_templates")
        os.makedirs(self.templates_dir, exist_ok=True)
        
        logger.info(f"[TemplateManager] 模板目录: {self.templates_dir}")
    
    def load_template(self, template_id: str) -> Dict[str, Any]:
        """
        加载模板
        
        Args:
            template_id: 模板ID（文件名，不含.json）
            
        Returns:
            {"success": true/false, "template": {...}}
        """
        try:
            template_file = os.path.join(self.templates_dir, f"{template_id}.json")
            
            if not os.path.exists(template_file):
                return {
                    "success": False,
                    "message": f"❌ 模板'{template_id}'不存在"
                }
            
            with open(template_file, 'r', encoding='utf-8') as f:
                template = json.load(f)
            
            logger.info(f"[TemplateManager] 已加载模板: {template_id}")
            
            return {
                "success": True,
                "message": f"✅ 已加载模板'{template_id}'",
                "verified": True,
                "template": template
            }
            
        except Exception as e:
            logger.error(f"[TemplateManager] 加载模板失败: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"❌ 加载模板失败: {str(e)}",
                "error": str(e)
            }
    
    def save_template(self, template: Dict[str, Any]) -> Dict[str, Any]:
        """
        保存模板
        
        Args:
            template: 模板数据（必须包含template_id字段）
            
        Returns:
            {"success": true/false, "message": "结果"}
        """
        try:
            template_id = template.get("template_id")
            if not template_id:
                return {
                    "success": False,
                    "message": "❌ 模板缺少template_id字段"
                }
            
            # 验证必需字段
            required_fields = ["name", "type", "steps"]
            missing_fields = [f for f in required_fields if f not in template]
            if missing_fields:
                return {
                    "success": False,
                    "message": f"❌ 模板缺少必需字段: {', '.join(missing_fields)}"
                }
            
            # 保存文件
            template_file = os.path.join(self.templates_dir, f"{template_id}.json")
            with open(template_file, 'w', encoding='utf-8') as f:
                json.dump(template, f, ensure_ascii=False, indent=2)
            
            # 验证保存
            if not os.path.exists(template_file):
                return {
                    "success": False,
                    "message": "❌ 模板保存失败（文件未创建）",
                    "verified": False
                }
            
            file_size = os.path.getsize(template_file)
            
            logger.info(f"[TemplateManager] 已保存模板: {template_id} ({file_size} bytes)")
            
            return {
                "success": True,
                "message": f"✅ 模板'{template_id}'已保存",
                "verified": True,
                "template_file": template_file,
                "file_size": file_size
            }
            
        except Exception as e:
            logger.error(f"[TemplateManager] 保存模板失败: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"❌ 保存模板失败: {str(e)}",
                "verified": False,
                "error": str(e)
            }
    
    def list_templates(self) -> Dict[str, Any]:
        """
        列出所有模板
        
        Returns:
            {"success": true, "templates": [...]}
        """
        try:
            templates = []
            
            # 扫描模板目录
            if os.path.exists(self.templates_dir):
                for filename in os.listdir(self.templates_dir):
                    if filename.endswith('.json'):
                        template_id = filename[:-5]  # 去掉.json
                        template_file = os.path.join(self.templates_dir, filename)
                        
                        try:
                            with open(template_file, 'r', encoding='utf-8') as f:
                                template_data = json.load(f)
                            
                            templates.append({
                                "template_id": template_id,
                                "name": template_data.get("name", template_id),
                                "type": template_data.get("type", "unknown"),
                                "description": template_data.get("description", ""),
                                "steps_count": len(template_data.get("steps", []))
                            })
                        except Exception as e:
                            logger.warning(f"[TemplateManager] 跳过无效模板: {filename} ({e})")
            
            logger.info(f"[TemplateManager] 找到{len(templates)}个模板")

            return {
                "success": True,
                "message": f"✅ 找到{len(templates)}个模板",
                "templates": templates
            }

        except Exception as e:
            logger.error(f"[TemplateManager] 列出模板失败: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"❌ 列出模板失败: {str(e)}",
                "templates": [],
                "error": str(e)
            }

    def delete_template(self, template_id: str) -> Dict[str, Any]:
        """
        删除模板

        Args:
            template_id: 模板ID

        Returns:
            {"success": true/false, "message": "结果"}
        """
        try:
            template_file = os.path.join(self.templates_dir, f"{template_id}.json")

            # 验证文件存在
            if not os.path.exists(template_file):
                return {
                    "success": False,
                    "message": f"❌ 模板'{template_id}'不存在"
                }

            # 删除文件
            os.remove(template_file)

            # 验证删除
            if os.path.exists(template_file):
                return {
                    "success": False,
                    "message": f"❌ 模板'{template_id}'删除失败（文件仍存在）",
                    "verified": False
                }

            logger.info(f"[TemplateManager] 已删除模板: {template_id}")

            return {
                "success": True,
                "message": f"✅ 模板'{template_id}'已删除",
                "verified": True
            }

        except Exception as e:
            logger.error(f"[TemplateManager] 删除模板失败: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"❌ 删除模板失败: {str(e)}",
                "verified": False,
                "error": str(e)
            }
