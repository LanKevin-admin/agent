"""
数据库修复脚本 - 添加缺失的字段
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(__file__))

from database.models import init_db, get_db, DB_PATH
from sqlalchemy import text

def fix_database():
    """修复数据库表结构"""
    print("=" * 60)
    print("  数据库修复工具")
    print("=" * 60)
    print(f"  数据库路径: {DB_PATH}")
    print("=" * 60)
    
    # 方法1：删除旧数据库，重新创建（最简单）
    if os.path.exists(DB_PATH):
        print("\n检测到旧数据库文件")
        print("警告：重建数据库会丢失所有数据！")
        choice = input("是否删除旧数据库并重建？(y/n): ")
        
        if choice.lower() == 'y':
            os.remove(DB_PATH)
            print("✅ 已删除旧数据库")
            
            # 重新创建
            init_db()
            print("✅ 数据库重建完成！")
            print("\n新的表结构：")
            print("  - conversations (对话记录)")
            print("  - scheduled_tasks (定时任务)")
            print("  - task_executions (任务执行记录)")
            print("  - analysis_templates (分析模板)")
            return
    
    # 如果数据库不存在，直接创建
    print("\n创建新数据库...")
    init_db()
    print("✅ 数据库创建完成！")


if __name__ == '__main__':
    fix_database()
