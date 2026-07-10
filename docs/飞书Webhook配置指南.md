# 飞书Webhook配置指南 - 实时响应模式

## 🚀 为什么要用Webhook？

### 对比两种模式

| 特性 | 轮询模式（当前） | Webhook模式（推荐） |
|------|----------------|-------------------|
| **响应速度** | 10秒延迟 | <1秒（实时） |
| **资源消耗** | 高（持续调用API） | 低（仅接收推送） |
| **API配额** | 消耗配额 | 不消耗配额 |
| **配置难度** | 简单 | 中等 |
| **服务器要求** | 无 | 需要公网IP或内网穿透 |

### 适用场景

**✅ 推荐使用Webhook：**
- 服务器有公网IP
- 需要实时响应
- 消息量大
- 关注用户体验

**⚠️ 继续使用轮询：**
- 服务器在内网（无公网IP）
- 不想配置内网穿透
- 消息量小，延迟可接受

---

## 📝 Webhook配置步骤

### 1. 确认服务器可访问

**选项A：有公网IP**
```bash
# 确认端口开放
curl http://你的公网IP:8888/api/health
```

**选项B：内网穿透（推荐使用ngrok或frp）**
```bash
# 使用ngrok（需要注册账号）
ngrok http 8888

# 会得到一个公网URL，类似：
# https://abc123.ngrok.io
```

### 2. 登录飞书开放平台

访问：https://open.feishu.cn/app

选择你的应用

### 3. 配置事件订阅

**步骤：**
1. 点击左侧「事件订阅」
2. 启用「事件订阅」
3. 请求地址配置：
   ```
   http://你的公网IP:8888/api/feishu/webhook
   
   或（使用ngrok）：
   https://abc123.ngrok.io/api/feishu/webhook
   ```

4. 点击「验证」按钮
   - ✅ 看到"验证成功"
   - ❌ 验证失败？查看下方排查指南

### 4. 订阅事件

在「添加事件」中搜索并添加：

**必选事件：**
- ✅ `im.message.receive_v1` - 接收消息

**可选事件：**
- `im.message.message_read_v1` - 消息已读（可用于阅读统计）

### 5. 发布版本

配置完成后，点击「创建版本」→「全员发布」

---

## 🧪 测试Webhook

### 方法1：直接测试

```bash
# 在群里@机器人
@机器人 你好

# 应该立即收到回复（<1秒）
```

### 方法2：查看日志

```bash
# 查看web_server.py输出
# 应该看到：
# [Webhook] 收到飞书事件: event_callback
# [Webhook] 检测到@消息: 你好...
# [Webhook] 已回复消息: om_xxx...
```

### 方法3：手动发送测试请求

```bash
curl -X POST http://localhost:8888/api/feishu/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "type": "url_verification",
    "challenge": "test123",
    "token": "your_token"
  }'

# 应该返回：
# {"challenge": "test123"}
```

---

## ⚙️ 切换到Webhook模式

### 选项A：完全替代轮询（推荐）

编辑 `web_server.py`，注释掉轮询启动：

```python
# 在startup_event中：
# start_message_monitor(agent, interval=10)  # 注释掉
logger.info("[WebServer] 使用Webhook模式，不启动轮询")
```

### 选项B：双模式并存

保持当前配置不变，Webhook和轮询同时工作：
- Webhook处理实时消息
- 轮询作为备份（防止Webhook漏消息）

---

## 🔧 故障排查

### 问题1：URL验证失败

**原因：**
- 服务器无法访问
- 端口未开放
- 防火墙阻拦

**解决：**
```bash
# 检查服务是否运行
curl http://localhost:8888/api/health

# 检查防火墙
# Windows:
netsh advfirewall firewall add rule name="RPA Monitor" dir=in action=allow protocol=TCP localport=8888

# Linux:
sudo ufw allow 8888
```

### 问题2：收到事件但没回复

**原因：**
- 没有@机器人
- 机器人权限不足
- Agent处理出错

**解决：**
```bash
# 查看日志详细错误
python web_server.py

# 测试Agent
python test_message_monitor.py
```

### 问题3：Webhook URL变化

**场景：** 使用ngrok，每次重启URL都变

**解决方案：**
1. **ngrok付费版**：固定域名
2. **使用frp**：自建内网穿透，固定域名
3. **使用固定公网IP**

---

## 📊 性能对比

### 轮询模式

```
消息发送 → 等待10秒 → 检测到 → 处理 → 回复
总耗时：10-20秒
API调用：每10秒1次（无论是否有消息）
```

### Webhook模式

```
消息发送 → 推送到服务器 → 处理 → 回复
总耗时：<1秒
API调用：0（仅接收推送）
```

---

## 🔐 安全建议

### 1. 验证请求来源

在 `.env` 中添加：
```env
FEISHU_VERIFICATION_TOKEN=你的验证令牌
FEISHU_ENCRYPT_KEY=你的加密密钥
```

获取方式：飞书开放平台 → 应用凭证

### 2. 使用HTTPS

生产环境建议使用HTTPS + 域名：
```bash
# 使用nginx反向代理
# 配置SSL证书（Let's Encrypt免费）
```

### 3. 限流

防止恶意请求：
```python
# 可以添加限流中间件
from slowapi import Limiter
limiter = Limiter(key_func=lambda: request.client.host)

@app.post("/api/feishu/webhook")
@limiter.limit("100/minute")  # 每分钟最多100次
async def feishu_webhook(...):
    ...
```

---

## 💡 最佳实践

### 1. 双模式部署

- **生产环境**：使用Webhook（实时响应）
- **开发/内网**：使用轮询（无需配置）

### 2. 监控告警

记录Webhook调用次数和失败率：
```python
# 可以添加到数据库
webhook_calls_total = 0
webhook_calls_failed = 0
```

### 3. 日志管理

Webhook日志独立输出：
```python
webhook_logger = logging.getLogger("feishu.webhook")
webhook_logger.setLevel(logging.INFO)
```

---

## 📚 相关文档

- [飞书事件订阅官方文档](https://open.feishu.cn/document/ukTMukTMukTM/uUTNz4SN1MjL1UzM)
- [飞书消息卡片](https://open.feishu.cn/document/ukTMukTMukTM/uczM3QjL3MzN04yNzcDN)
- [ngrok使用指南](https://ngrok.com/docs)

---

## ✅ 配置检查清单

- [ ] 服务器有公网IP或已配置内网穿透
- [ ] 端口8888已开放
- [ ] 飞书开放平台已配置Webhook URL
- [ ] 已订阅 `im.message.receive_v1` 事件
- [ ] URL验证通过
- [ ] 版本已发布
- [ ] 测试消息能实时响应

---

**配置完成后，群里@机器人即可实时响应！** 🎉
