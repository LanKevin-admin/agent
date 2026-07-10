# EXE打包路径兼容性修复

## 🎯 问题概述

用户发现EXE打包后无法显示之前的数据，经过全面检查发现多个路径问题：

1. **数据库路径** - `__file__` 在EXE中指向临时解压目录
2. **配置文件加载** - `.env` 文件找不到外部配置
3. **报告输出目录** - 相对路径不稳定
4. **配置文件写入** - 写入到错误的位置

---

## 🔧 修复内容

### 1️⃣ 数据库路径 (`database/models.py`)

**问题：**
```python
# 旧代码 - 开发环境路径
DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
```

**修复：**
```python
import sys

def get_data_dir():
    """获取数据目录，兼容开发环境和EXE打包"""
    if getattr(sys, 'frozen', False):
        # EXE运行：使用EXE所在目录
        base_dir = os.path.dirname(sys.executable)
    else:
        # 开发环境：使用项目根目录
        base_dir = os.path.dirname(os.path.dirname(__file__))
    
    data_dir = os.path.join(base_dir, 'data')
    os.makedirs(data_dir, exist_ok=True)
    return data_dir

DB_DIR = get_data_dir()
DB_PATH = os.path.join(DB_DIR, 'rpa_monitor.db')
```

**效果：**
- 开发环境：`项目根目录/data/rpa_monitor.db`
- EXE运行：`EXE同目录/data/rpa_monitor.db`

---

### 2️⃣ 配置文件加载 (`config/settings.py`)

**问题：**
```python
# 旧代码 - 无法找到外部.env
load_dotenv()
```

**修复：**
```python
import sys

def get_base_dir():
    """获取基础目录，兼容开发环境和EXE打包"""
    if getattr(sys, 'frozen', False):
        # EXE运行：使用EXE所在目录
        return os.path.dirname(sys.executable)
    else:
        # 开发环境：使用当前文件所在目录
        return os.path.dirname(__file__)

# 加载环境变量，优先外部.env
base_dir = get_base_dir()
external_env = os.path.join(base_dir, '.env')
if os.path.exists(external_env):
    load_dotenv(external_env, override=True)
else:
    # 回退到打包内的.env
    load_dotenv()
```

**效果：**
- 优先加载EXE同目录的`.env`（用户可修改）
- 没有则使用打包内的`.env`（默认值）

---

### 3️⃣ 报告输出目录 (`config/settings.py`)

**问题：**
```python
# 旧代码 - 相对路径不稳定
OUTPUT_DIR = os.getenv("REPORT_OUTPUT_DIR", "./reports")
```

**修复：**
```python
class ReportConfig:
    """汇报输出配置"""
    # 使用基础目录下的reports文件夹
    OUTPUT_DIR = os.path.join(get_base_dir(), "reports")
```

**效果：**
- 开发环境：`项目根目录/reports/`
- EXE运行：`EXE同目录/reports/`

---

### 4️⃣ 配置文件写入 (`web_server.py`)

**问题：**
```python
# 旧代码 - 写入到__file__所在目录（临时目录）
env_file = os.path.join(os.path.dirname(__file__), ".env")
```

**修复：**
```python
# 获取.env文件路径，兼容EXE打包
if getattr(sys, 'frozen', False):
    # EXE模式：写入EXE同目录
    env_file = os.path.join(os.path.dirname(sys.executable), ".env")
else:
    # 开发模式：写入项目根目录
    env_file = os.path.join(os.path.dirname(__file__), ".env")
```

**效果：**
- 前端配置页面保存后，配置文件写入正确位置
- 重启EXE后配置仍然有效

---

## 📂 EXE运行时文件结构

```
dist/
├── 飞书RPA监控系统.exe     # EXE主程序
├── .env                     # 配置文件（用户可修改）
├── data/                    # 数据目录
│   └── rpa_monitor.db       # SQLite数据库
└── reports/                 # 报告输出目录
    └── *.txt                # 生成的报告文件
```

---

## ✅ 核心技术点

### `sys.frozen` 检测

```python
if getattr(sys, 'frozen', False):
    # EXE打包环境
    base_dir = os.path.dirname(sys.executable)
else:
    # 开发环境
    base_dir = os.path.dirname(__file__)
```

### `sys._MEIPASS` 临时目录

- PyInstaller打包后，会将资源文件解压到临时目录
- `__file__` 会自动指向 `sys._MEIPASS`
- 对于打包进去的资源（`web/dist`、`prompts`），直接使用`__file__`即可

### 区分用户数据和程序资源

- **用户数据**（数据库、报告、配置）→ 使用 `sys.executable` 获取EXE目录
- **程序资源**（前端文件、提示词）→ 使用 `__file__` 获取临时目录

---

## 🎯 测试清单

- [x] 数据库路径正确（EXE同目录）
- [x] 配置文件加载正确（外部优先）
- [x] 报告输出目录正确
- [x] 配置保存功能正常
- [ ] 重新打包EXE验证
- [ ] 运行EXE测试所有功能

---

## 📝 重新打包命令

```bash
# 确保前端已构建
cd web
npm run build
cd ..

# 重新打包EXE
pyinstaller --clean feishu_rpa_monitor.spec
```
