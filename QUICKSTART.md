# ⚡ 快速启动指南（开发者版）

克隆项目后快速启动的完整步骤。

---

## 📋 前置要求

- **Python 3.8+**
- **Node.js 16+**
- **Git**

---

## 🚀 5步快速启动

### 1️⃣ 克隆项目

```bash
git clone https://github.com/LanKevin-admin/agent.git
cd agent
```

### 2️⃣ 配置环境变量

```bash
# 复制配置模板
copy .env.example .env

# 编辑.env文件，最少填写以下内容：
# AI_API_KEY=你的DeepSeek API Key
# AI_API_BASE=https://api.deepseek.com
# AI_MODEL=deepseek-chat
```

**Windows：** 使用记事本或VS Code编辑`.env`文件

**必填配置：**
```env
AI_API_KEY=sk-xxxxxxxxxxxxxxxx  # 从 https://platform.deepseek.com/ 获取
AI_API_BASE=https://api.deepseek.com
AI_MODEL=deepseek-chat
```

**可选配置：**
- 飞书推送：`FEISHU_APP_ID`、`FEISHU_APP_SECRET`、`FEISHU_CHAT_ID`
- 邮件通知：`SMTP_HOST`、`SMTP_USER`、`SMTP_PASSWORD`等
- 企业微信：`WECOM_WEBHOOK`

### 3️⃣ 安装Python依赖

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

**常用依赖：**
- fastapi - Web框架
- uvicorn - ASGI服务器
- sqlalchemy - ORM
- openai - AI SDK
- apscheduler - 定时任务
- pandas - 数据处理

### 4️⃣ 安装前端依赖并构建

```bash
cd web
npm install
npm run build
cd ..
```

**说明：**
- `npm install` 安装Vue、Element Plus等依赖
- `npm run build` 构建生产版本到`web/dist/`
- 后端会自动从`web/dist/`加载前端文件

### 5️⃣ 启动服务

```bash
python web_server.py
```

**启动成功后：**
- 服务会自动打开浏览器
- 访问：http://127.0.0.1:8888
- API文档：http://127.0.0.1:8888/docs

---

## 🔧 开发模式（可选）

如果需要前端热重载开发：

**终端1 - 后端：**
```bash
python web_server.py
```

**终端2 - 前端：**
```bash
cd web
npm run dev
```

然后访问：http://localhost:5173（前端开发服务器）

---

## 📦 打包成EXE（可选）

```bash
# 确保前端已构建
cd web
npm run build
cd ..

# 打包
pyinstaller --clean feishu_rpa_monitor.spec
```

**输出：** `dist/飞书RPA监控系统.exe`（约41MB）

---

## ✅ 验证安装

### 检查后端

```bash
python -c "from agent.skill_based_agent import SkillBasedAgent; print('后端OK')"
```

### 检查前端

确认`web/dist/`目录存在且包含以下文件：
- `index.html`
- `assets/` 文件夹

---

## 🐛 常见问题

### Q: pip install失败

**A: 使用国内镜像源**
```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### Q: npm install很慢

**A: 使用淘宝镜像**
```bash
npm config set registry https://registry.npmmirror.com
npm install
```

### Q: 启动后浏览器无法访问

**A: 检查：**
1. 8888端口是否被占用
2. 防火墙是否拦截
3. 控制台是否有错误信息

### Q: AI功能无法使用

**A: 检查：**
1. `.env`文件中的`AI_API_KEY`是否正确
2. 是否已重启服务器
3. API Key是否有效（访问 https://platform.deepseek.com/ 检查）

### Q: 前端页面是空白的

**A: 检查：**
1. `web/dist/`目录是否存在
2. 是否执行了`npm run build`
3. 浏览器控制台是否有错误

---

## 📝 目录结构

下载后的项目结构：

```
agent/
├── .env.example          # 配置模板 ⭐ 复制为.env
├── .gitignore
├── README.md             # 项目说明
├── requirements.txt      # Python依赖
├── web_server.py         # 启动文件 ⭐
├── agent/                # AI Agent核心
├── skills/               # 9个Skills模块
├── config/               # 配置管理
├── database/             # 数据库
├── feishu/               # 飞书API
├── notify/               # 通知模块
├── report/               # 报告生成
├── scheduler/            # 定时任务
├── web/                  # Vue 3前端
│   ├── src/
│   ├── package.json
│   └── dist/             # 构建输出（执行npm run build后生成）
├── docs/                 # 文档
└── prompts/              # AI提示词
```

---

## 🎯 首次运行流程

1. **克隆项目** → 下载代码
2. **配置.env** → 填写API Key
3. **安装依赖** → Python + Node.js
4. **构建前端** → npm run build
5. **启动服务** → python web_server.py
6. **打开浏览器** → 自动打开或访问 http://127.0.0.1:8888
7. **开始使用** → 访问智能对话页面测试

---

## 📚 更多文档

- [完整使用说明](使用说明.md)
- [项目结构说明](docs/项目结构说明.md)
- [开发指南](docs/开发指南.md)
- [Skills架构](docs/SKILLS_README.md)

---

**预计启动时间：** 5-10分钟（取决于网络速度）

**遇到问题？** 查看[开发指南](docs/开发指南.md)中的调试技巧部分。
