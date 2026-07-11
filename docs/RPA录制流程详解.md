# RPA录制流程详解

## 📋 录制流程底层逻辑

### 方案对比

#### ❌ 方案1：浏览器插件录制（复杂）
**Chrome扩展方式：**
- 需要开发Chrome扩展（manifest.json + background.js + content.js）
- 需要用户手动安装插件
- 需要Chrome应用商店审核（或开发者模式加载）
- 需要额外学习Chrome扩展API
- **优点**：可以录制任何浏览器操作
- **缺点**：开发复杂、分发困难、维护成本高

#### ✅ 方案2：Playwright内置录制（推荐）
**使用Playwright Codegen：**
- Playwright自带录制工具（playwright codegen）
- 自动生成Python代码
- 无需插件，一键启动
- **优点**：简单、稳定、官方支持
- **缺点**：需要安装Playwright

#### ✅ 方案3：监听Playwright事件（我们的方案）
**事件监听方式：**
- 使用Playwright的CDP (Chrome DevTools Protocol)
- 监听所有用户操作事件
- 实时转换为模板JSON
- **优点**：自动化、可定制、无需插件
- **缺点**：需要编写事件处理逻辑

---

## 🔧 我们的录制方案（方案3）

### 底层原理

```
用户操作浏览器
    ↓
Playwright Page对象监听事件
    ↓
CDP (Chrome DevTools Protocol)
    ↓
BrowserRecorder捕获事件
    ↓
转换为模板JSON步骤
    ↓
保存为模板文件
```

### 核心代码逻辑

```python
# 1. 启动浏览器（有头模式）
browser = await playwright.chromium.launch(headless=False)
page = await browser.new_page()

# 2. 监听所有点击事件
page.on('click', lambda: recorder.record_action('click', ...))

# 3. 监听所有输入事件
page.on('input', lambda: recorder.record_action('input', ...))

# 4. 监听导航事件
page.on('framenavigated', lambda: recorder.record_action('navigate', ...))

# 5. 用户操作完成后，生成模板
template = recorder.stop_recording()
# 返回完整的JSON模板
```

---

## 📝 Playwright内置录制（更简单的方式）

### 方法1：使用playwright codegen命令

```bash
# 直接录制并生成代码
playwright codegen https://feishu.cn

# 优点：
# - 自动录制所有操作
# - 自动生成选择器
# - 支持断言录制
# - 可以直接运行

# 缺点：
# - 生成的是Python代码，不是我们的JSON模板格式
# - 需要手动转换为模板
```

### 方法2：使用Inspector API

```python
from playwright.sync_api import sync_playwright

# Playwright提供的暂停功能
page.pause()  # 会打开Inspector界面，可以手动选择元素

# 优点：
# - 可以手动选择元素
# - 查看所有可用的选择器
# - 调试方便

# 缺点：
# - 需要手动操作
# - 不是自动录制
```

---

## 🎯 我们推荐的混合方案

### 录制流程

#### 1. **用户触发录制**
```
AI："开始录制飞书登录模板"
系统：启动浏览器（有头模式）+ 打开Playwright Inspector
```

#### 2. **两种录制方式**

**方式A：自动录制（事件监听）**
```python
# BrowserRecorder自动监听
recorder = BrowserRecorder(page)
await recorder.start_recording("feishu_login")

# 用户操作：
# 1. 点击登录按钮
# 2. 输入用户名
# 3. 输入密码
# 4. 点击提交

# 自动记录所有操作
```

**方式B：半自动录制（Playwright Codegen）**
```bash
# 1. 运行codegen
playwright codegen https://feishu.cn

# 2. 用户操作，自动生成代码：
page.click('#login')
page.fill('#username', 'test@example.com')
page.fill('#password', '***')
page.click('button[type="submit"]')

# 3. 我们的工具自动转换为JSON模板
```

#### 3. **停止录制并保存**
```
AI："停止录制"
系统：生成模板JSON → 自动识别参数 → 保存到rpa_templates/
```

---

## 🔌 是否需要浏览器插件？

### ❌ 不需要插件的原因

1. **Playwright已经够强大**
   ```python
   # Playwright可以直接控制浏览器
   page.click('#button')  # 点击
   page.fill('#input', 'text')  # 输入
   page.screenshot(path='screenshot.png')  # 截图
   page.evaluate('() => document.title')  # 执行JS
   ```

2. **CDP协议足够**
   ```python
   # Chrome DevTools Protocol
   # Playwright底层就是通过CDP控制浏览器
   # 可以监听所有事件，无需插件
   ```

3. **插件的缺点**
   - 需要用户手动安装
   - Chrome商店审核慢
   - 维护成本高
   - 可能有安全风险
   - 跨浏览器支持差

### ✅ 推荐方案

**不使用插件，直接用Playwright：**

```python
# 录制方案流程：

# 1. AI调用录制工具
tool_record_rpa_template("feishu_login", "browser")

# 2. 启动浏览器（有头模式）
browser = BrowserManager()
await browser.start(headless=False)

# 3. 用户操作时，Playwright自动捕获
# （或使用playwright codegen辅助）

# 4. 停止录制，生成模板
template = recorder.stop_recording()
# {
#   "template_id": "feishu_login",
#   "steps": [
#     {"action": "navigate", "url": "https://feishu.cn"},
#     {"action": "click", "selector": "#login"},
#     {"action": "input", "selector": "#username", "text": "{{username}}"},
#     ...
#   ]
# }

# 5. 保存模板
template_manager.save_template(template)
```

---

## 💡 实际实现建议

### 方案：Playwright Codegen + 自动转换

#### 步骤1：集成playwright codegen

```python
# agent/rpa_tools.py

def tool_record_with_codegen(url: str, template_name: str) -> Dict:
    """使用Playwright codegen录制"""
    import subprocess
    
    # 启动codegen
    process = subprocess.Popen([
        'playwright', 'codegen',
        '--target', 'python-async',
        '--output', f'temp_{template_name}.py',
        url
    ])
    
    return {
        "success": True,
        "message": "✅ 录制窗口已打开！操作完成后关闭窗口即可",
        "process_id": process.pid
    }
```

#### 步骤2：自动转换生成的代码

```python
def convert_codegen_to_template(py_file: str, template_name: str) -> Dict:
    """将codegen生成的Python代码转换为JSON模板"""
    
    # 读取生成的Python代码
    with open(py_file, 'r') as f:
        code = f.read()
    
    # 解析代码，提取操作
    steps = []
    
    # page.goto("https://...") → navigate
    if 'page.goto' in code:
        url = extract_url(code)
        steps.append({"action": "navigate", "url": url})
    
    # page.click("#button") → click
    for match in re.findall(r'page\.click\(["\'](.+?)["\']\)', code):
        steps.append({"action": "click", "selector": match})
    
    # page.fill("#input", "value") → input
    for match in re.findall(r'page\.fill\(["\'](.+?)["\']\s*,\s*["\'](.+?)["\']\)', code):
        selector, value = match
        steps.append({"action": "input", "selector": selector, "text": value})
    
    # 生成模板
    template = {
        "template_id": template_name,
        "name": template_name,
        "type": "browser",
        "steps": steps,
        "parameters": extract_parameters(steps)
    }
    
    return template
```

---

## 🎉 最终推荐方案

### 不需要开发浏览器插件！

**推荐使用：**
1. ✅ **Playwright内置功能**（codegen命令）
2. ✅ **自动转换工具**（Python代码 → JSON模板）
3. ✅ **事件监听**（CDP协议，可选）

**优点：**
- 无需插件开发
- 无需用户安装插件
- 开发成本低
- 维护简单
- 官方支持

**实现步骤：**
1. 用户对AI说："录制飞书登录"
2. 系统运行：`playwright codegen https://feishu.cn`
3. 用户操作浏览器
4. 关闭窗口后，自动转换生成的代码为JSON模板
5. 保存到 `rpa_templates/feishu_login.json`
6. 完成！

---

## 📊 对比总结

| 方案 | 开发难度 | 用户体验 | 维护成本 | 推荐度 |
|------|---------|---------|---------|--------|
| Chrome插件 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ❌ 不推荐 |
| Playwright Codegen | ⭐⭐ | ⭐⭐⭐⭐ | ⭐ | ✅✅✅ 强烈推荐 |
| CDP事件监听 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ✅✅ 可选 |

**结论：使用Playwright内置的codegen功能 + 自动转换脚本即可，无需开发浏览器插件！** 🎯
