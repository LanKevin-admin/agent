"""
测试飞书消息监听功能
"""
import logging
from feishu.message_monitor import message_monitor
from config.settings import config

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_config():
    """测试飞书配置"""
    print("\n" + "="*60)
    print("0. 检查飞书配置")
    print("="*60)

    app_id = config.feishu.APP_ID
    app_secret = config.feishu.APP_SECRET
    chat_id = config.feishu.TARGET_CHAT_ID

    print(f"APP_ID: {'✅ 已配置' if app_id else '❌ 未配置'}")
    print(f"APP_SECRET: {'✅ 已配置' if app_secret else '❌ 未配置'}")
    print(f"TARGET_CHAT_ID: {'✅ 已配置' if chat_id else '❌ 未配置'}")

    if not app_id or not app_secret or not chat_id:
        print("\n⚠️  警告：飞书配置不完整，消息监听功能将无法正常工作")
        print("请在 .env 文件中配置：")
        print("  FEISHU_APP_ID=...")
        print("  FEISHU_APP_SECRET=...")
        print("  FEISHU_CHAT_ID=...")
        return False

    return True

def test_bot_info():
    """测试获取机器人信息"""
    print("\n" + "="*60)
    print("1. 测试获取机器人信息")
    print("="*60)
    
    bot_id = message_monitor.get_bot_info()
    if bot_id:
        print(f"✅ 机器人ID: {bot_id}")
        return True
    else:
        print("❌ 获取机器人信息失败")
        return False

def test_fetch_messages():
    """测试获取群消息"""
    print("\n" + "="*60)
    print("2. 测试获取最近1分钟的群消息")
    print("="*60)

    messages = message_monitor.fetch_recent_messages(minutes=1)
    print(f"✅ 获取到 {len(messages)} 条消息")

    if messages:
        print("\n最新的3条消息：")
        for i, msg in enumerate(messages[:3], 1):
            print(f"\n原始消息 {i} 结构：")
            print(f"  - message_id: {msg.get('message_id', 'N/A')}")
            print(f"  - msg_type: {msg.get('msg_type', 'N/A')}")
            print(f"  - sender: {msg.get('sender', {})}")

            # 打印body结构
            body = msg.get('body', {})
            print(f"  - body.content类型: {type(body.get('content', ''))}")
            print(f"  - body.content: {str(body.get('content', ''))[:100]}...")

            # 打印mentions结构
            mentions = msg.get('mentions', [])
            print(f"  - mentions数量: {len(mentions)}")
            if mentions:
                for j, mention in enumerate(mentions[:2], 1):
                    print(f"    mention {j}: {mention}")

            # 解析消息
            print(f"\n  解析结果：")
            parsed = message_monitor.parse_message(msg)
            if parsed:
                print(f"    ✅ 解析成功")
                print(f"    - 内容: {parsed['content'][:50]}...")
                print(f"    - 是否@机器人: {parsed['is_mention_bot']}")
            else:
                print(f"    ❌ 解析失败")

    return len(messages) > 0

def test_check_mentions():
    """测试检查@消息"""
    print("\n" + "="*60)
    print("3. 测试检查新@消息（含后续消息）")
    print("="*60)

    mentions = message_monitor.check_new_mentions()
    print(f"✅ 发现 {len(mentions)} 条需要处理的消息")

    if mentions:
        print("\n需要处理的消息详情：")
        for i, mention in enumerate(mentions, 1):
            is_mention = mention.get('is_mention_bot', False)
            msg_type = "[@消息]" if is_mention else "[后续消息]"
            print(f"\n消息 {i} {msg_type}:")
            print(f"  - 消息ID: {mention['message_id'][:30]}...")
            print(f"  - 原始内容: {mention['content']}")
            if is_mention:
                print(f"  - 清理后: {message_monitor.clean_mention_text(mention['content'])}")
    else:
        print("\n💡 提示：")
        print("  测试场景1 - 先@后不@：")
        print("    1. 在群里@机器人发送：@机器人 第一条消息")
        print("    2. 不要@，直接发送：第二条消息")
        print("    3. 等10秒后运行此测试")
        print("\n  测试场景2 - 连续@：")
        print("    1. 在群里@机器人发送：@机器人 问题1")
        print("    2. 再次@机器人发送：@机器人 问题2")
        print("    3. 等10秒后运行此测试")

    return True

def test_session_info():
    """测试会话信息"""
    print("\n" + "="*60)
    print("4. 当前会话状态")
    print("="*60)

    if message_monitor.user_sessions:
        print(f"✅ 活跃会话数: {len(message_monitor.user_sessions)}")
        for user_id, session in message_monitor.user_sessions.items():
            import time
            last_time = session['last_mention_time']
            time_diff = int(time.time()) - last_time
            print(f"\n用户: {user_id[:20]}...")
            print(f"  - 最后活跃: {time_diff}秒前")
            print(f"  - 会话状态: {'有效' if time_diff <= 300 else '已过期'}")
    else:
        print("⚠️ 当前没有活跃会话")

    print(f"\n已处理消息数: {len(message_monitor.processed_message_ids)}")

    return True

def main():
    """主测试流程"""
    print("\n🔍 飞书消息监听功能测试 - 增强版")
    print("="*60)

    try:
        # 测试0: 检查配置
        if not test_config():
            print("\n❌ 配置检查失败，请先配置飞书信息")
            return

        # 测试1: 获取机器人信息
        if not test_bot_info():
            print("\n❌ 测试失败：无法获取机器人信息，请检查飞书配置")
            return

        # 测试2: 获取群消息
        test_fetch_messages()

        # 测试3: 检查@消息
        test_check_mentions()

        # 测试4: 会话状态
        test_session_info()

        print("\n" + "="*60)
        print("✅ 测试完成")
        print("="*60)
        print("\n💡 新功能：")
        print("  1. 先@后续不@：机器人会记住5分钟内的对话")
        print("  2. 连续@消息：每条都会独立回复")
        print("  3. 会话过期：5分钟无交互后需要重新@")
        print("="*60)

    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
