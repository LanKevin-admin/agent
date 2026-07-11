"""
AI配置助手 - 通过自然语言对话配置系统
"""
import os
import sys
import re
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def get_base_dir():
    """获取基础目录，兼容开发环境和EXE打包"""
    if getattr(sys, 'frozen', False):
        # EXE运行：使用EXE所在目录
        return os.path.dirname(sys.executable)
    else:
        # 开发环境：使用项目根目录
        return os.path.dirname(os.path.dirname(__file__))


def tool_update_config(
    config_updates: str
) -> Dict[str, Any]:
    """
    更新系统配置

    Args:
        config_updates: JSON格式的配置更新，例如：
        {
            "FEISHU_APP_ID": "cli_xxx",
            "FEISHU_APP_SECRET": "xxx",
            "AI_API_KEY": "sk-xxx"
        }

    Returns:
        {"success": true/false, "message": "更新结果"}
    """
    try:
        updates = json.loads(config_updates)
        env_path = os.path.join(get_base_dir(), '.env')

        # 读取现有配置（如果不存在则从模板创建）
        if os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        else:
            # .env不存在，从.env.example创建
            example_path = os.path.join(get_base_dir(), '.env.example')
            if os.path.exists(example_path):
                with open(example_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                logger.info("[ConfigAssistant] .env不存在，从.env.example创建")
            else:
                # 连example都没有，从打包内的加载
                if getattr(sys, 'frozen', False):
                    # EXE模式：从临时目录加载
                    example_path = os.path.join(sys._MEIPASS, '.env.example')
                    if os.path.exists(example_path):
                        with open(example_path, 'r', encoding='utf-8') as f:
                            lines = f.readlines()
                    else:
                        lines = []
                else:
                    lines = []
        
        # 更新配置
        updated_keys = set()
        new_lines = []
        
        for line in lines:
            line = line.rstrip('\n')
            # 跳过空行和注释
            if not line.strip() or line.strip().startswith('#'):
                new_lines.append(line)
                continue
            
            # 解析键值对
            if '=' in line:
                key = line.split('=')[0].strip()
                if key in updates:
                    new_lines.append(f"{key}={updates[key]}")
                    updated_keys.add(key)
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)
        
        # 添加新配置项
        for key, value in updates.items():
            if key not in updated_keys:
                new_lines.append(f"{key}={value}")
        
        # 写回文件
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(new_lines))
            if new_lines and not new_lines[-1].endswith('\n'):
                f.write('\n')

        logger.info(f"[ConfigAssistant] 配置文件已写入: {env_path}")

        # 验证：重新读取文件确认写入成功
        try:
            with open(env_path, 'r', encoding='utf-8') as f:
                verify_content = f.read()

            # 检查每个更新的配置项是否在文件中
            verification_failed = []
            for key, value in updates.items():
                expected_line = f"{key}={value}"
                if expected_line not in verify_content:
                    verification_failed.append(key)

            if verification_failed:
                return {
                    "success": False,
                    "message": f"❌ 配置写入验证失败\n"
                              f"未找到配置项: {', '.join(verification_failed)}\n"
                              f"请检查文件权限或手动编辑.env文件",
                    "verified": False,
                    "failed_keys": verification_failed
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"❌ 配置写入后验证失败: {str(e)}",
                "verified": False
            }

        # 特别提示：需要重启服务
        need_restart_keys = ['FEISHU_APP_ID', 'FEISHU_APP_SECRET', 'AI_API_KEY', 'AI_API_BASE', 'AI_MODEL']
        needs_restart = any(key in need_restart_keys for key in updates.keys())

        # 构建详细的成功消息
        updated_list = '\n'.join([f"  • {k} = {v[:20]}..." if len(str(v)) > 20 else f"  • {k} = {v}"
                                   for k, v in updates.items()])

        message = f"✅ 配置更新成功！已更新 {len(updates)} 项：\n{updated_list}\n"
        if needs_restart:
            message += "\n⚠️  部分配置需要重启服务才能生效"
        else:
            message += "\n✓ 配置已立即生效"

        return {
            "success": True,
            "message": message,
            "verified": True,
            "updated_keys": list(updates.keys()),
            "needs_restart": needs_restart,
            "file_path": env_path
        }
        
    except Exception as e:
        logger.error(f"[ConfigAssistant] 配置更新失败: {e}")
        return {
            "success": False,
            "message": f"配置更新失败: {str(e)}"
        }


def tool_save_analysis_template(
    template_name: str,
    template_config: str
) -> Dict[str, Any]:
    """
    保存分析模板（固定成功的分析流程）- 带验证

    Args:
        template_name: 模板名称，如 "生产环境日报"
        template_config: 模板配置JSON，包含：
        {
            "data_source": "database|feishu",
            "db_config": {...},  # 数据库配置
            "query": "SELECT...",  # SQL查询
            "field_mapping": {...},  # 字段映射
            "file_check_field": "file_path",  # 需要校验的文件路径字段
            "date_range_field": "query_range",  # 日期范围字段
            "description": "模板描述"
        }

    Returns:
        {"success": true/false, "message": "保存结果", "verified": true/false}
    """
    try:
        # 步骤1: 解析配置JSON
        try:
            config = json.loads(template_config)
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "message": f"❌ 模板配置JSON格式错误: {str(e)}",
                "verified": False
            }

        # 步骤2: 验证必需字段
        required_fields = ['data_source']
        missing_fields = [f for f in required_fields if f not in config]
        if missing_fields:
            return {
                "success": False,
                "message": f"❌ 模板配置缺少必需字段: {', '.join(missing_fields)}",
                "verified": False
            }

        # 步骤3: 创建目录
        templates_dir = os.path.join(get_base_dir(), 'templates')
        os.makedirs(templates_dir, exist_ok=True)

        # 步骤4: 写入文件
        template_file = os.path.join(templates_dir, f"{template_name}.json")
        with open(template_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

        logger.info(f"[ConfigAssistant] 模板文件已写入: {template_file}")

        # 步骤5: 验证文件是否存在
        if not os.path.exists(template_file):
            return {
                "success": False,
                "message": f"❌ 模板文件写入后未找到: {template_file}",
                "verified": False
            }

        # 步骤6: 读回验证内容
        try:
            with open(template_file, 'r', encoding='utf-8') as f:
                verify_config = json.load(f)

            # 验证关键字段
            if verify_config.get('data_source') != config.get('data_source'):
                return {
                    "success": False,
                    "message": f"❌ 模板文件验证失败：内容不匹配",
                    "verified": False
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"❌ 模板文件读回验证失败: {str(e)}",
                "verified": False
            }

        # 步骤7: 获取文件大小
        file_size = os.path.getsize(template_file)

        return {
            "success": True,
            "message": f"✅ 模板 '{template_name}' 保存成功！\n"
                      f"📁 文件路径: {template_file}\n"
                      f"📊 文件大小: {file_size} 字节\n"
                      f"✓ 已验证文件完整性",
            "verified": True,
            "template_path": template_file,
            "file_size": file_size,
            "template_name": template_name
        }

    except Exception as e:
        logger.error(f"[ConfigAssistant] 模板保存失败: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"❌ 模板保存失败: {str(e)}",
            "verified": False,
            "error": str(e)
        }


def tool_load_analysis_template(template_name: str) -> Dict[str, Any]:
    """
    加载已保存的分析模板

    Args:
        template_name: 模板名称

    Returns:
        {
            "success": true/false,
            "template": {...},  # 模板配置
            "message": "加载结果"
        }
    """
    try:
        templates_dir = os.path.join(get_base_dir(), 'templates')
        template_file = os.path.join(templates_dir, f"{template_name}.json")
        
        if not os.path.exists(template_file):
            return {
                "success": False,
                "message": f"模板 '{template_name}' 不存在"
            }
        
        with open(template_file, 'r', encoding='utf-8') as f:
            template = json.load(f)
        
        logger.info(f"[ConfigAssistant] 模板已加载: {template_name}")
        
        return {
            "success": True,
            "template": template,
            "message": f"模板 '{template_name}' 已加载"
        }
        
    except Exception as e:
        logger.error(f"[ConfigAssistant] 模板加载失败: {e}")
        return {
            "success": False,
            "message": f"模板加载失败: {str(e)}"
        }


def tool_list_templates() -> Dict[str, Any]:
    """
    列出所有已保存的模板

    Returns:
        {
            "success": true,
            "templates": [
                {"name": "生产环境日报", "description": "..."},
                ...
            ]
        }
    """
    try:
        templates_dir = os.path.join(get_base_dir(), 'templates')
        
        if not os.path.exists(templates_dir):
            return {
                "success": True,
                "templates": []
            }
        
        templates = []
        for filename in os.listdir(templates_dir):
            if filename.endswith('.json'):
                template_name = filename[:-5]
                template_file = os.path.join(templates_dir, filename)
                
                with open(template_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                templates.append({
                    "name": template_name,
                    "description": config.get("description", ""),
                    "data_source": config.get("data_source", "")
                })
        
        return {
            "success": True,
            "templates": templates
        }
        
    except Exception as e:
        logger.error(f"[ConfigAssistant] 列出模板失败: {e}")
        return {
            "success": False,
            "message": f"列出模板失败: {str(e)}",
            "templates": []
        }
