# RPA系统快速使用指南

## ✅ 安装完成！

所有依赖已安装：
- ✅ playwright 1.48.0
- ✅ pywinauto 0.6.9
- ✅ playwright-stealth 1.0.6
- ✅ Chromium浏览器

---

## 🚀 快速开始

### 方式1：自动连接（推荐）

```bash
# 1. 启动Chrome调试模式（终端1）
python scripts/start_chrome_debug.py

# 2. 启动Web服务（终端2）
python web_server.py

# 3. 在对话界面测试RPA
浏览器访问: http://localhost:8888
进入"对话"页面，输入：
"列出所有RPA模板"
"执行百度搜索模板，搜索Python"
```

### 方式2：手动启动Chrome

```powershell
# Windows PowerShell
& "C:\Program Files\Google\Chrome\Application\chrome.exe" `
  --remote-debugging-port=9222 `
  --user-data-dir="E:\飞书ai\feishu_rpa_monitor\chrome_rpa_profile"

# 然后RPA会自动连接到这个Chrome
```

---

## 📋 可用的RPA命令

### 1. 列出模板
```
"列出所有RPA模板"
"有哪些RPA模板"
```

### 2. 执行模板
```
"执行百度搜索模板，搜索Playwright"
"运行百度搜索，关键词是Python"
```

### 3. 录制模板（即将支持）
```
"录制一个飞书登录模板"
"开始录制RPA模板"
```

---

## 🎯 功能特性

### ✅ 页面复用
- 不重复启动浏览器
- 保持登录状态
- 保留所有Cookie和会话
- 可以手动+自动混合操作

### ✅ 反检测
- 隐藏webdriver特征
- 模拟真实浏览器环境
- 通过大部分机器人检测

### ✅ 智能修复
- 页面变化自动适应
- 三级降级查找（主选择器→备用→智能搜索）
- 自动生成修复建议

---

## 🧪 测试示例

### 测试1：百度搜索
```bash
# 启动Chrome调试模式
python scripts/start_chrome_debug.py

# 在对话界面输入：
"执行百度搜索模板，搜索Playwright"

# 预期结果：
✅ 浏览器自动打开百度
✅ 自动输入关键词
✅ 自动点击搜索
✅ 截图保存到reports/
```

### 测试2：反检测
```bash
# 在连接的Chrome中访问检测网站：
https://bot.sannysoft.com/

# 预期结果：
✅ WEBDRIVER: false
✅ CHROME: present
✅ PLUGINS: present
✅ 大部分检测为"人类"
```

---

## 📁 目录结构

```
feishu_rpa_monitor/
├── rpa/                           # RPA核心模块
│   ├── executor.py                # 执行引擎
│   ├── browser_manager.py         # 浏览器管理（支持CDP连接）
│   ├── desktop_automation.py      # Windows桌面自动化
│   ├── template_recorder.py       # 模板录制器
│   ├── smart_repairer.py          # 智能修复器
│   └── template_manager.py        # 模板管理器
├── rpa_templates/                 # RPA模板库
│   └── baidu_search.json          # 百度搜索示例
├── agent/
│   └── rpa_tools.py               # AI调用RPA的工具
├── scripts/
│   └── start_chrome_debug.py      # 启动Chrome调试模式
├── chrome_rpa_profile/            # Chrome用户数据（自动创建）
├── rpa_sessions/                  # 会话存储（自动创建）
└── docs/
    ├── RPA自动化方案.md           # 方案设计
    ├── RPA录制流程详解.md         # 录制原理
    └── RPA反检测与页面复用方案.md # 核心技术方案
```

---

## 💡 使用建议

### 日常使用流程

1. **每天启动一次Chrome调试模式**
   ```bash
   python scripts/start_chrome_debug.py
   ```
   - 保持这个窗口运行
   - 所有RPA都在这个浏览器中执行

2. **执行RPA任务**
   - 通过AI对话调用
   - 保持登录状态
   - 可以手动操作混合自动化

3. **定期重启Chrome**
   - 每天或每周重启一次
   - 清理内存
   - 更新Cookie

### 最佳实践

**页面复用：**
- ✅ 优先使用`start_or_connect()`自动连接
- ✅ 保持Chrome运行，维持会话
- ✅ 定期清理浏览器缓存

**反检测：**
- ✅ 使用真实的user-data-dir（有历史记录）
- ✅ 不使用无头模式（headless=False）
- ✅ 添加随机延迟（模拟人类操作）

**模板管理：**
- ✅ 为重要元素配置备用选择器
- ✅ 定期测试和更新模板
- ✅ 利用智能修复功能

---

## 🔧 故障排除

### 问题1：连接Chrome失败
```
错误：连接失败: Cannot connect to CDP endpoint

解决：
1. 确认Chrome已启动（远程调试模式）
2. 检查端口9222是否被占用
3. 尝试手动启动：
   python scripts/start_chrome_debug.py
```

### 问题2：找不到元素
```
错误：选择器失效

解决：
1. 检查页面是否变化
2. RPA会自动尝试备用选择器
3. 智能修复会提供修复建议
4. 根据建议更新模板
```

### 问题3：被检测为机器人
```
错误：网站提示"检测到自动化"

解决：
1. 确保启用了stealth模式
2. 使用真实user-data-dir
3. 添加随机延迟
4. 避免高频操作
```

---

## 📖 相关文档

- [RPA自动化方案](./RPA自动化方案.md) - 完整方案设计
- [RPA录制流程详解](./RPA录制流程详解.md) - 录制原理
- [RPA反检测与页面复用方案](./RPA反检测与页面复用方案.md) - 核心技术

---

## 🎉 开始使用

```bash
# 一键启动
python scripts/start_chrome_debug.py

# 等待提示：
# ✅ Chrome已启动！
# 📡 CDP地址: http://localhost:9222
# 💡 RPA将自动连接到此浏览器

# 然后在对话界面测试：
"列出所有RPA模板"
"执行百度搜索模板"
```

**祝你使用愉快！** 🚀
