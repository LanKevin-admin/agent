# 飞书RPA监控系统 - Skills架构说明

> 参考OpenClaw设计，采用模块化Skills架构 + MD提示词分离

---

## 🎯 架构设计

```
┌─────────────────────────────────────┐
│         SkillBasedAgent            │
│  (核心Agent，协调所有Skills)        │
└──────────────┬──────────────────────┘
               │
         ┌─────▼─────┐
         │  Skill    │
         │  Manager  │
         └─────┬─────┘
               │
     ┌─────────┼─────────┐
     │         │         │
  ┌──▼──┐  ┌──▼──┐  ┌──▼──┐
  │Skill│  │Skill│  │Skill│ ...
  └─────┘  └─────┘  └─────┘
```

---

## 📦 Skills列表

| Skill名称 | 功能描述 | 提示词文件 |
|-----------|----------|-----------|
| `feishu` | 飞书消息拉取、过滤、发送 | `prompts/skills/feishu.md` |
| `file_validation` | 文件存在性、时间、日期校验 | `prompts/skills/file_validation.md` |
| `database` | MySQL/PostgreSQL/SQLite查询 | `prompts/skills/database.md` |
| `notification` | 邮件、企业微信通知 | `prompts/skills/notification.md` |
| `report` | 简洁汇总报告生成 | `prompts/skills/report.md` |
| `config` | 配置管理、模板保存/加载 | `prompts/skills/config.md` |

---

## 📝 提示词文件结构

```
prompts/
├── system_prompt.md          # 系统主提示词
└── skills/                   # 各Skill的提示词片段
    ├── feishu.md
    ├── file_validation.md
    ├── database.md
    ├── notification.md
    ├── report.md
    └── config.md
```

### 提示词加载流程

1. Agent启动时加载`system_prompt.md`（基础提示词）
2. Skill Manager遍历所有启用的Skills
3. 每个Skill从`prompts/skills/{skill_name}.md`加载自己的提示词片段
4. 合并成完整的系统提示词

---

## 🛠️ 如何添加新Skill

### 步骤1：创建Skill类

在`skills/`目录下创建`your_skill.py`：

```python
from skills.base_skill import BaseSkill

class YourSkill(BaseSkill):
    def get_name(self) -> str:
        return "your_skill"
    
    def get_description(self) -> str:
        return "你的Skill描述"
    
    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "your_tool",
                    "description": "工具描述",
                    "parameters": {...}
                }
            }
        ]
    
    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]):
        if tool_name == "your_tool":
            # 执行逻辑
            return {"result": "success"}
```

### 步骤2：创建提示词文件

在`prompts/skills/`下创建`your_skill.md`：

```markdown
## Skill: 你的Skill名称

### 能力
- 功能1
- 功能2

### 可用工具
- `your_tool` - 工具描述

### 使用建议
- 建议1
- 建议2
```

### 步骤3：注册Skill

在`agent/skill_based_agent.py`的`_register_skills()`中添加：

```python
self.skill_manager.register_skill(YourSkill())
```

完成！Agent会自动加载你的Skill和提示词。

---

## 🎨 优势对比

### ❌ 旧架构（单体Agent）

```python
# agent/rpa_agent.py (500+ 行)
class RPAAgent:
    def _register_tools(self):
        # 所有工具定义写在一起
        return [tool1, tool2, tool3, ...]  # 100+ 行
    
    def _register_handlers(self):
        # 所有工具实现混在一起
        from agent.tools import ...
        from agent.db_tools import ...
        from agent.config_tools import ...
```

**问题：**
- 代码耦合严重
- 提示词硬编码在代码里
- 难以扩展和维护
- 修改提示词需要改代码

### ✅ 新架构（Skills + MD）

```
skills/
  ├── feishu_skill.py        (60行)
  ├── database_skill.py      (50行)
  └── ...
prompts/
  ├── system_prompt.md
  └── skills/
      ├── feishu.md
      └── database.md
```

**优势：**
- ✅ 模块化：每个Skill独立文件
- ✅ 提示词分离：MD文件独立管理
- ✅ 易扩展：新增Skill只需3步
- ✅ 易调试：单独测试每个Skill
- ✅ 易维护：修改提示词不动代码

---

## 🚀 使用示例

### 使用新Agent

```python
from agent.skill_based_agent import SkillBasedAgent

agent = SkillBasedAgent()
result = agent.run("分析今天的RPA日志")
```

### 列出所有Skills

```python
skills = agent.list_skills()
# [
#   {"name": "feishu", "description": "...", "enabled": True, "tools_count": 3},
#   {"name": "database", "description": "...", "enabled": True, "tools_count": 1},
#   ...
# ]
```

### 禁用/启用Skill

```python
agent.disable_skill("database")  # 暂时不用数据库查询
agent.enable_skill("database")   # 重新启用
```

---

## 📋 迁移指南

### 从旧Agent迁移到新Agent

1. **修改main.py**：
   ```python
   # 旧：
   from agent.rpa_agent import RPAAgent
   agent = RPAAgent()
   
   # 新：
   from agent.skill_based_agent import SkillBasedAgent
   agent = SkillBasedAgent()
   ```

2. **修改web_server.py**：
   ```python
   # 旧：
   from agent.rpa_agent import RPAAgent
   
   # 新：
   from agent.skill_based_agent import SkillBasedAgent
   ```

3. **其他代码无需改动**，接口完全兼容！

---

## 🎯 最佳实践

1. **提示词迭代**：
   - 直接编辑MD文件调整提示词
   - 不需要重启Python，只需重新加载Agent

2. **调试单个Skill**：
   ```python
   skill = FeishuSkill()
   result = skill.execute_tool("fetch_messages", {...})
   ```

3. **自定义Skill组合**：
   ```python
   # 只启用需要的Skills
   agent.disable_skill("database")
   agent.disable_skill("notification")
   ```

4. **提示词版本管理**：
   - 提示词是MD文件，可以Git管理
   - 方便团队协作和版本回滚

---

## 📚 参考资料

- [OpenClaw GitHub](https://github.com/OpenClaw/openclaw) - 参考架构
- [OpenAI Function Calling](https://platform.openai.com/docs/guides/function-calling) - 工具调用规范

---

## 🔧 技术栈

- **核心框架**：Python 3.8+
- **AI模型**：DeepSeek (兼容OpenAI SDK)
- **架构模式**：Skills + MD Prompts
- **设计理念**：模块化、可扩展、易维护
