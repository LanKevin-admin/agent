"""
配置文件诊断工具
检查EXE模式下的配置文件路径和AI配置助手
"""
import os
import sys

print("=" * 60)
print("  配置文件诊断工具")
print("=" * 60)

# 检查运行模式
if getattr(sys, 'frozen', False):
    print("\n✅ 运行模式: EXE打包模式")
    base_dir = os.path.dirname(sys.executable)
    print(f"   EXE路径: {sys.executable}")
else:
    print("\n✅ 运行模式: 开发模式")
    base_dir = os.path.dirname(__file__)

print(f"   基础目录: {base_dir}")

# 检查.env文件
env_file = os.path.join(base_dir, '.env')
print(f"\n📄 .env文件:")
print(f"   路径: {env_file}")
print(f"   存在: {'✅ 是' if os.path.exists(env_file) else '❌ 否'}")

if os.path.exists(env_file):
    with open(env_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    print(f"   行数: {len(lines)}行")
    print(f"   内容预览:")
    for i, line in enumerate(lines[:5], 1):
        print(f"      {i}. {line.rstrip()}")
    if len(lines) > 5:
        print(f"      ... (共{len(lines)}行)")

# 检查.env.example模板
example_file = os.path.join(base_dir, '.env.example')
print(f"\n📄 .env.example模板:")
print(f"   路径: {example_file}")
print(f"   存在: {'✅ 是' if os.path.exists(example_file) else '❌ 否'}")

if not os.path.exists(example_file) and getattr(sys, 'frozen', False):
    # 检查打包内的模板
    if hasattr(sys, '_MEIPASS'):
        packed_example = os.path.join(sys._MEIPASS, '.env.example')
        print(f"\n📦 打包内的模板:")
        print(f"   路径: {packed_example}")
        print(f"   存在: {'✅ 是' if os.path.exists(packed_example) else '❌ 否'}")

# 检查配置加载
print(f"\n⚙️ 配置加载测试:")
try:
    from config.settings import config
    print(f"   AI_API_KEY: {'已配置' if config.ai.API_KEY else '❌ 未配置'}")
    print(f"   FEISHU_APP_ID: {'已配置' if config.feishu.APP_ID else '❌ 未配置'}")
    print(f"   SMTP_USER: {'已配置' if config.email.SMTP_USER else '❌ 未配置'}")
except Exception as e:
    print(f"   ❌ 加载失败: {e}")

# 测试AI配置助手
print(f"\n🤖 AI配置助手测试:")
try:
    from agent.config_tools import get_base_dir as tool_base_dir
    tool_dir = tool_base_dir()
    print(f"   工具基础目录: {tool_dir}")
    print(f"   与实际基础目录一致: {'✅ 是' if tool_dir == base_dir else '❌ 否'}")
    
    # 测试.env路径
    tool_env = os.path.join(tool_dir, '.env')
    print(f"   工具.env路径: {tool_env}")
    print(f"   与实际.env一致: {'✅ 是' if tool_env == env_file else '❌ 否'}")
except Exception as e:
    print(f"   ❌ 测试失败: {e}")

print("\n" + "=" * 60)
print("  诊断完成")
print("=" * 60)

# 给出建议
print("\n💡 问题诊断:")
if not os.path.exists(env_file):
    print("   ⚠️ .env文件不存在")
    print("   建议: 从配置页面保存配置，或手动创建")
elif os.path.exists(env_file):
    with open(env_file, 'r', encoding='utf-8') as f:
        content = f.read()
    if len(content.strip().split('\n')) < 10:
        print("   ⚠️ .env文件内容不完整（少于10行）")
        print("   建议: 从.env.example复制完整模板")
    else:
        print("   ✅ .env文件看起来正常")

input("\n按回车键退出...")
