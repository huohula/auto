import requests
import time
import json
import webbrowser
import subprocess
from urllib.parse import urlparse, parse_qs

# ===== 用户配置：填入你的签到链接列表（可混用两种格式） =====
LINK_LIST = [
    "http://mall.tellhowdm.cn/activity/act67/open/home?openid=obJT21TdFBT_uX8ZAKgEBxaipr68&channel=share",
    "http://mall.tellhowdm.cn/activity/act67/open/home?openid=obJT21aOxa_lJMPrq8djUbtF8zxY&channel=share",
    "https://mall.tellhowdm.cn/activity/act67/open/home?terminalId=Uld7lY83AUzNxc69qzzMLA%3D%3D&channel=share",
    "https://mall.tellhowdm.cn/activity/act67/open/home?terminalId=DD3amwP0iKtdsYM3ogVcag%3D%3D&channel=share",
    "https://mall.tellhowdm.cn/activity/act67/open/home?terminalId=9WqaO4BKBzLUXDK4y%2BqprQ%3D%3D&channel=share",
    "https://mall.tellhowdm.cn/activity/act67/open/home?terminalId=o8i7fm%2BnOLFdsYM3ogVcag%3D%3D&channel=share",

]
BASE = "https://mall.tellhowdm.cn"
INTERVAL = 2


# =============================================================

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


def get_jsessionid(base_url, user_id, channel):
    """访问主页获取 JSESSIONID"""
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:146.0) Gecko/20100101 Firefox/146.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    })
    resp = session.get(f"{base_url}/activity/act67/open/home",
                       params={"openid": user_id, "channel": channel} if user_id else {"channel": channel},
                       timeout=10)
    jsessionid = session.cookies.get("JSESSIONID")
    return session, jsessionid


def query_init(base_url, user_id, channel, is_openid, jsessionid):
    """查询签到状态（init 接口）"""
    url = f"{base_url}/activity/act67/init"
    params = {"channel": channel}
    if is_openid:
        params["openid"] = user_id
    else:
        params["terminalId"] = user_id

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:146.0) Gecko/20100101 Firefox/146.0",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Referer": f"{base_url}/activity/act67/open/home?{('openid' if is_openid else 'terminalId')}={user_id}&channel={channel}",
        "X-Requested-With": "XMLHttpRequest",
        "Cookie": f"JSESSIONID={jsessionid}"
    }
    resp = requests.get(url, params=params, headers=headers, timeout=10)
    return resp


def do_sign(base_url, user_id, channel, is_openid, jsessionid):
    """执行签到"""
    url = f"{base_url}/activity/newYear20/signed"
    params = {"actId": "67", "channel": channel}
    if is_openid:
        params["openid"] = user_id
    else:
        params["terminalId"] = user_id

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:146.0) Gecko/20100101 Firefox/146.0",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Referer": f"{base_url}/activity/act67/open/home?{('openid' if is_openid else 'terminalId')}={user_id}&channel={channel}",
        "X-Requested-With": "XMLHttpRequest",
        "Cookie": f"JSESSIONID={jsessionid}"
    }
    resp = requests.get(url, params=params, headers=headers, timeout=10)
    return resp


def query_vip_info(base_url, user_id, channel, is_openid, jsessionid):
    """查询VIP信息（获取手机号等）"""
    url = f"{base_url}/activity/vip/book2/queryByBossAll"
    params = {"channel": channel}
    if is_openid:
        params["openid"] = user_id
    else:
        params["terminalId"] = user_id

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:146.0) Gecko/20100101 Firefox/146.0",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Referer": f"{base_url}/activity/act67/open/home?{('openid' if is_openid else 'terminalId')}={user_id}&channel={channel}",
        "X-Requested-With": "XMLHttpRequest",
        "Cookie": f"JSESSIONID={jsessionid}"
    }
    resp = requests.get(url, params=params, headers=headers, timeout=10)
    return resp


def process_one(url, index, total):
    print(f"\n🔹 处理第 {index + 1}/{total} 个链接")
    print(f"🔗 {url}")

    user_id, channel, is_openid = parse_identifier(url)
    if not user_id:
        print("❌ 未找到用户标识，跳过")
        return

    id_type = "openid" if is_openid else "terminalId"
    print(f"🔑 使用 {id_type}: {user_id}")

    # 获取 JSESSIONID
    session, jsessionid = get_jsessionid(BASE, user_id, channel)
    if not jsessionid:
        print("⚠️ 未能获取 JSESSIONID，尝试使用空值继续...")
        jsessionid = ""

    print(f"🍪 JSESSIONID: {jsessionid or '未获取'}")

    # 1. 查询签到状态
    resp_init = query_init(BASE, user_id, channel, is_openid, jsessionid)
    print(f"📡 状态查询响应码: {resp_init.status_code}")

    try:
        init_data = resp_init.json()
        status = init_data.get('statusCode')
        if status is None:
            status = init_data.get('code')
        if status != 0:
            print(f"⚠️ 查询状态失败: {init_data.get('statusDesc', init_data.get('msg', '未知错误'))}")
            return
        data = init_data.get('data', {})
        signed = data.get('signed', '0')
        week_num = data.get('weekNum', 0)
        luck_count = data.get('luckCount', 0)
    except Exception as e:
        print(f"⚠️ 解析状态查询响应失败: {e}")
        print(f"   响应原文: {resp_init.text[:200]}")
        return

    # 2. 判断签到状态
    if str(signed) == "1":
        print(f"✅ 今日已签到  \n连续签到: {week_num}天  当前金币: {luck_count}")
    else:
        print(f"ℹ️ 今日未签到，即将执行签到...")
        resp_sign = do_sign(BASE, user_id, channel, is_openid, jsessionid)
        print(f"📡 签到响应码: {resp_sign.status_code}")
        try:
            sign_data = resp_sign.json()
            if sign_data.get('statusCode') == 0:
                d = sign_data.get('data', {})
                print(f"✅ 签到成功")
                print(f"   连续签到: {d.get('weekNum', 0)} 天  当前金币: {d.get('luckCount', 0)}")
                luck_count = d.get('luckCount', luck_count)
            else:
                print(f"⚠️ 签到失败: {sign_data.get('statusDesc', '未知错误')}")
        except Exception as e:
            print(f"⚠️ 解析签到响应失败: {e}")
            print(f"   响应原文: {resp_sign.text[:200]}")

    # 3. 查询VIP信息（获取手机号）
    resp_vip = query_vip_info(BASE, user_id, channel, is_openid, jsessionid)
    print(f"📡 VIP信息响应码: {resp_vip.status_code}")
    phone = "未获取"
    try:
        vip_data = resp_vip.json()
        if vip_data.get('retCode') == "0":
            phone = vip_data.get('phone', '未获取')
            print(f"📱 手机号: {phone}")
        else:
            print(f"⚠️ VIP信息查询失败: {vip_data.get('msg', '未知错误')}")
    except Exception as e:
        print(f"⚠️ 解析VIP信息失败: {e}")
        print(f"   响应原文: {resp_vip.text[:200]}")

    # 4. 最终汇总显示（手机号 + 金币 + 签到状态）
    status_text = "已签到" if str(signed) == "1" else "未签到"
    print(f"\n📊 最终结果：手机号 {phone}  金币 {luck_count}  签到状态 {status_text}")


def detect_and_close_browser():
    """自动检测当前运行的浏览器并关闭"""
    browser_names = ['chrome', 'msedge', 'firefox', 'opera', 'brave', 'vivaldi']
    try:
        result = subprocess.run(['tasklist'], capture_output=True, text=True, encoding='gbk')
        task_output = result.stdout.lower()
        closed = []
        for browser in browser_names:
            if f"{browser}.exe" in task_output:
                subprocess.run(['taskkill', '/f', '/im', f'{browser}.exe'],
                               capture_output=True)
                closed.append(browser)
        return closed
    except Exception as e:
        print(f"⚠️ 检测浏览器失败: {e}")
        return []


def main():
    total = len(LINK_LIST)
    if total == 0:
        print("⚠️ 链接列表为空，请添加链接")
        return

    # 1. 先用浏览器打开所有链接
    print(f"🌐 正在使用默认浏览器打开 {total} 个链接...")
    for url in LINK_LIST:
        webbrowser.open(url)

    # 2. 等待10秒
    print("⏳ 等待10秒，请检查浏览器页面...")
    time.sleep(4)

    # 3. 自动检测并关闭浏览器
    print("🧹 正在自动检测并关闭浏览器...")
    closed = detect_and_close_browser()
    if closed:
        print(f"✅ 已关闭: {', '.join(closed)}")
    else:
        print("⚠️ 未检测到运行中的浏览器")

    # 4. 开始执行签到逻辑
    print(f"\n📋 开始执行签到脚本，共 {total} 个链接，间隔 {INTERVAL} 秒")
    for i, url in enumerate(LINK_LIST):
        process_one(url, i, total)
        if i < total - 1:
            print(f"⏳ 等待 {INTERVAL} 秒...")
            time.sleep(INTERVAL)

    print("\n🎉 全部处理完成！")


if __name__ == "__main__":
    main()
