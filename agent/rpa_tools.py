"""
RPA自动化工具 - AI调用RPA执行自动化任务
"""
import asyncio
import logging
from typing import Dict, Any, List

from ..rpa import (
    RPAExecutor,
    BrowserManager,
    DesktopAutomation,
    TemplateManager,
    BrowserRecorder
)

logger = logging.getLogger(__name__)

# 全局管理器实例
browser_manager = BrowserManager()
template_manager = TemplateManager()
desktop_auto = DesktopAutomation()


def tool_list_rpa_templates() -> Dict[str, Any]:
    """
    列出所有RPA模板
    
    Returns:
        {
            "success": true/false,
            "templates": [
                {
                    "template_id": "feishu_login",
                    "name": "飞书登录",
                    "type": "browser",
                    "description": "...",
                    "steps_count": 5
                }
            ]
        }
    """
    try:
        result = template_manager.list_templates()
        
        if result["success"]:
            templates = result.get("templates", [])
            logger.info(f"[RPATools] 找到{len(templates)}个模板")
            
            # 格式化返回给AI
            template_list = "\n".join([
                f"• {t['template_id']} - {t['name']} ({t['type']}, {t['steps_count']}步)"
                for t in templates
            ])
            
            return {
                "success": True,
                "message": f"✅ 找到{len(templates)}个RPA模板:\n{template_list}",
                "templates": templates
            }
        else:
            return result
            
    except Exception as e:
        logger.error(f"[RPATools] 列出模板失败: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"❌ 列出模板失败: {str(e)}",
            "error": str(e)
        }


def tool_run_rpa_template(template_id: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    执行RPA模板
    
    Args:
        template_id: 模板ID（如 feishu_login）
        parameters: 参数字典（如 {"username": "xxx", "password": "***"}）
        
    Returns:
        {
            "success": true/false,
            "message": "执行结果",
            "verified": true/false,
            "execution_log": [...]
        }
    """
    try:
        # 1. 加载模板
        load_result = template_manager.load_template(template_id)
        if not load_result["success"]:
            return load_result
        
        template = load_result["template"]
        template_type = template.get("type", "browser")
        
        logger.info(f"[RPATools] 开始执行模板: {template_id} (类型: {template_type})")
        
        # 2. 根据类型执行
        if template_type == "browser":
            # 浏览器自动化
            result = asyncio.run(_execute_browser_template(template, parameters or {}))
        elif template_type == "desktop":
            # 桌面自动化
            result = _execute_desktop_template(template, parameters or {})
        else:
            return {
                "success": False,
                "message": f"❌ 不支持的模板类型: {template_type}"
            }
        
        return result
        
    except Exception as e:
        logger.error(f"[RPATools] 执行模板失败: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"❌ 执行模板失败: {str(e)}",
            "verified": False,
            "error": str(e)
        }


async def _execute_browser_template(template: Dict, parameters: Dict) -> Dict:
    """执行浏览器模板"""
    try:
        # 启动浏览器
        headless = template.get("headless", True)
        start_result = await browser_manager.start(headless=headless)
        
        if not start_result["success"]:
            return start_result
        
        # 创建执行器
        page = browser_manager.get_page()
        executor = RPAExecutor(page)
        
        # 执行模板
        result = await executor.execute_template(template, parameters)
        
        # 保存会话（如果需要）
        if template.get("save_session") and result["success"]:
            session_name = template.get("session_name", template["template_id"])
            await browser_manager.save_cookies(session_name)
        
        # 关闭浏览器（可选）
        if template.get("auto_close", False):
            await browser_manager.stop()
        
        return result
        
    except Exception as e:
        logger.error(f"[RPATools] 浏览器模板执行失败: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"❌ 浏览器执行失败: {str(e)}",
            "verified": False,
            "error": str(e)
        }


def _execute_desktop_template(template: Dict, parameters: Dict) -> Dict:
    """执行桌面模板"""
    try:
        # 桌面自动化执行逻辑
        # 这里简化实现，实际应该根据模板步骤执行
        app_path = template.get("app_path")

        if app_path:
            # 启动应用
            result = desktop_auto.start_application(app_path)
            if not result["success"]:
                return result
        else:
            # 连接已运行的应用
            connect_params = template.get("connect_params", {})
            result = desktop_auto.connect_application(**connect_params)
            if not result["success"]:
                return result

        # 执行步骤
        execution_log = []
        for step in template.get("steps", []):
            action = step.get("action")

            if action == "click":
                result = desktop_auto.click_element(**step.get("params", {}))
            elif action == "input":
                result = desktop_auto.input_text(**step.get("params", {}))
            elif action == "get_text":
                result = desktop_auto.get_text(**step.get("params", {}))
            else:
                result = {"success": False, "message": f"未知动作: {action}"}

            execution_log.append({
                "step": step,
                "result": result
            })

            if not result["success"]:
                return {
                    "success": False,
                    "message": f"❌ 步骤执行失败: {step.get('description', action)}",
                    "execution_log": execution_log
                }

        return {
            "success": True,
            "message": f"✅ 桌面模板执行成功！完成{len(execution_log)}个步骤",
            "verified": True,
            "execution_log": execution_log
        }

    except Exception as e:
        logger.error(f"[RPATools] 桌面模板执行失败: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"❌ 桌面执行失败: {str(e)}",
            "verified": False,
            "error": str(e)
        }


def tool_record_rpa_template(template_name: str, template_type: str = "browser") -> Dict[str, Any]:
    """
    开始录制RPA模板

    Args:
        template_name: 模板名称
        template_type: 模板类型（browser/desktop）

    Returns:
        {
            "success": true/false,
            "message": "录制说明",
            "recording_id": "..."
        }
    """
    try:
        if template_type == "browser":
            # 浏览器录制
            result = asyncio.run(_start_browser_recording(template_name))
        elif template_type == "desktop":
            # 桌面录制（暂未实现）
            return {
                "success": False,
                "message": "❌ 桌面录制功能暂未实现，请使用浏览器录制"
            }
        else:
            return {
                "success": False,
                "message": f"❌ 不支持的录制类型: {template_type}"
            }

        return result

    except Exception as e:
        logger.error(f"[RPATools] 开始录制失败: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"❌ 开始录制失败: {str(e)}",
            "error": str(e)
        }


async def _start_browser_recording(template_name: str) -> Dict:
    """开始浏览器录制"""
    try:
        # 启动浏览器（必须有头模式）
        start_result = await browser_manager.start(headless=False)
        if not start_result["success"]:
            return start_result

        # 创建录制器
        page = browser_manager.get_page()
        recorder = BrowserRecorder(page)

        # 开始录制
        await recorder.start_recording(template_name)

        logger.info(f"[RPATools] 已开始录制: {template_name}")

        return {
            "success": True,
            "message": f"✅ 已开始录制'{template_name}'\n"
                      f"📝 现在可以在浏览器中操作，所有操作都会被记录\n"
                      f"⚠️ 录制完成后，请调用停止录制工具",
            "recording": True,
            "template_name": template_name
        }

    except Exception as e:
        logger.error(f"[RPATools] 浏览器录制失败: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"❌ 浏览器录制失败: {str(e)}",
            "error": str(e)
        }
