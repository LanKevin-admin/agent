"""
RPA监控Agent - 核心Agent引擎
基于大模型的Tool-Use Agent，具备：
1. 理解用户自然语言指令（如"查询最近7天的日志"）
2. 自主规划任务链
3. 调用工具执行（拉取日志、分析内容、校验文件、推送报告）
4. 多轮对话 + 记忆
"""
import logging
from typing import List, Dict, Any, Callable
import json
from datetime import datetime
from openai import OpenAI
from config.settings import config

logger = logging.getLogger(__name__)

# Agent系统提示词
SYSTEM_PROMPT = """你是一个RPA运维监控Agent，负责分析RPA运行日志。支持多种数据源和智能配置。
当前日期：{today}

你的核心能力：
1. **智能配置助手**：用户可以用自然语言告诉你配置信息，你调用update_config自动写入配置文件
   - 例如："帮我配置飞书，App ID是cli_xxx，App Secret是xxx"
   - 例如："更新AI的API Key为sk-xxx"

2. **多数据源支持**：
   - 从飞书群拉取日志（fetch_messages）
   - 从数据库读取RPA记录（query_rpa_database）
   - 用户可以指定使用哪个数据源

3. **流程模板固化**：
   - 当用户对某次分析满意时，询问是否保存为模板
   - 调用save_analysis_template保存（包括数据源、SQL、字段映射等）
   - 下次可以直接"使用xxx模板分析"，调用load_analysis_template加载

4. **智能日志分析**：
   - 理解用户指令确定时间范围
   - 识别RPA日志（区分闲聊、表情包）
   - 提取结构化信息（账号、状态、文件路径等）
   - 校验文件存在性和日期一致性
   - 统计成功率和失败原因

5. **简洁汇报生成**：
   - 调用generate_executive_report生成简洁汇总（成功率+失败情况+TXT附件）
   - 推送到企业微信/飞书/邮件

6. **根据分析结果决定推送策略**（正常→业务邮箱，异常→技术邮箱）

RPA日志格式示例：
```
xxxx账号
登录成功
流水查询范围：2026-05-01,2026-06-01
查询成功流水保存路径：C:\\xxxx-20260501-20260601-流水.xlsx
退出成功
```

分析时注意：
- 登录失败要提取具体原因（密码错误、页面卡顿、超时等）
- 所有文件路径都要通过validate_file或validate_multiple_files工具逐一校验
- 调用validate_file时必须传入expected_date_range参数（从日志中提取的查询范围），以校验文件名日期一致性
- 日志说"成功"但文件不存在，要标记为异常
- 文件名中的日期与日志查询范围不一致，也要标记为异常
- 无数据查询也要确认截图是否存在
- fetch_messages返回的messages字段是对象列表，每个对象有text/time/sender字段
- filter_rpa_logs接收的messages参数应为fetch_messages返回的messages字段

你可以调用以下工具完成任务。每次只做必要的操作，分步执行。"""


class RPAAgent:
    """RPA监控Agent - 基于大模型的自主Agent"""

    def __init__(self):
        self.client = OpenAI(
            api_key=config.ai.API_KEY,
            base_url=config.ai.API_BASE
        )
        self.model = config.ai.MODEL
        self.tools = self._register_tools()
        self.tool_handlers = self._register_handlers()
        self.conversation_history: List[Dict] = []
        self.task_results: List[Dict] = []  # Agent执行的任务结果

    def _register_tools(self) -> List[Dict]:
        """注册Agent可调用的工具定义"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "fetch_messages",
                    "description": "从飞书群拉取指定时间范围内的消息",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "start_date": {
                                "type": "string",
                                "description": "开始日期，格式：YYYY-MM-DD"
                            },
                            "end_date": {
                                "type": "string",
                                "description": "结束日期，格式：YYYY-MM-DD"
                            },
                            "start_time": {
                                "type": "string",
                                "description": "开始时间（可选），格式：HH:MM，如 14:00。不填则默认从当天00:00开始"
                            },
                            "end_time": {
                                "type": "string",
                                "description": "结束时间（可选），格式：HH:MM，如 18:00。不填则默认到当天23:59结束"
                            }
                        },
                        "required": ["start_date", "end_date"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "filter_rpa_logs",
                    "description": "从消息列表中智能过滤出RPA运行日志，排除闲聊和无效消息。messages可以是fetch_messages返回的对象列表，也可以是纯字符串列表",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "messages": {
                                "type": "array",
                                "items": {
                                    "oneOf": [
                                        {"type": "string"},
                                        {
                                            "type": "object",
                                            "properties": {
                                                "text": {"type": "string"},
                                                "time": {"type": "string"},
                                                "sender": {"type": "string"}
                                            }
                                        }
                                    ]
                                },
                                "description": "原始消息列表，可直接传入fetch_messages返回的messages字段"
                            }
                        },
                        "required": ["messages"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "validate_file",
                    "description": "校验指定路径的文件是否存在，并检查时间合理性",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "要校验的文件完整路径"
                            },
                            "description": {
                                "type": "string",
                                "description": "文件描述（如：流水文件、余额截图等）"
                            },
                            "expected_date_range": {
                                "type": "string",
                                "description": "RPA日志中的查询日期范围（如：2026-01-01,2026-01-31），用于校验文件时间一致性"
                            }
                        },
                        "required": ["file_path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "validate_multiple_files",
                    "description": "批量校验多个文件路径是否存在",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_paths": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "path": {"type": "string"},
                                        "description": {"type": "string"}
                                    }
                                },
                                "description": "文件路径列表"
                            }
                        },
                        "required": ["file_paths"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "send_feishu_message",
                    "description": "向飞书群发送报告消息",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "content": {
                                "type": "string",
                                "description": "要发送的消息内容"
                            }
                        },
                        "required": ["content"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "send_email",
                    "description": "发送邮件报告",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "recipient_type": {
                                "type": "string",
                                "enum": ["business", "tech"],
                                "description": "收件人类型：business=业务负责人，tech=技术运维"
                            },
                            "subject": {
                                "type": "string",
                                "description": "邮件标题"
                            },
                            "body": {
                                "type": "string",
                                "description": "邮件正文"
                            }
                        },
                        "required": ["recipient_type", "subject", "body"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "send_wecom_message",
                    "description": "发送消息到企业微信群（支持Markdown格式）",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "content": {
                                "type": "string",
                                "description": "消息内容，支持Markdown格式"
                            },
                            "msg_type": {
                                "type": "string",
                                "enum": ["markdown", "text"],
                                "description": "消息类型，默认markdown"
                            }
                        },
                        "required": ["content"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "generate_executive_report",
                    "description": "生成领导级汇报（简洁突出重点+成功率+主要故障原因+失败详情TXT文件）",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "analysis_data": {
                                "type": "object",
                                "description": "RPA分析数据，包含total_count、success_count、failed_count、failed_items等字段",
                                "properties": {
                                    "total_count": {"type": "integer"},
                                    "success_count": {"type": "integer"},
                                    "failed_count": {"type": "integer"},
                                    "failed_items": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "account": {"type": "string"},
                                                "failure_reason": {"type": "string"},
                                                "login_status": {"type": "string"},
                                                "query_range": {"type": "string"},
                                                "file_path": {"type": "string"},
                                                "file_status": {"type": "string"}
                                            }
                                        }
                                    }
                                }
                            }
                        },
                        "required": ["analysis_data"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "query_rpa_database",
                    "description": "从数据库查询RPA运行日志（替代从飞书读取）",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "db_config_json": {
                                "type": "string",
                                "description": "数据库配置JSON字符串"
                            },
                            "start_date": {
                                "type": "string",
                                "description": "开始日期 YYYY-MM-DD"
                            },
                            "end_date": {
                                "type": "string",
                                "description": "结束日期 YYYY-MM-DD"
                            },
                            "custom_query": {
                                "type": "string",
                                "description": "可选，自定义SQL查询语句"
                            },
                            "field_mapping": {
                                "type": "string",
                                "description": "可选，字段映射JSON"
                            }
                        },
                        "required": ["db_config_json", "start_date", "end_date"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "update_config",
                    "description": "更新系统配置（飞书、AI、邮件等），用于AI配置助手",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "config_updates": {
                                "type": "string",
                                "description": "配置更新JSON字符串"
                            }
                        },
                        "required": ["config_updates"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "save_analysis_template",
                    "description": "保存分析模板（固定成功的分析流程，下次直接使用）",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "template_name": {
                                "type": "string",
                                "description": "模板名称"
                            },
                            "template_config": {
                                "type": "string",
                                "description": "模板配置JSON字符串"
                            }
                        },
                        "required": ["template_name", "template_config"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "load_analysis_template",
                    "description": "加载已保存的分析模板",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "template_name": {
                                "type": "string",
                                "description": "模板名称"
                            }
                        },
                        "required": ["template_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_templates",
                    "description": "列出所有已保存的分析模板",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_task",
                    "description": "创建一个待执行的任务（如：校验文件、发送通知等）",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "task_type": {
                                "type": "string",
                                "enum": ["validate_file", "send_notification",
                                         "analyze_screenshot", "check_data"],
                                "description": "任务类型"
                            },
                            "task_params": {
                                "type": "object",
                                "description": "任务参数"
                            },
                            "priority": {
                                "type": "string",
                                "enum": ["high", "medium", "low"],
                                "description": "优先级"
                            }
                        },
                        "required": ["task_type", "task_params"]
                    }
                }
            }
        ]

    def _register_handlers(self) -> Dict[str, Callable]:
        """注册工具的实际执行函数"""
        from agent.tools import (
            tool_fetch_messages,
            tool_filter_rpa_logs,
            tool_validate_file,
            tool_validate_multiple_files,
            tool_send_feishu_message,
            tool_send_email,
            tool_send_wecom_message,
            tool_generate_executive_report,
            tool_create_task,
        )
        from agent.db_tools import tool_query_rpa_database
        from agent.config_tools import (
            tool_update_config,
            tool_save_analysis_template,
            tool_load_analysis_template,
            tool_list_templates
        )
        return {
            "fetch_messages": tool_fetch_messages,
            "filter_rpa_logs": tool_filter_rpa_logs,
            "validate_file": tool_validate_file,
            "validate_multiple_files": tool_validate_multiple_files,
            "send_feishu_message": tool_send_feishu_message,
            "send_email": tool_send_email,
            "send_wecom_message": tool_send_wecom_message,
            "generate_executive_report": tool_generate_executive_report,
            "create_task": tool_create_task,
            "query_rpa_database": tool_query_rpa_database,
            "update_config": tool_update_config,
            "save_analysis_template": tool_save_analysis_template,
            "load_analysis_template": tool_load_analysis_template,
            "list_templates": tool_list_templates,
        }

    def run(self, user_input: str) -> str:
        """
        Agent主循环：接收用户指令，自主规划并执行任务链
        支持多轮工具调用直到任务完成
        """
        # 添加用户消息
        self.conversation_history.append({
            "role": "user",
            "content": user_input
        })

        # 限制历史长度，防止token溢出（保留最近20轮对话）
        history_window = self.conversation_history[-40:]
        today = datetime.now().strftime("%Y-%m-%d")
        system_msg = {"role": "system", "content": SYSTEM_PROMPT.format(today=today)}
        messages = [system_msg] + history_window
        max_iterations = 15  # 防止无限循环

        for i in range(max_iterations):
            logger.info(f"[Agent] 第 {i+1} 轮思考...")

            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=self.tools,
                    tool_choice="auto"
                )
            except Exception as e:
                error_msg = f"[Agent] 大模型调用失败: {e}"
                logger.error(error_msg)
                return error_msg

            message = response.choices[0].message

            # 如果没有工具调用，说明Agent已完成任务，返回最终回复
            if not message.tool_calls:
                final_reply = message.content or ""
                self.conversation_history.append({
                    "role": "assistant",
                    "content": final_reply
                })
                logger.info(f"[Agent] 任务完成，共执行 {i} 轮工具调用")
                return final_reply

            # 处理工具调用 - 构造assistant消息（只保留必要字段）
            assistant_msg = {
                "role": "assistant",
                "content": message.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in message.tool_calls
                ]
            }
            messages.append(assistant_msg)

            for tool_call in message.tool_calls:
                func_name = tool_call.function.name

                try:
                    func_args = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    func_args = {}
                    logger.warning(f"[Agent] 工具参数解析失败: {tool_call.function.arguments}")

                logger.info(f"[Agent] 调用工具: {func_name}({json.dumps(func_args, ensure_ascii=False)[:200]})")

                # 执行工具
                handler = self.tool_handlers.get(func_name)
                if handler:
                    try:
                        result = handler(**func_args)
                    except Exception as e:
                        result = {"success": False, "error": f"工具执行错误: {str(e)}"}
                        logger.error(f"[Agent] 工具 {func_name} 执行异常: {e}")
                else:
                    result = {"success": False, "error": f"未知工具: {func_name}"}

                # 记录结果
                self.task_results.append({
                    "tool": func_name,
                    "args": func_args,
                    "result": result
                })

                # 序列化结果（限制长度防止爆token）
                result_str = json.dumps(result, ensure_ascii=False) if not isinstance(result, str) else result
                if len(result_str) > 8000:
                    result_str = result_str[:8000] + "\n...(结果过长已截断)"

                # 添加工具结果到消息
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result_str
                })

        return "[Agent] 达到最大执行轮次，任务可能未完成"

    def run_daily_analysis(self) -> str:
        """每日自动分析入口 - 无需用户指令，自动执行"""
        prompt = (
            "请执行今日的RPA日志分析任务：\n"
            "1. 拉取今日飞书群内所有消息\n"
            "2. 过滤出RPA运行日志\n"
            "3. 分析每条日志的运行状态\n"
            "4. 提取所有文件路径并逐一校验是否存在\n"
            "5. 统计今日运行总数、成功数、失败数\n"
            "6. 生成汇总报告发送到飞书群\n"
            "7. 根据是否有异常，差异化发送邮件（无异常→业务负责人，有异常→技术运维）"
        )
        return self.run(prompt)

    def query(self, user_input: str) -> str:
        """对话式查询入口 - 响应用户自然语言指令"""
        return self.run(user_input)

    def reset(self):
        """重置对话历史"""
        self.conversation_history = []
        self.task_results = []
