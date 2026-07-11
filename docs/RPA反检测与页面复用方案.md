# RPA反检测与页面复用方案

## 🎯 核心需求

### 1. **页面复用** - 不重复打开浏览器
```
问题：每次执行RPA都启动新浏览器，会导致：
❌ 需要重新登录
❌ 会话状态丢失
❌ Cookie丢失
❌ 资源浪费

解决：连接到已运行的浏览器实例
✅ 保持登录状态
✅ 会话持续
✅ 可以手动操作+自动操作混合
```

### 2. **反检测** - 模拟人工操作
```
问题：自动化工具容易被检测为机器人：
❌ navigator.webdriver = true
❌ 缺少Chrome插件
❌ 鼠标移动轨迹不自然
❌ 操作速度过快

解决：反检测 + 人类行为模拟
✅ 隐藏自动化特征
✅ 随机延迟
✅ 模拟鼠标轨迹
✅ 真实浏览器环境
```

---

## 🔧 方案1：连接到现有Chrome（CDP协议）

### 原理：Chrome Remote Debugging

```
1. 启动Chrome时开启远程调试端口
   chrome.exe --remote-debugging-port=9222

2. Playwright连接到这个端口
   browser = await playwright.chromium.connect_over_cdp("http://localhost:9222")

3. 获取已打开的页面
   pages = browser.contexts[0].pages
   page = pages[0]  # 使用第一个标签页

优点：
✅ 不重复启动浏览器
✅ 保持所有会话状态
✅ 可以手动操作混合自动化
✅ 真实用户环境（有插件、有历史记录）
```

### 实现代码

```python
class BrowserManager:
    async def connect_to_existing(self, cdp_url: str = "http://localhost:9222") -> Dict:
        """连接到已运行的Chrome"""
        try:
            from playwright.async_api import async_playwright
            
            self.playwright = await async_playwright().start()
            
            # 连接到现有浏览器
            self.browser = await self.playwright.chromium.connect_over_cdp(cdp_url)
            
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
            
            return {
                "success": True,
                "message": f"✅ 已连接到现有浏览器（{len(pages)}个标签页）",
                "verified": True,
                "pages_count": len(pages)
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"❌ 连接失败: {str(e)}",
                "error": str(e)
            }
```

### 使用方式

```python
# 1. 手动启动Chrome（只需一次）
# Windows:
# "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\chrome_rpa_profile"

# 2. 后续所有RPA都连接到这个Chrome
browser = BrowserManager()
await browser.connect_to_existing()  # 连接到已打开的Chrome

# 3. 执行RPA任务
page = browser.get_page()
await page.goto("https://feishu.cn")
# ... 执行操作

# 4. 完成后不关闭浏览器（保持会话）
# browser不调用stop()，浏览器继续运行
```

---

## 🕵️ 方案2：反检测技术

### 技术选型

#### 方案A：playwright-stealth（推荐）

```python
# 安装
pip install playwright-stealth

# 使用
from playwright_stealth import stealth_async

page = await browser.new_page()
await stealth_async(page)  # 注入反检测脚本

# 效果：
# ✅ navigator.webdriver = false
# ✅ chrome.runtime存在
# ✅ plugins不为空
# ✅ permissions正常
# ✅ 通过大部分机器人检测
```

#### 方案B：手动注入反检测脚本

```python
async def inject_anti_detection(page):
    """手动注入反检测脚本"""
    await page.add_init_script("""
        // 1. 隐藏webdriver
        Object.defineProperty(navigator, 'webdriver', {
            get: () => false
        });
        
        // 2. 模拟Chrome对象
        window.chrome = {
            runtime: {}
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
    """)
```

---

## 🎭 方案3：人类行为模拟

### 1. 随机延迟

```python
import random
import asyncio

async def human_delay(min_ms=500, max_ms=2000):
    """模拟人类操作延迟"""
    delay = random.uniform(min_ms, max_ms) / 1000
    await asyncio.sleep(delay)

# 使用
await page.click('#button')
await human_delay(800, 1500)  # 随机延迟800-1500ms
await page.fill('#input', 'text')
```

### 2. 模拟鼠标轨迹

```python
async def human_mouse_move(page, selector):
    """模拟人类鼠标移动轨迹"""
    element = await page.query_selector(selector)
    box = await element.bounding_box()
    
    # 当前鼠标位置（假设在(0,0)）
    start_x, start_y = 0, 0
    
    # 目标位置（元素中心）
    end_x = box['x'] + box['width'] / 2
    end_y = box['y'] + box['height'] / 2
    
    # 生成贝塞尔曲线轨迹（模拟人类移动）
    steps = random.randint(20, 40)
    for i in range(steps):
        t = i / steps
        # 添加随机抖动
        noise_x = random.uniform(-5, 5)
        noise_y = random.uniform(-5, 5)
        
        x = start_x + (end_x - start_x) * t + noise_x
        y = start_y + (end_y - start_y) * t + noise_y
        
        await page.mouse.move(x, y)
        await asyncio.sleep(random.uniform(0.01, 0.03))
    
    # 最后点击
    await page.mouse.click(end_x, end_y)
```

### 3. 随机化操作顺序

```python
async def human_input(page, selector, text):
    """模拟人类输入（逐字输入+随机停顿）"""
    await page.click(selector)
    await human_delay(200, 500)
    
    for char in text:
        await page.keyboard.type(char)
        # 随机延迟，模拟打字速度
        await asyncio.sleep(random.uniform(0.05, 0.2))
        
        # 偶尔停顿（思考）
        if random.random() < 0.1:  # 10%概率停顿
            await asyncio.sleep(random.uniform(0.5, 1.5))
```

---

## 🚀 综合方案（推荐）

### 架构设计

```
Chrome浏览器（远程调试模式）
    ↓
Playwright连接（CDP）
    ↓
反检测脚本注入
    ↓
人类行为模拟
    ↓
RPA执行引擎
```

### 实现代码

```python
class SmartBrowserManager(BrowserManager):
    """智能浏览器管理器 - 支持复用+反检测"""
    
    async def start_or_connect(
        self,
        cdp_url: str = "http://localhost:9222",
        headless: bool = False,
        stealth: bool = True
    ) -> Dict:
        """智能启动：优先连接现有浏览器，失败则新建"""
        
        # 1. 尝试连接现有浏览器
        result = await self.connect_to_existing(cdp_url)
        if result["success"]:
            logger.info("[SmartBrowser] 已连接到现有浏览器")
        else:
            # 2. 连接失败，启动新浏览器
            logger.info("[SmartBrowser] 无现有浏览器，启动新实例")
            result = await self.start(headless=headless)
            
            if not result["success"]:
                return result
        
        # 3. 注入反检测脚本
        if stealth:
            await self._inject_stealth()
        
        return {
            "success": True,
            "message": "✅ 浏览器已就绪（已启用反检测）",
            "verified": True
        }
    
    async def _inject_stealth(self):
        """注入反检测脚本"""
        try:
            # 方案1：使用playwright-stealth
            from playwright_stealth import stealth_async
            await stealth_async(self.page)
            logger.info("[SmartBrowser] 已注入playwright-stealth")
        except ImportError:
            # 方案2：手动注入
            await self._inject_anti_detection_manual()
            logger.info("[SmartBrowser] 已注入手动反检测脚本")
```

---

## 📦 依赖补充

```txt
# requirements.txt

# 反检测库（可选，但推荐）
playwright-stealth>=1.0.0

# 或者使用undetected版本
# undetected-playwright>=0.3.0
```

---

## 💡 使用建议

### 日常使用流程

```
1. 【首次启动】手动启动Chrome（远程调试模式）
   运行脚本: python scripts/start_chrome_debug.py
   
2. 【RPA执行】所有RPA都连接到这个Chrome
   browser.start_or_connect()  # 自动连接
   
3. 【保持运行】任务完成后不关闭浏览器
   保持登录状态、Cookie、会话
   
4. 【定期重启】每天或每周重启一次Chrome
   清理内存、更新状态
```

### 反检测最佳实践

```
✅ 使用真实的user-data-dir（有历史记录）
✅ 添加常见浏览器插件
✅ 启用图片加载
✅ 随机化操作时间
✅ 模拟鼠标轨迹
✅ 避免高频操作
✅ 使用代理IP（如需要）
❌ 不要使用无头模式（容易被检测）
❌ 不要并发过多（看起来像攻击）
```

---

## 🎯 最终推荐配置

```python
# 启动配置
config = {
    "mode": "connect",  # 优先连接现有浏览器
    "cdp_url": "http://localhost:9222",
    "stealth": True,  # 启用反检测
    "human_behavior": True,  # 启用人类行为模拟
    "random_delay": (500, 2000),  # 操作延迟范围（毫秒）
    "user_data_dir": "C:/chrome_rpa_profile",  # 使用真实用户配置
    "headless": False  # 必须有头模式
}
```

**这个方案可以让你的RPA：**
- ✅ 像真人一样操作
- ✅ 不被检测为机器人
- ✅ 保持浏览器会话
- ✅ 可以手动+自动混合操作
- ✅ 稳定可靠
