"""
RPA模板录制器 - 录制用户操作自动生成模板
"""
import json
import logging
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)


class TemplateRecorder:
    """RPA模板录制器"""
    
    def __init__(self):
        self.recording = False
        self.actions = []
        self.start_time = None
        self.template_name = None
        
    def start_recording(self, template_name: str):
        """开始录制"""
        self.recording = True
        self.actions = []
        self.start_time = datetime.now()
        self.template_name = template_name
        logger.info(f"[Recorder] 开始录制模板: {template_name}")
        
    def stop_recording(self) -> Dict[str, Any]:
        """停止录制并生成模板"""
        self.recording = False
        duration = (datetime.now() - self.start_time).total_seconds()
        
        template = {
            "template_id": self.template_name.lower().replace(" ", "_"),
            "name": self.template_name,
            "description": f"录制于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "recording_duration": duration,
            "parameters": self._extract_parameters(),
            "steps": self.actions,
            "metadata": {
                "recorded": True,
                "action_count": len(self.actions)
            }
        }
        
        logger.info(f"[Recorder] 录制完成: {len(self.actions)} 个操作")
        return template
    
    def record_action(self, action_type: str, **kwargs):
        """记录一个操作"""
        if not self.recording:
            return
            
        action = {
            "action": action_type,
            "timestamp": (datetime.now() - self.start_time).total_seconds(),
            **kwargs
        }
        
        # 自动添加描述
        action["description"] = self._generate_description(action)
        
        self.actions.append(action)
        logger.debug(f"[Recorder] 记录操作: {action_type}")
        
    def _generate_description(self, action: Dict) -> str:
        """生成操作描述"""
        action_type = action["action"]
        
        if action_type == "navigate":
            return f"访问 {action.get('url', '')}"
        elif action_type == "click":
            return f"点击元素 {action.get('selector', '')}"
        elif action_type == "input":
            return f"输入文本到 {action.get('selector', '')}"
        elif action_type == "wait":
            return f"等待 {action.get('seconds', 0)} 秒"
        else:
            return f"执行 {action_type}"
    
    def _extract_parameters(self) -> Dict[str, Dict]:
        """从录制的操作中提取参数"""
        parameters = {}
        
        for action in self.actions:
            if action["action"] == "input":
                # 输入操作可能需要参数化
                selector = action.get("selector", "")
                if "username" in selector.lower() or "user" in selector.lower():
                    parameters["username"] = {
                        "type": "string",
                        "required": True,
                        "description": "用户名"
                    }
                elif "password" in selector.lower() or "pwd" in selector.lower():
                    parameters["password"] = {
                        "type": "string",
                        "required": True,
                        "description": "密码",
                        "sensitive": True
                    }
        
        return parameters


class BrowserRecorder:
    """浏览器操作录制器（与Playwright集成）"""
    
    def __init__(self, page):
        """
        Args:
            page: Playwright page对象
        """
        self.page = page
        self.recorder = TemplateRecorder()
        
    async def start_recording(self, template_name: str):
        """开始录制"""
        self.recorder.start_recording(template_name)
        
        # 监听页面事件
        self.page.on("load", self._on_page_load)
        self.page.on("framenavigated", self._on_navigation)
        
    def _on_page_load(self, page):
        """页面加载事件"""
        url = page.url
        self.recorder.record_action("navigate", url=url)
        
    def _on_navigation(self, frame):
        """页面导航事件"""
        if frame == self.page.main_frame:
            url = frame.url
            self.recorder.record_action("wait_for_navigation", url=url)
    
    async def record_click(self, selector: str):
        """记录点击操作"""
        element = await self.page.query_selector(selector)
        if element:
            # 获取元素的多个选择器（备用）
            fallback_selectors = await self._get_fallback_selectors(element)
            
            self.recorder.record_action(
                "click",
                selector=selector,
                fallback_selectors=fallback_selectors
            )
    
    async def record_input(self, selector: str, value: str):
        """记录输入操作"""
        element = await self.page.query_selector(selector)
        if element:
            fallback_selectors = await self._get_fallback_selectors(element)
            
            # 判断是否需要参数化
            is_sensitive = any(
                keyword in selector.lower() 
                for keyword in ['password', 'pwd', 'secret', 'token']
            )
            
            self.recorder.record_action(
                "input",
                selector=selector,
                value="{{password}}" if is_sensitive else value,
                fallback_selectors=fallback_selectors
            )
    
    async def _get_fallback_selectors(self, element) -> List[str]:
        """获取元素的备用选择器"""
        selectors = []
        
        # 通过JS获取多种选择器
        result = await element.evaluate("""
            (el) => {
                const selectors = [];
                
                // ID选择器
                if (el.id) selectors.push('#' + el.id);
                
                // Name选择器
                if (el.name) selectors.push('[name="' + el.name + '"]');
                
                // Class选择器
                if (el.className) {
                    const classes = el.className.split(' ').filter(c => c);
                    if (classes.length) {
                        selectors.push('.' + classes.join('.'));
                    }
                }
                
                // 属性选择器
                if (el.type) selectors.push('[type="' + el.type + '"]');
                
                return selectors;
            }
        """)
        
        return result
    
    def stop_recording(self) -> Dict[str, Any]:
        """停止录制并返回模板"""
        template = self.recorder.stop_recording()
        return template
