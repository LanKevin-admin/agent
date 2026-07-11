"""
RPA浏览器管理器 - 管理浏览器启动、关闭、会话
"""
import logging
import asyncio
from typing import Optional, Dict, Any
from pathlib import Path
import json
import os
import sys

logger = logging.getLogger(__name__)


class BrowserManager:
    """浏览器管理器"""
    
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.headless = True
        self.is_connected = False  # 是否是连接到现有浏览器

    async def start_or_connect(
        self,
        cdp_url: str = "http://localhost:9222",
        headless: bool = False,
        stealth: bool = True
    ) -> Dict[str, Any]:
        """
        智能启动：优先连接现有浏览器，失败则新建

        Args:
            cdp_url: Chrome远程调试地址
            headless: 是否无头模式
            stealth: 是否启用反检测

        Returns:
            {"success": true/false, "message": "结果", "mode": "connected/created"}
        """
        try:
            # 1. 尝试连接现有浏览器
            result = await self.connect_to_existing(cdp_url)
            if result["success"]:
                logger.info("[BrowserManager] 已连接到现有浏览器")
                mode = "connected"
            else:
                # 2. 连接失败，启动新浏览器
                logger.info("[BrowserManager] 无现有浏览器，启动新实例")
                result = await self.start(headless=headless)

                if not result["success"]:
                    return result

                mode = "created"

            # 3. 注入反检测脚本
            if stealth:
                await self._inject_stealth()

            return {
                "success": True,
                "message": f"✅ 浏览器已就绪（模式: {mode}）",
                "verified": True,
                "mode": mode,
                "stealth": stealth
            }

        except Exception as e:
            logger.error(f"[BrowserManager] 启动/连接失败: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"❌ 浏览器启动失败: {str(e)}",
                "error": str(e)
            }

    async def connect_to_existing(self, cdp_url: str = "http://localhost:9222") -> Dict[str, Any]:
        """
        连接到已运行的Chrome浏览器（CDP协议）

        Args:
            cdp_url: Chrome远程调试地址

        Returns:
            {"success": true/false, "message": "结果"}
        """
        try:
            from playwright.async_api import async_playwright

            # 启动playwright
            if not self.playwright:
                self.playwright = await async_playwright().start()

            # 连接到现有浏览器
            self.browser = await self.playwright.chromium.connect_over_cdp(cdp_url)
            self.is_connected = True

            # 获取第一个上下文（通常是默认的用户会话）
            if len(self.browser.contexts) > 0:
                self.context = self.browser.contexts[0]
            else:
                self.context = await self.browser.new_context()

            # 获取或创建页面
            pages = self.context.pages
            if len(pages) > 0:
                self.page = pages[0]
            else:
                self.page = await self.context.new_page()

            logger.info(f"[BrowserManager] 已连接到现有浏览器（{len(pages)}个标签页）")

            return {
                "success": True,
                "message": f"✅ 已连接到现有浏览器（{len(pages)}个标签页）",
                "verified": True,
                "pages_count": len(pages),
                "mode": "connected"
            }

        except Exception as e:
            logger.warning(f"[BrowserManager] 连接现有浏览器失败: {e}")
            return {
                "success": False,
                "message": f"❌ 连接失败: {str(e)}",
                "error": str(e)
            }

    async def _inject_stealth(self):
        """注入反检测脚本"""
        try:
            # 尝试使用playwright-stealth
            try:
                from playwright_stealth import stealth_async
                await stealth_async(self.page)
                logger.info("[BrowserManager] 已注入playwright-stealth")
                return
            except ImportError:
                pass

            # 手动注入反检测脚本
            await self.page.add_init_script("""
                // 1. 隐藏webdriver
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => false
                });

                // 2. 模拟Chrome对象
                window.chrome = {
                    runtime: {},
                    loadTimes: function() {},
                    csi: function() {},
                    app: {}
                };

                // 3. 修改permissions
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );

                // 4. 模拟插件
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });

                // 5. 模拟语言
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['zh-CN', 'zh', 'en-US', 'en']
                });

                // 6. 模拟平台
                Object.defineProperty(navigator, 'platform', {
                    get: () => 'Win32'
                });
            """)
            logger.info("[BrowserManager] 已注入手动反检测脚本")

        except Exception as e:
            logger.warning(f"[BrowserManager] 注入反检测脚本失败: {e}")
        
    async def start(self, headless: bool = True, **kwargs) -> Dict[str, Any]:
        """
        启动浏览器
        
        Args:
            headless: 是否无头模式
            **kwargs: 其他Playwright启动参数
            
        Returns:
            {"success": true/false, "message": "结果"}
        """
        try:
            from playwright.async_api import async_playwright
            
            self.headless = headless
            
            # 启动Playwright
            self.playwright = await async_playwright().start()
            
            # 启动浏览器
            self.browser = await self.playwright.chromium.launch(
                headless=headless,
                **kwargs
            )
            
            # 创建上下文
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            
            # 创建页面
            self.page = await self.context.new_page()
            
            logger.info(f"[BrowserManager] 浏览器已启动 (headless={headless})")
            
            return {
                "success": True,
                "message": f"✅ 浏览器已启动 ({'无头模式' if headless else '有头模式'})",
                "verified": True
            }
            
        except Exception as e:
            logger.error(f"[BrowserManager] 浏览器启动失败: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"❌ 浏览器启动失败: {str(e)}",
                "verified": False,
                "error": str(e)
            }
    
    async def stop(self) -> Dict[str, Any]:
        """
        关闭浏览器
        
        Returns:
            {"success": true/false, "message": "结果"}
        """
        try:
            if self.page:
                await self.page.close()
                self.page = None
            
            if self.context:
                await self.context.close()
                self.context = None
            
            if self.browser:
                await self.browser.close()
                self.browser = None
            
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None
            
            logger.info("[BrowserManager] 浏览器已关闭")
            
            return {
                "success": True,
                "message": "✅ 浏览器已关闭",
                "verified": True
            }
            
        except Exception as e:
            logger.error(f"[BrowserManager] 浏览器关闭失败: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"❌ 浏览器关闭失败: {str(e)}",
                "verified": False,
                "error": str(e)
            }
    
    async def new_page(self) -> Optional[Any]:
        """创建新页面"""
        if not self.context:
            logger.error("[BrowserManager] 浏览器上下文未初始化")
            return None
        
        page = await self.context.new_page()
        logger.info("[BrowserManager] 已创建新页面")
        return page
    
    def get_page(self) -> Optional[Any]:
        """获取当前页面"""
        return self.page
    
    async def save_cookies(self, session_name: str) -> Dict[str, Any]:
        """
        保存会话Cookies
        
        Args:
            session_name: 会话名称
            
        Returns:
            {"success": true/false, "message": "结果"}
        """
        try:
            if not self.context:
                return {
                    "success": False,
                    "message": "❌ 浏览器上下文未初始化"
                }
            
            # 获取Cookies
            cookies = await self.context.cookies()
            
            # 保存到文件
            if getattr(sys, 'frozen', False):
                base_dir = os.path.dirname(sys.executable)
            else:
                base_dir = os.path.dirname(os.path.dirname(__file__))
            
            sessions_dir = os.path.join(base_dir, "rpa_sessions")
            os.makedirs(sessions_dir, exist_ok=True)
            
            session_file = os.path.join(sessions_dir, f"{session_name}.json")
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(cookies, f, ensure_ascii=False, indent=2)
            
            logger.info(f"[BrowserManager] 会话已保存: {session_name}")
            
            return {
                "success": True,
                "message": f"✅ 会话'{session_name}'已保存",
                "verified": True,
                "session_file": session_file
            }
            
        except Exception as e:
            logger.error(f"[BrowserManager] 保存会话失败: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"❌ 保存会话失败: {str(e)}",
                "verified": False,
                "error": str(e)
            }

    async def load_cookies(self, session_name: str) -> Dict[str, Any]:
        """
        加载会话Cookies

        Args:
            session_name: 会话名称

        Returns:
            {"success": true/false, "message": "结果"}
        """
        try:
            if not self.context:
                return {
                    "success": False,
                    "message": "❌ 浏览器上下文未初始化"
                }

            # 读取会话文件
            if getattr(sys, 'frozen', False):
                base_dir = os.path.dirname(sys.executable)
            else:
                base_dir = os.path.dirname(os.path.dirname(__file__))

            sessions_dir = os.path.join(base_dir, "rpa_sessions")
            session_file = os.path.join(sessions_dir, f"{session_name}.json")

            if not os.path.exists(session_file):
                return {
                    "success": False,
                    "message": f"❌ 会话'{session_name}'不存在"
                }

            with open(session_file, 'r', encoding='utf-8') as f:
                cookies = json.load(f)

            # 加载Cookies
            await self.context.add_cookies(cookies)

            logger.info(f"[BrowserManager] 会话已加载: {session_name}")

            return {
                "success": True,
                "message": f"✅ 会话'{session_name}'已加载",
                "verified": True,
                "cookies_count": len(cookies)
            }

        except Exception as e:
            logger.error(f"[BrowserManager] 加载会话失败: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"❌ 加载会话失败: {str(e)}",
                "verified": False,
                "error": str(e)
            }
