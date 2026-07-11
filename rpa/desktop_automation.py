"""
Windows桌面自动化 - 调用Windows API实现桌面程序自动化
使用pywinauto库
"""
import logging
from typing import Dict, Any, Optional, List
import time

logger = logging.getLogger(__name__)


class DesktopAutomation:
    """Windows桌面自动化"""
    
    def __init__(self):
        self.app = None
        self.window = None
        
    def connect_application(self, **kwargs) -> Dict[str, Any]:
        """
        连接到已运行的应用程序
        
        Args:
            title: 窗口标题（模糊匹配）
            class_name: 窗口类名
            process: 进程ID
            path: 程序路径
            
        Returns:
            {"success": true/false, "message": "结果"}
        """
        try:
            from pywinauto import Application
            
            # 连接到应用
            self.app = Application(backend="uia").connect(**kwargs)
            
            logger.info(f"[DesktopAuto] 已连接到应用: {kwargs}")
            
            return {
                "success": True,
                "message": f"✅ 已连接到应用",
                "verified": True
            }
            
        except Exception as e:
            logger.error(f"[DesktopAuto] 连接应用失败: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"❌ 连接失败: {str(e)}",
                "verified": False,
                "error": str(e)
            }
    
    def start_application(self, path: str, **kwargs) -> Dict[str, Any]:
        """
        启动应用程序
        
        Args:
            path: 程序路径
            **kwargs: 其他启动参数
            
        Returns:
            {"success": true/false, "message": "结果"}
        """
        try:
            from pywinauto import Application
            
            # 启动应用
            self.app = Application(backend="uia").start(path, **kwargs)
            
            # 等待窗口出现
            time.sleep(2)
            
            logger.info(f"[DesktopAuto] 已启动应用: {path}")
            
            return {
                "success": True,
                "message": f"✅ 应用已启动: {path}",
                "verified": True
            }
            
        except Exception as e:
            logger.error(f"[DesktopAuto] 启动应用失败: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"❌ 启动失败: {str(e)}",
                "verified": False,
                "error": str(e)
            }
    
    def find_window(self, title: str = None, class_name: str = None) -> Dict[str, Any]:
        """
        查找窗口
        
        Args:
            title: 窗口标题（模糊匹配）
            class_name: 窗口类名
            
        Returns:
            {"success": true/false, "window": window对象}
        """
        try:
            if not self.app:
                return {
                    "success": False,
                    "message": "❌ 应用未连接"
                }
            
            # 查找窗口
            if title:
                self.window = self.app.window(title=title)
            elif class_name:
                self.window = self.app.window(class_name=class_name)
            else:
                self.window = self.app.top_window()
            
            # 等待窗口可用
            self.window.wait('ready', timeout=10)
            
            logger.info(f"[DesktopAuto] 已找到窗口: {title or class_name or '顶层窗口'}")
            
            return {
                "success": True,
                "message": f"✅ 已找到窗口",
                "verified": True,
                "window": self.window
            }
            
        except Exception as e:
            logger.error(f"[DesktopAuto] 查找窗口失败: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"❌ 查找窗口失败: {str(e)}",
                "verified": False,
                "error": str(e)
            }
    
    def click_element(self, control_id: str = None, automation_id: str = None, **kwargs) -> Dict[str, Any]:
        """
        点击元素
        
        Args:
            control_id: 控件ID
            automation_id: 自动化ID
            **kwargs: 其他查找参数（title, class_name等）
            
        Returns:
            {"success": true/false, "message": "结果"}
        """
        try:
            if not self.window:
                return {
                    "success": False,
                    "message": "❌ 窗口未找到"
                }
            
            # 查找控件
            if control_id:
                control = self.window.child_window(auto_id=control_id)
            elif automation_id:
                control = self.window.child_window(auto_id=automation_id)
            else:
                control = self.window.child_window(**kwargs)

            # 点击
            control.click()

            logger.info(f"[DesktopAuto] 已点击: {control_id or automation_id or kwargs}")

            return {
                "success": True,
                "message": "✅ 已点击元素",
                "verified": True
            }

        except Exception as e:
            logger.error(f"[DesktopAuto] 点击失败: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"❌ 点击失败: {str(e)}",
                "verified": False,
                "error": str(e)
            }

    def input_text(self, control_id: str, text: str, **kwargs) -> Dict[str, Any]:
        """
        输入文本

        Args:
            control_id: 控件ID
            text: 要输入的文本
            **kwargs: 其他查找参数

        Returns:
            {"success": true/false, "message": "结果"}
        """
        try:
            if not self.window:
                return {
                    "success": False,
                    "message": "❌ 窗口未找到"
                }

            # 查找控件
            control = self.window.child_window(auto_id=control_id, **kwargs)

            # 输入文本
            control.set_text(text)

            logger.info(f"[DesktopAuto] 已输入文本到: {control_id}")

            return {
                "success": True,
                "message": "✅ 已输入文本",
                "verified": True
            }

        except Exception as e:
            logger.error(f"[DesktopAuto] 输入文本失败: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"❌ 输入文本失败: {str(e)}",
                "verified": False,
                "error": str(e)
            }

    def get_text(self, control_id: str, **kwargs) -> Dict[str, Any]:
        """
        获取文本

        Args:
            control_id: 控件ID
            **kwargs: 其他查找参数

        Returns:
            {"success": true/false, "text": "文本内容"}
        """
        try:
            if not self.window:
                return {
                    "success": False,
                    "message": "❌ 窗口未找到"
                }

            # 查找控件
            control = self.window.child_window(auto_id=control_id, **kwargs)

            # 获取文本
            text = control.window_text()

            logger.info(f"[DesktopAuto] 已获取文本: {control_id}")

            return {
                "success": True,
                "message": "✅ 已获取文本",
                "verified": True,
                "text": text
            }

        except Exception as e:
            logger.error(f"[DesktopAuto] 获取文本失败: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"❌ 获取文本失败: {str(e)}",
                "verified": False,
                "error": str(e)
            }
