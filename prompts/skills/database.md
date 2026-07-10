## Skill: 数据库查询

### 能力
- 连接MySQL/PostgreSQL/SQLite数据库
- 查询RPA运行记录
- 支持自定义SQL和字段映射

### 可用工具
- `query_rpa_database` - 查询数据库

### 数据库配置格式
```json
{
  "type": "mysql|postgresql|sqlite",
  "host": "localhost",
  "port": 3306,
  "database": "rpa_db",
  "user": "root",
  "password": "xxx",
  "table": "rpa_logs",
  "date_field": "created_at"
}
```

### 字段映射格式
```json
{
  "account": "账号名字段",
  "status": "状态字段",
  "file_path": "文件路径字段",
  "query_range": "查询范围字段"
}
```

### 使用建议
- 首次使用询问用户数据库配置和字段映射
- 成功后建议保存为模板
