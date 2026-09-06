import requests
import time
import json
from urllib.parse import urlparse, parse_qs
import os  # 导入 os 模块
from dotenv import load_dotenv  # 导入 dotenv 模块

# --- 加载环境变量 ---
# 这行代码会读取当前目录下的 .env 文件，并将其中的变量加载到环境变量中
load_dotenv()

# ===== 用户配置：从环境变量中读取 =====
# 1. 读取 LINK_LIST 字符串
link_list_str = os.getenv('LINK_LIST')

# 2. 将字符串按行分割，并过滤掉空行，生成列表
# os.getenv 的第二个参数是默认值，如果环境变量不存在，则返回一个空列表
LINK_LIST = link_list_str.splitlines() if link_list_str else []

BASE = "https://mall.tellhowdm.cn"
INTERVAL = 2
# =====================================

# ... (其余代码保持不变) ...

def parse_identifier(url):
    """从链接中提取 openid 或 terminalId，以及 channel"""
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    openid = params.get('openid', [None])[0]
    terminal_id = params.get('terminalId', [None])[0]
    channel = params.get('channel', ['share'])[0]
    user_id = openid or terminal_id
    is_openid = openid is not None
    return user_id, channel, is_openid

# ... (其余函数 get_jsessionid, query_init, do_sign, query_vip_info 保持不变) ...

def get_jsessionid(base_url, user_id, channel):
    """访问主页获取 JSESSIONID"""
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:146.0) Gecko/20100101 Firefox/146.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    })
    # 注意：这里保留了 4.py 的逻辑，即只处理 openid。
    # 如果你的链接包含 terminalId，请参考上一个回答使用“调整.py”的逻辑。
    resp = session.get(f"{base_url}/activity/act67/open/home",
                       params={"openid": user_id, "channel": channel} if user_id else {"channel": channel},
                       timeout=10)
    jsessionid = session.cookies.get("JSESSIONID")
    return session, jsessionid

# ... (其余函数 process_one, main 保持不变) ...

def process_one(url, index, total):
    print(f"\n🔹 处理第 {index+1}/{total} 个链接")
    # 为了安全，打印时隐藏部分链接信息
    print(f"🔗 {url[:30]}...") 
    # ...
    # (process_one 函数内部逻辑不变)
    # ...

def main():
    total = len(LINK_LIST)
    if total == 0:
        print("⚠️ 链接列表为空，请检查 .env 文件中的 LINK_LIST 配置")
        return

    print(f"📋 共 {total} 个链接，间隔 {INTERVAL} 秒")
    for i, url in enumerate(LINK_LIST):
        process_one(url, i, total)
        if i < total - 1:
            print(f"⏳ 等待 {INTERVAL} 秒...")
            time.sleep(INTERVAL)

    print("\n🎉 全部处理完成！")

if __name__ == "__main__":
    main()
