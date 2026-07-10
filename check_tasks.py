"""检查定时任务"""
from database.models import DB_PATH, SessionLocal
from database.operations import get_all_tasks

print("=" * 60)
print("  定时任务检查")
print("=" * 60)
print(f"数据库路径: {DB_PATH}")
print("=" * 60)

db = SessionLocal()
try:
    tasks = get_all_tasks(db)
    print(f"\n✅ 找到 {len(tasks)} 个定时任务：\n")
    
    if tasks:
        for t in tasks:
            print(f"📋 任务名: {t.task_name}")
            print(f"   类型: {t.task_type}")
            print(f"   Cron: {t.cron_expression}")
            print(f"   状态: {'✅ 启用' if t.enabled else '❌ 禁用'}")
            print(f"   查询: {t.query_text[:50]}...")
            print()
    else:
        print("⚠️ 没有找到任何定时任务")
        print("\n可能原因：")
        print("1. AI创建任务后保存到了其他数据库")
        print("2. 数据库路径不对")
        print("3. 任务创建失败")
        
finally:
    db.close()
