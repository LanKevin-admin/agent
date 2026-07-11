"""
RPA执行引擎 - 根据模板执行自动化任务
"""
import logging
import asyncio
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class RPAExecutor:
    """RPA执行引擎"""
    
    def __init__(self, page=None):
        """
        Args:
            page: Playwright page对象（可选，延迟初始化）
        """
        self.page = page
        self.execution_log = []
        self.variables = {}  # 存储执行过程中的变量
        
    async def execute_template(
        self, 
        template: Dict[str, Any], 
        parameters: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        执行RPA模板
        
        Args:
            template: 模板配置
            parameters: 参数值
            
        Returns:
            {
                "success": true/false,
                "message": "执行结果",
                "output": {...},
                "execution_log": [...]
            }
        """
        self.execution_log = []
        self.variables = parameters or {}
        
        template_name = template.get("name", "未命名模板")
        logger.info(f"[RPAExecutor] 开始执行模板: {template_name}")
        
        try:
            # 验证参数
            missing_params = self._validate_parameters(template, parameters)
            if missing_params:
                return {
                    "success": False,
                    "message": f"❌ 缺少必需参数: {', '.join(missing_params)}",
                    "verified": False
                }
            
            # 执行步骤
            steps = template.get("steps", [])
            for i, step in enumerate(steps):
                logger.info(f"[RPAExecutor] 执行步骤 {i+1}/{len(steps)}: {step.get('action')}")
                
                try:
                    result = await self._execute_step(step)
                    
                    self.execution_log.append({
                        "step": i + 1,
                        "action": step.get("action"),
                        "description": step.get("description", ""),
                        "result": "success",
                        "details": result
                    })
                    
                except Exception as e:
                    error_msg = f"步骤 {i+1} 失败: {str(e)}"
                    logger.error(f"[RPAExecutor] {error_msg}", exc_info=True)
                    
                    self.execution_log.append({
                        "step": i + 1,
                        "action": step.get("action"),
                        "description": step.get("description", ""),
                        "result": "failed",
                        "error": str(e)
                    })
                    
                    return {
                        "success": False,
                        "message": f"❌ {error_msg}",
                        "verified": False,
                        "execution_log": self.execution_log
                    }
            
            # 提取输出
            output = template.get("output", {})
            
            logger.info(f"[RPAExecutor] 模板执行成功: {template_name}")
            
            return {
                "success": True,
                "message": f"✅ 执行成功！完成 {len(steps)} 个步骤",
                "verified": True,
                "output": output,
                "execution_log": self.execution_log,
                "variables": self.variables
            }
            
        except Exception as e:
            logger.error(f"[RPAExecutor] 模板执行失败: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"❌ 执行失败: {str(e)}",
                "verified": False,
                "error": str(e),
                "execution_log": self.execution_log
            }
    
    def _validate_parameters(self, template: Dict, parameters: Dict) -> List[str]:
        """验证参数"""
        missing = []
        required_params = template.get("parameters", {})
        
        for param_name, param_config in required_params.items():
            if param_config.get("required", False):
                if not parameters or param_name not in parameters:
                    missing.append(param_name)
        
        return missing
    
    async def _execute_step(self, step: Dict[str, Any]) -> Any:
        """执行单个步骤"""
        action = step.get("action")
        
        # 替换变量占位符
        step_data = self._replace_variables(step)
        
        # 根据动作类型执行
        if action == "navigate":
            return await self._action_navigate(step_data)
        elif action == "click":
            return await self._action_click(step_data)
        elif action == "input":
            return await self._action_input(step_data)
        elif action == "wait":
            return await self._action_wait(step_data)
        elif action == "wait_for_navigation":
            return await self._action_wait_navigation(step_data)
        elif action == "screenshot":
            return await self._action_screenshot(step_data)
        elif action == "extract_data":
            return await self._action_extract_data(step_data)
        elif action == "verify":
            return await self._action_verify(step_data)
        else:
            raise ValueError(f"未知的动作类型: {action}")
    
    def _replace_variables(self, data: Any) -> Any:
        """替换变量占位符 {{variable}}"""
        if isinstance(data, str):
            # 替换 {{key}} 格式的占位符
            for key, value in self.variables.items():
                placeholder = f"{{{{{key}}}}}"
                if placeholder in data:
                    data = data.replace(placeholder, str(value))
            return data
        elif isinstance(data, dict):
            return {k: self._replace_variables(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._replace_variables(item) for item in data]
        else:
            return data

    async def _action_navigate(self, step: Dict) -> Dict:
        """导航到URL"""
        url = step.get("url")
        wait = step.get("wait", 0)

        if not self.page:
            raise RuntimeError("浏览器页面未初始化")

        await self.page.goto(url)
        logger.info(f"[RPAExecutor] 已导航到: {url}")

        if wait > 0:
            await asyncio.sleep(wait)

        return {"url": url}

    async def _action_click(self, step: Dict) -> Dict:
        """点击元素"""
        selector = step.get("selector")
        fallback_selectors = step.get("fallback_selectors", [])

        if not self.page:
            raise RuntimeError("浏览器页面未初始化")

        # 智能查找元素（支持备用选择器）
        element = await self._find_element_smart(selector, fallback_selectors)

        if not element:
            raise RuntimeError(f"未找到元素: {selector}")

        await element.click()
        logger.info(f"[RPAExecutor] 已点击: {selector}")

        return {"selector": selector}

    async def _action_input(self, step: Dict) -> Dict:
        """输入文本"""
        selector = step.get("selector")
        value = step.get("value")
        fallback_selectors = step.get("fallback_selectors", [])
        clear = step.get("clear", True)

        if not self.page:
            raise RuntimeError("浏览器页面未初始化")

        element = await self._find_element_smart(selector, fallback_selectors)

        if not element:
            raise RuntimeError(f"未找到元素: {selector}")

        if clear:
            await element.fill("")

        await element.type(value)
        logger.info(f"[RPAExecutor] 已输入文本到: {selector}")

        return {"selector": selector, "value": "***" if "password" in selector.lower() else value}

    async def _action_wait(self, step: Dict) -> Dict:
        """等待"""
        seconds = step.get("seconds", 1)
        await asyncio.sleep(seconds)
        logger.info(f"[RPAExecutor] 已等待 {seconds} 秒")
        return {"seconds": seconds}

    async def _action_wait_navigation(self, step: Dict) -> Dict:
        """等待页面导航"""
        timeout = step.get("timeout", 30000)

        if not self.page:
            raise RuntimeError("浏览器页面未初始化")

        await self.page.wait_for_load_state("networkidle", timeout=timeout)
        logger.info(f"[RPAExecutor] 页面导航完成")

        return {"url": self.page.url}

    async def _action_screenshot(self, step: Dict) -> Dict:
        """截图"""
        filename = step.get("filename", "screenshot.png")

        if not self.page:
            raise RuntimeError("浏览器页面未初始化")

        # 保存到reports目录
        import os
        import sys
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.dirname(__file__))

        reports_dir = os.path.join(base_dir, "reports")
        os.makedirs(reports_dir, exist_ok=True)

        filepath = os.path.join(reports_dir, filename)
        await self.page.screenshot(path=filepath)
        logger.info(f"[RPAExecutor] 已截图: {filepath}")

        return {"filepath": filepath}

    async def _action_extract_data(self, step: Dict) -> Dict:
        """提取数据"""
        selector = step.get("selector")
        fields = step.get("fields", {})
        output_var = step.get("output", "extracted_data")

        if not self.page:
            raise RuntimeError("浏览器页面未初始化")

        # 查找容器元素
        container = await self.page.query_selector(selector)
        if not container:
            raise RuntimeError(f"未找到容器: {selector}")

        # 提取数据
        data = []
        rows = await container.query_selector_all("tr")

        for row in rows:
            row_data = {}
            for field_name, field_selector in fields.items():
                cell = await row.query_selector(field_selector)
                if cell:
                    row_data[field_name] = await cell.inner_text()

            if row_data:
                data.append(row_data)

        # 存储到变量
        self.variables[output_var] = data

        logger.info(f"[RPAExecutor] 已提取 {len(data)} 条数据")
        return {"count": len(data), "data": data}

    async def _action_verify(self, step: Dict) -> Dict:
        """验证元素存在"""
        selector = step.get("selector")

        if not self.page:
            raise RuntimeError("浏览器页面未初始化")

        element = await self.page.query_selector(selector)

        if not element:
            raise RuntimeError(f"验证失败: 未找到元素 {selector}")

        logger.info(f"[RPAExecutor] 验证成功: {selector}")
        return {"verified": True}

    async def _find_element_smart(self, selector: str, fallback_selectors: List[str]) -> Optional[Any]:
        """智能查找元素（支持备用选择器）"""
        if not self.page:
            return None

        # 1. 尝试主选择器
        element = await self.page.query_selector(selector)
        if element:
            return element

        # 2. 尝试备用选择器
        for fallback in fallback_selectors:
            element = await self.page.query_selector(fallback)
            if element:
                logger.warning(f"[RPAExecutor] 主选择器失效，使用备用: {fallback}")
                return element

        return None

