"""
RPA自动化模块

支持浏览器自动化（Playwright）和Windows桌面自动化（pywinauto）
"""

from .executor import RPAExecutor
from .browser_manager import BrowserManager
from .desktop_automation import DesktopAutomation
from .template_recorder import TemplateRecorder, BrowserRecorder
from .smart_repairer import SmartRepairer
from .template_manager import TemplateManager

__all__ = [
    'RPAExecutor',
    'BrowserManager',
    'DesktopAutomation',
    'TemplateRecorder',
    'BrowserRecorder',
    'SmartRepairer',
    'TemplateManager'
]
