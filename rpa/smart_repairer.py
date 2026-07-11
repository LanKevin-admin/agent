"""
RPA智能修复器 - 自动检测并修复失效的元素选择器
"""
import logging
from typing import Dict, Any, List, Optional
import difflib

logger = logging.getLogger(__name__)


class SmartRepairer:
    """智能修复器 - 元素失效时自动查找替代"""
    
    def __init__(self, page):
        """
        Args:
            page: Playwright page对象
        """
        self.page = page
        self.repair_history = []
        
    async def find_element_smart(
        self, 
        selector: str, 
        fallback_selectors: List[str] = None,
        context: Dict[str, Any] = None
    ) -> Optional[Any]:
        """
        智能查找元素
        
        Args:
            selector: 主选择器
            fallback_selectors: 备用选择器列表
            context: 上下文信息（用于AI分析）
            
        Returns:
            找到的元素，或None
        """
        # 1. 尝试主选择器
        element = await self.page.query_selector(selector)
        if element:
            logger.debug(f"[SmartRepairer] 主选择器成功: {selector}")
            return element
        
        logger.warning(f"[SmartRepairer] 主选择器失效: {selector}")
        
        # 2. 尝试备用选择器
        if fallback_selectors:
            for fallback in fallback_selectors:
                element = await self.page.query_selector(fallback)
                if element:
                    logger.info(f"[SmartRepairer] 备用选择器成功: {fallback}")
                    self._record_repair(selector, fallback, "fallback_success")
                    return element
        
        # 3. 智能搜索相似元素
        logger.info(f"[SmartRepairer] 启动智能搜索...")
        element, new_selector = await self._smart_search(selector, context)
        
        if element:
            logger.info(f"[SmartRepairer] 智能搜索成功: {new_selector}")
            self._record_repair(selector, new_selector, "smart_search")
            return element
        
        logger.error(f"[SmartRepairer] 未找到元素: {selector}")
        return None
    
    async def _smart_search(
        self, 
        original_selector: str, 
        context: Dict = None
    ) -> tuple[Optional[Any], Optional[str]]:
        """
        智能搜索相似元素
        
        策略：
        1. 分析原选择器的特征（id/class/type/text）
        2. 在页面中搜索相似元素
        3. 根据相似度排序
        4. 返回最匹配的元素
        """
        # 提取原选择器的特征
        features = self._extract_selector_features(original_selector)
        
        # 获取页面上所有可能的元素
        candidates = await self._get_candidate_elements(features)
        
        if not candidates:
            return None, None
        
        # 找到最匹配的
        best_match = candidates[0]
        return best_match["element"], best_match["selector"]
    
    def _extract_selector_features(self, selector: str) -> Dict[str, Any]:
        """提取选择器特征"""
        features = {
            "original": selector,
            "keywords": []
        }
        
        # 提取关键词
        keywords = [
            "username", "user", "name",
            "password", "pwd", "pass",
            "email", "mail",
            "submit", "login", "button",
            "search", "query",
            "input", "text", "field"
        ]
        
        selector_lower = selector.lower()
        for keyword in keywords:
            if keyword in selector_lower:
                features["keywords"].append(keyword)
        
        # 提取类型
        if "[type=" in selector:
            type_match = selector.split("[type=")[1].split("]")[0].strip('"\'')
            features["type"] = type_match
        
        return features
    
    async def _get_candidate_elements(self, features: Dict) -> List[Dict]:
        """获取候选元素"""
        # 使用JS在页面中搜索相似元素
        candidates = await self.page.evaluate("""
            (features) => {
                const results = [];
                const keywords = features.keywords || [];
                
                // 搜索所有input元素
                const inputs = document.querySelectorAll('input, button, textarea, select');
                
                inputs.forEach((el, index) => {
                    let score = 0;
                    const selectors = [];
                    
                    // 生成选择器
                    if (el.id) {
                        selectors.push('#' + el.id);
                        // 检查ID是否包含关键词
                        keywords.forEach(kw => {
                            if (el.id.toLowerCase().includes(kw)) score += 10;
                        });
                    }
                    
                    if (el.name) {
                        selectors.push('[name="' + el.name + '"]');
                        keywords.forEach(kw => {
                            if (el.name.toLowerCase().includes(kw)) score += 10;
                        });
                    }
                    
                    if (el.className) {
                        const classes = el.className.split(' ').filter(c => c);
                        if (classes.length) {
                            selectors.push('.' + classes.join('.'));
                            classes.forEach(cls => {
                                keywords.forEach(kw => {
                                    if (cls.toLowerCase().includes(kw)) score += 5;
                                });
                            });
                        }
                    }
                    
                    if (el.type) {
                        selectors.push('[type="' + el.type + '"]');
                        if (features.type && el.type === features.type) {
                            score += 15;
                        }
                    }
                    
                    // 检查placeholder
                    if (el.placeholder) {
                        keywords.forEach(kw => {
                            if (el.placeholder.toLowerCase().includes(kw)) score += 8;
                        });
                    }
                    
                    // 检查label
                    const label = document.querySelector(`label[for="${el.id}"]`);
                    if (label) {
                        keywords.forEach(kw => {
                            if (label.textContent.toLowerCase().includes(kw)) score += 12;
                        });
                    }
                    
                    if (score > 0 && selectors.length > 0) {
                        results.push({
                            selector: selectors[0],
                            allSelectors: selectors,
                            score: score,
                            tag: el.tagName.toLowerCase(),
                            type: el.type || null,
                            index: index
                        });
                    }
                });
                
                // 按分数排序
                results.sort((a, b) => b.score - a.score);
                
                return results.slice(0, 5);  // 返回前5个最匹配的
            }
        """, features)
        
        # 为每个候选元素获取实际的Playwright元素对象
        result_with_elements = []
        for candidate in candidates:
            element = await self.page.query_selector(candidate["selector"])
            if element:
                result_with_elements.append({
                    **candidate,
                    "element": element
                })
        
        return result_with_elements
    
    def _record_repair(self, old_selector: str, new_selector: str, method: str):
        """记录修复历史"""
        from datetime import datetime
        repair_record = {
            "timestamp": datetime.now().isoformat(),
            "old_selector": old_selector,
            "new_selector": new_selector,
            "method": method
        }
        self.repair_history.append(repair_record)
        
    def get_repair_suggestions(self) -> List[Dict]:
        """获取修复建议（用于更新模板）"""
        suggestions = []
        
        for repair in self.repair_history:
            suggestions.append({
                "old": repair["old_selector"],
                "new": repair["new_selector"],
                "confidence": 0.95 if repair["method"] == "fallback_success" else 0.75,
                "reason": f"通过{repair['method']}方法找到替代元素"
            })
        
        return suggestions
