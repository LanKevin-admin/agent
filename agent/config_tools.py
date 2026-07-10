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
        
        logger.info(f"[ConfigAssistant] 配置已更新: {list(updates.keys())}")

        # 特别提示：需要重启服务
        need_restart_keys = ['FEISHU_APP_ID', 'FEISHU_APP_SECRET', 'AI_API_KEY', 'AI_API_BASE', 'AI_MODEL']
        needs_restart = any(key in need_restart_keys for key in updates.keys())

        message = f"已更新 {len(updates)} 项配置"
        if needs_restart:
            message += "，需要重启服务才能生效"

        return {
            "success": True,
            "message": message,
            "updated_keys": list(updates.keys()),
            "needs_restart": needs_restart
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
    保存分析模板（固定成功的分析流程）

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
        {"success": true/false, "message": "保存结果"}
    """
    try:
        config = json.loads(template_config)
        templates_dir = os.path.join(get_base_dir(), 'templates')
        os.makedirs(templates_dir, exist_ok=True)
        
        template_file = os.path.join(templates_dir, f"{template_name}.json")
        
        with open(template_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        logger.info(f"[ConfigAssistant] 模板已保存: {template_name}")
        
        return {
            "success": True,
            "message": f"模板 '{template_name}' 已保存",
            "template_path": template_file
        }
        
    except Exception as e:
        logger.error(f"[ConfigAssistant] 模板保存失败: {e}")
        return {
            "success": False,
            "message": f"模板保存失败: {str(e)}"
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
