# RPA自动化方案 - AI指挥 + 模板执行

## 🎯 方案设计

### 核心思想

**不让AI分析页面（不稳定），而是让AI调用预定义的RPA模板（稳定）**

```
传统方案（不稳定）：
用户 → AI分析页面 → AI判断元素 → 操作 ❌ 页面变化就挂

我们的方案（稳定）：
用户 → AI理解意图 → 匹配模板 → RPA执行固定步骤 ✅ 稳定可靠
```

---

## 🏗️ 架构设计

### 三层架构

```
┌─────────────────────────────────────────┐
│  对话层（AI）                            │
│  - 理解用户意图                          │
│  - 提取参数                              │
│  - 匹配RPA模板                           │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│  模板层（预定义流程）                    │
│  - 登录模板                              │
│  - 查询模板                              │
│  - 导出模板                              │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│  执行层（Playwright/Selenium）           │
│  - 浏览器自动化                          │
│  - 元素定位                              │
│  - 数据提取                              │
└─────────────────────────────────────────┘
```

---

## 📋 RPA模板格式

### 模板示例

```json
{
  "template_id": "feishu_login",
  "name": "飞书后台登录",
  "description": "登录飞书管理后台",
  "parameters": {
    "username": {"type": "string", "required": true},
    "password": {"type": "string", "required": true}
  },
  "steps": [
    {
      "action": "navigate",
      "url": "https://open.feishu.cn",
      "wait": 2
    },
    {
      "action": "input",
      "selector": "#username",
      "value": "{{username}}",
      "description": "输入用户名"
    },
    {
      "action": "input",
      "selector": "#password",
      "value": "{{password}}",
      "description": "输入密码"
    },
    {
      "action": "click",
      "selector": "button[type='submit']",
      "description": "点击登录"
    },
    {
      "action": "wait_for_navigation",
      "timeout": 10000
    },
    {
      "action": "verify",
      "selector": ".user-avatar",
      "description": "验证登录成功"
    }
  ],
  "output": {
    "success": true,
    "cookies": "save_to_session"
  }
}
```

---

## 🎮 使用流程

### 场景1：简单查询

```
用户：帮我登录飞书查询今天的审批单

AI分析：
  1. 需要执行的操作：登录 → 查询
  2. 匹配模板：
     - feishu_login（需要参数：username, password）
     - feishu_query_approvals（需要参数：date_range）
  3. 提取参数：
     - date_range = "今天"
  
AI询问：
  "我理解你想登录飞书查询今天的审批单。
   请提供飞书账号密码，或使用已保存的凭证？"

用户：用已保存的凭证

AI执行：
  1. 调用 feishu_login（使用保存的凭证）
  2. 等待登录成功
  3. 调用 feishu_query_approvals（date="today"）
  4. 返回查询结果

AI回复：
  "✅ 查询完成！今天共有15条审批单：
   - 待审批：5条
   - 已通过：8条
   - 已拒绝：2条
   
   详细数据已导出到 reports/approvals_20260710.xlsx"
```

---

## 🔧 技术选型

### 推荐：Playwright（微软开源）

**优点：**
- ✅ 现代化（支持最新浏览器特性）
- ✅ 稳定（自动等待元素）
- ✅ 快速（支持并发）
- ✅ 跨浏览器（Chrome/Firefox/Edge/Safari）
- ✅ Python原生支持

**安装：**
```bash
pip install playwright
playwright install chromium
```

---

## 📝 代码结构

```
feishu_rpa_monitor/
├── rpa/
│   ├── __init__.py
│   ├── executor.py           # RPA执行引擎
│   ├── browser_manager.py    # 浏览器管理
│   ├── template_loader.py    # 模板加载器
│   └── actions.py            # 基础动作库
├── rpa_templates/            # RPA模板目录
│   ├── feishu_login.json
│   ├── feishu_query_approvals.json
│   └── database_query.json
└── agent/
    └── rpa_tools.py          # AI调用的RPA工具
```

---

## 🎯 AI的职责

### 只做3件事

1. **理解意图**
   ```python
   用户："帮我登录飞书查询今天的数据"
   AI识别：需要 [登录] + [查询] 操作
   ```

2. **匹配模板**
   ```python
   AI选择：
   - feishu_login 模板
   - feishu_query_data 模板
   ```

3. **提取参数**
   ```python
   AI提取：
   - template: "feishu_login"
   - params: {"username": "xxx", "password": "***"}
   
   - template: "feishu_query_data"
   - params: {"date": "today"}
   ```

**不做：**
- ❌ 不分析页面结构
- ❌ 不判断元素位置
- ❌ 不处理页面变化

---

## 🛡️ 稳定性保证

### 1. 模板固化

```json
{
  "steps": [
    {
      "action": "click",
      "selector": "#submit-btn",
      "fallback_selectors": [
        "button[type='submit']",
        ".submit-button",
        "//button[text()='提交']"
      ],
      "description": "点击提交按钮"
    }
  ]
}
```

### 2. 智能重试

```python
# 自动重试机制
max_retries = 3
retry_interval = 2  # 秒

if action_fails:
    retry with fallback_selector
    wait and retry
    take screenshot and report
```

### 3. 验证机制

```python
# 每步都验证
after_login:
    verify user_avatar exists
    verify url contains "/dashboard"
    verify no error_message

if verification_fails:
    return detailed_error
```

---

## 🚀 快速开始

### 第一步：创建简单模板

```json
{
  "template_id": "simple_search",
  "name": "百度搜索",
  "parameters": {
    "keyword": {"type": "string", "required": true}
  },
  "steps": [
    {"action": "navigate", "url": "https://www.baidu.com"},
    {"action": "input", "selector": "#kw", "value": "{{keyword}}"},
    {"action": "click", "selector": "#su"},
    {"action": "wait", "seconds": 2},
    {"action": "screenshot", "filename": "search_result.png"}
  ]
}
```

### 第二步：AI调用

```
用户：百度搜索"飞书开放平台"

AI：
  1. 匹配模板：simple_search
  2. 提取参数：keyword="飞书开放平台"
  3. 调用RPA执行
  4. 返回截图
```

---

## 💡 高级功能

### 1. 链式执行

```
模板A（登录）→ 模板B（查询）→ 模板C（导出）
```

### 2. 条件分支

```json
{
  "action": "if",
  "condition": "element_exists('.error')",
  "then": [
    {"action": "screenshot"},
    {"action": "return_error"}
  ],
  "else": [
    {"action": "continue"}
  ]
}
```

### 3. 数据提取

```json
{
  "action": "extract_data",
  "selector": "table.data-table",
  "fields": {
    "name": "td:nth-child(1)",
    "status": "td:nth-child(2)",
    "date": "td:nth-child(3)"
  },
  "output": "approvals_data"
}
```

---

**下一步：我帮你实现完整的RPA框架代码？** 🚀
