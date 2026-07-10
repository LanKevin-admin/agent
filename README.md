# 🚀 飞书RPA监控系统

一个基于AI的RPA监控系统，通过自然语言对话实现日志分析、报告生成、定时任务管理等功能。

## ✨ 核心特性

- **🤖 智能对话** - 通过自然语言与AI交互，无需复杂操作
- **📊 自动分析** - AI自动分析RPA日志，识别问题和趋势
- **📅 定时任务** - AI自动生成Cron表达式，智能调度
- **📧 多渠道通知** - 支持飞书、邮件、企业微信推送
- **📈 可视化界面** - Vue 3前端，Element Plus组件库
- **💾 数据持久化** - SQLite数据库存储对话和任务
- **📦 单文件分发** - 打包成EXE，开箱即用

---

## 🚀 快速开始

### 用户版（EXE分发包）

**下载并解压分发包后：**


---

## ⚡ 快速启动（3步）

### 1️⃣ 双击运行

双击 **`飞书RPA监控系统.exe`**

程序会自动：
- 创建数据文件夹
- 初始化数据库
- 启动Web服务器
- **自动打开浏览器**

### 2️⃣ 配置AI

访问配置页面（浏览器会自动打开）

**最少只需填写3项：**
- AI API Key（DeepSeek）
- API Base：`https://api.deepseek.com`
- 模型：`deepseek-chat`

点击"保存配置"

### 3️⃣ 重启生效

关闭程序窗口，重新双击EXE启动

开始使用智能对话功能！🎉

---

## 🔑 获取DeepSeek API Key

1. 访问：https://platform.deepseek.com/
2. 注册/登录账号
3. 进入"API Keys"页面
4. 点击"创建新密钥"
5. 复制密钥，填入配置页面

**费用说明：** 新用户送免费额度，按实际使用量计费

---

## 📖 开发者版（源码）

### 快速启动

**5步启动：** 查看 [快速启动指南](QUICKSTART.md)

```bash
# 1. 克隆项目
git clone https://github.com/LanKevin-admin/agent.git
cd agent

# 2. 配置环境
copy .env.example .env
# 编辑.env填写DeepSeek API Key

# 3. 安装Python依赖
pip install -r requirements.txt

# 4. 构建前端
cd web
npm install
npm run build
cd ..

# 5. 启动服务
python web_server.py
```

访问：http://127.0.0.1:8888

### 打包EXE

```bash
# 1. 构建前端
cd web
npm run build
cd ..

# 2. 打包EXE
pyinstaller --clean feishu_rpa_monitor.spec
```

**输出：** `dist/飞书RPA监控系统.exe`

---

## 📚 文档导航

| 文档 | 说明 | 适用对象 |
|------|------|----------|
| [使用说明](使用说明.md) | 详细使用教程 | 用户 |
| [项目结构说明](docs/项目结构说明.md) | 完整的项目架构 | 开发者 |
| [开发指南](docs/开发指南.md) | 开发流程和规范 | 开发者 |
| [SKILLS架构](docs/SKILLS_README.md) | Skills设计详解 | 开发者 |
| [分发包制作](docs/分发包制作指南.md) | 打包和分发流程 | 开发者 |
| [EXE打包说明](docs/EXE打包完成.md) | PyInstaller配置 | 开发者 |
| [路径兼容性](docs/EXE路径兼容性修复.md) | 路径问题解决 | 开发者 |
| [数据库集成](docs/SQLite数据库集成完成.md) | 数据库设计 | 开发者 |
| [智能功能指南](docs/智能功能使用指南.md) | AI功能教程 | 用户 |

---

## 🏗️ 技术架构

### 后端

- **FastAPI** - 现代化Web框架
- **SQLAlchemy** - ORM + SQLite数据库
- **OpenAI SDK** - AI对话（DeepSeek兼容）
- **APScheduler** - 定时任务调度
- **PyInstaller** - 打包成EXE

### 前端

- **Vue 3** - Composition API + `<script setup>`
- **Element Plus** - UI组件库
- **Vue Router** - Hash路由
- **axios** - HTTP请求
- **Vite** - 构建工具

### AI架构

- **Skills模式** - 参考OpenClaw设计
- **Tool-Use** - OpenAI function calling
- **9个Skills** - 模块化功能封装
- **22+工具函数** - 自动注册和路由

---

## 📁 项目结构

```
feishu_rpa_monitor/
├── agent/              # AI Agent核心
├── skills/             # 9个Skills模块
├── config/             # 配置管理
├── database/           # 数据库（SQLite）
├── feishu/             # 飞书API
├── notify/             # 通知（邮件、企微）
├── report/             # 报告生成
├── scheduler/          # 定时任务
├── web/                # Vue 3前端
│   ├── src/
│   │   ├── views/      # 7个页面
│   │   └── components/ # 可复用组件
│   └── dist/           # 构建输出
├── web_server.py       # FastAPI后端
├── requirements.txt    # Python依赖
└── feishu_rpa_monitor.spec  # 打包配置
```

---

## 🎯 典型使用场景

### 场景1：每日自动分析

```
你：每天下午4点帮我分析今天的日志并发邮件
AI：收到！已创建定时任务，每天16:00执行 ✅
```

### 场景2：即时查询

```
你：分析今天的日志，重点看有没有失败的
AI：正在分析...
    今天共执行23个任务，其中2个失败...
```

### 场景3：报告生成

```
你：生成本周的汇总报告发给领导
AI：正在生成报告...
    报告已生成并发送到邮箱 ✅
```

---

## ⚠️ 注意事项

1. **首次启动需要配置AI** - 否则无法使用智能功能
2. **保持程序运行** - 定时任务需要程序持续运行
3. **防火墙提示** - 首次运行可能提示防火墙，请允许
4. **端口占用** - 程序使用8888端口，确保没有其他程序占用

---

## 🆘 常见问题

### 程序无法启动
- 检查是否有杀毒软件拦截
- 尝试"以管理员身份运行"

### 浏览器无法访问
- 检查8888端口是否被占用
- 防火墙是否拦截

### 配置保存后不生效
- 需要重启程序才能加载新配置
- 确保配置项填写正确

查看详细的 [使用说明](使用说明.md) 了解更多

---

## 📄 许可证

本项目为内部使用，版权所有。

---

## 🙏 致谢

- **OpenAI** - GPT模型和Tool-Use设计
- **DeepSeek** - 高性价比的AI API
- **FastAPI** - 现代化的Python Web框架
- **Vue.js** - 渐进式前端框架
- **Element Plus** - 优秀的Vue组件库

---

**开始体验智能RPA监控！** 🚀
