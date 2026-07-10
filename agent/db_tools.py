"""
数据库查询工具
支持从MySQL/PostgreSQL/SQLite等数据库读取RPA日志
"""
import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# 数据库连接池（延迟加载）
_db_connections = {}


def get_database_connection(db_config: Dict[str, Any]):
    """
    获取数据库连接
    
    Args:
        db_config: {
            "type": "mysql|postgresql|sqlite",
            "host": "localhost",
            "port": 3306,
            "database": "rpa_db",
            "user": "root",
            "password": "xxx",
            "table": "rpa_logs"  # 可选，默认表名
        }
    """
    db_type = db_config.get("type", "mysql").lower()
    
    try:
        if db_type == "mysql":
            import pymysql
            conn = pymysql.connect(
                host=db_config.get("host", "localhost"),
                port=db_config.get("port", 3306),
                user=db_config.get("user"),
                password=db_config.get("password"),
                database=db_config.get("database"),
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
            return conn
            
        elif db_type == "postgresql":
            import psycopg2
            import psycopg2.extras
            conn = psycopg2.connect(
                host=db_config.get("host", "localhost"),
                port=db_config.get("port", 5432),
                user=db_config.get("user"),
                password=db_config.get("password"),
                database=db_config.get("database")
            )
            return conn
            
        elif db_type == "sqlite":
            import sqlite3
            conn = sqlite3.connect(db_config.get("database", "rpa.db"))
            conn.row_factory = sqlite3.Row
            return conn
            
        else:
            raise ValueError(f"不支持的数据库类型: {db_type}")
            
    except Exception as e:
        logger.error(f"[DB] 连接数据库失败: {e}")
        raise


def query_database(
    db_config: Dict[str, Any],
    query: str,
    params: Optional[tuple] = None
) -> List[Dict[str, Any]]:
    """
    执行数据库查询
    
    Args:
        db_config: 数据库配置
        query: SQL查询语句
        params: 查询参数（防SQL注入）
        
    Returns:
        查询结果列表
    """
    conn = None
    try:
        conn = get_database_connection(db_config)
        cursor = conn.cursor()
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        # 获取结果
        if db_config.get("type") == "postgresql":
            import psycopg2.extras
            results = [dict(row) for row in cursor.fetchall()]
        elif db_config.get("type") == "sqlite":
            results = [dict(row) for row in cursor.fetchall()]
        else:  # MySQL
            results = cursor.fetchall()
        
        logger.info(f"[DB] 查询成功，返回 {len(results)} 条记录")
        return results
        
    except Exception as e:
        logger.error(f"[DB] 查询失败: {e}")
        raise
        
    finally:
        if conn:
            conn.close()


def tool_query_rpa_database(
    db_config_json: str,
    start_date: str,
    end_date: str,
    custom_query: Optional[str] = None,
    field_mapping: Optional[str] = None
) -> Dict[str, Any]:
    """
    从数据库查询RPA运行日志
    
    Args:
        db_config_json: 数据库配置JSON字符串
        start_date: 开始日期 YYYY-MM-DD
        end_date: 结束日期 YYYY-MM-DD
        custom_query: 可选，自定义SQL查询语句（必须包含 {start_date} 和 {end_date} 占位符）
        field_mapping: 可选，字段映射JSON，如 {"account": "账号名", "status": "运行状态", "file_path": "文件路径"}
        
    Returns:
        {
            "success": true/false,
            "records": [...],  # 查询到的记录
            "count": 10,
            "error": "错误信息"
        }
    """
    try:
        db_config = json.loads(db_config_json)
        
        # 构建查询语句
        if custom_query:
            query = custom_query.format(start_date=start_date, end_date=end_date)
        else:
            # 默认查询模板
            table = db_config.get("table", "rpa_logs")
            date_field = db_config.get("date_field", "created_at")
            query = f"""
                SELECT * FROM {table}
                WHERE {date_field} >= '{start_date}' 
                AND {date_field} < DATE_ADD('{end_date}', INTERVAL 1 DAY)
                ORDER BY {date_field} DESC
            """
        
        records = query_database(db_config, query)
        
        # 字段映射
        if field_mapping:
            mapping = json.loads(field_mapping)
            mapped_records = []
            for record in records:
                mapped = {}
                for target_field, source_field in mapping.items():
                    mapped[target_field] = record.get(source_field)
                mapped_records.append(mapped)
            records = mapped_records
        
        return {
            "success": True,
            "records": records,
            "count": len(records)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "records": [],
            "count": 0
        }
