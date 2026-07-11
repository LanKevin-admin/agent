"""
启动Chrome浏览器（远程调试模式）
用于RPA页面复用
"""
import os
import sys
import subprocess
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def find_chrome_path():
    """查找Chrome安装路径"""
    possible_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Users\{}\AppData\Local\Google\Chrome\Application\chrome.exe".format(os.getenv('USERNAME')),
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    return None


def start_chrome_debug(port=9222, user_data_dir=None):
    """
    启动Chrome远程调试模式
    
    Args:
        port: 远程调试端口（默认9222）
        user_data_dir: 用户数据目录（默认使用临时目录）
    """
    # 查找Chrome路径
    chrome_path = find_chrome_path()
    
    if not chrome_path:
        logger.error("❌ 未找到Chrome浏览器！请确保已安装Chrome")
        return False
    
    logger.info(f"✅ 找到Chrome: {chrome_path}")
    
    # 设置用户数据目录
    if not user_data_dir:
        user_data_dir = os.path.join(os.path.dirname(__file__), "..", "chrome_rpa_profile")
        user_data_dir = os.path.abspath(user_data_dir)
    
    os.makedirs(user_data_dir, exist_ok=True)
    logger.info(f"📁 用户数据目录: {user_data_dir}")
    
    # 构建启动命令
    cmd = [
        chrome_path,
        f"--remote-debugging-port={port}",
        f"--user-data-dir={user_data_dir}",
        "--no-first-run",  # 跳过首次运行提示
        "--no-default-browser-check",  # 跳过默认浏览器检查
    ]
    
    logger.info(f"🚀 启动Chrome（远程调试端口: {port}）...")
    logger.info(f"   命令: {' '.join(cmd)}")
    
    try:
        # 启动Chrome（不等待）
        subprocess.Popen(cmd, 
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == 'win32' else 0)
        
        logger.info("✅ Chrome已启动！")
        logger.info(f"📡 CDP地址: http://localhost:{port}")
        logger.info("")
        logger.info("💡 使用说明:")
        logger.info("   1. 保持此Chrome窗口运行")
        logger.info("   2. RPA将自动连接到此浏览器")
        logger.info("   3. 所有操作都在此浏览器中执行")
        logger.info("   4. 关闭浏览器即结束RPA会话")
        logger.info("")
        logger.info("⚠️  注意: 请勿手动关闭命令行窗口")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 启动Chrome失败: {e}")
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='启动Chrome浏览器（远程调试模式）')
    parser.add_argument('--port', type=int, default=9222, help='远程调试端口（默认9222）')
    parser.add_argument('--user-data-dir', type=str, default=None, help='用户数据目录')
    
    args = parser.parse_args()
    
    success = start_chrome_debug(port=args.port, user_data_dir=args.user_data_dir)
    
    if success:
        print("\n按Ctrl+C退出...")
        try:
            # 保持脚本运行
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n👋 脚本已停止（Chrome仍在运行）")
    else:
        sys.exit(1)
