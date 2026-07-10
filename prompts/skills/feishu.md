## Skill: 飞书消息处理

### 能力
- 从飞书群拉取指定时间范围的消息
- 过滤出RPA运行日志（排除闲聊、表情包）
- 向飞书群发送报告消息

### 可用工具
- `fetch_messages` - 拉取消息，支持日期和时间范围过滤
- `filter_rpa_logs` - 智能识别RPA日志
- `send_feishu_message` - 发送消息到飞书群

### 使用建议
- 时间过滤可选，不指定start_time/end_time则查询全天
- filter_rpa_logs会自动排除无效消息（emoji、闲聊等）
