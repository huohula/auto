import requests
import json
import time
import os
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 从 GitHub Secrets 环境变量读取
GLOBAL_DS_TOKEN = os.environ.get("DS_TOKEN", "")
ACCOUNTS_RAW = os.environ.get("ACCOUNTS", "")

# 解析账号信息，格式：账号名1|Cookie1;;;账号名2|Cookie2
ACCOUNTS = []
if ACCOUNTS_RAW:
    for item in ACCOUNTS_RAW.split(";;;"):
        parts = item.split("|", 1)
        if len(parts) == 2:
            ACCOUNTS.append({"name": parts[0], "cookie": parts[1]})

# 接口地址
BASE_URL = "https://n.cmread.com"
QUERY_URL = f"{BASE_URL}/nap/p/nldh2026.jsp"
SIGNIN_URL = f"{BASE_URL}/nap/a/ms.sns.snsService/signinAction.json"

# 请求头
QUERY_HEADERS = {
    "Host": "n.cmread.com",
    "Connection": "keep-alive",
    "Accept": "*/*",
    "X-Requested-With": "XMLHttpRequest",
    "User-Agent": "CMREADBC_Android_1600*2560_V12.10.0(1600*2560;HUAWEI;DBY-W09;Android 12;cn;JSBridge=1.0;https;normalTextMode) AndroidAmberV2.9.26",
    "x-tptoken": "fU7dnB9bXm4/A034wOmU3iPwMQG0fWyF3985QJDShnuvChb6zk3zY16cMjtecS5D",
    "Referer": "https://n.cmread.com/nap/p/qdnew.jsp?hideAllTitleBar=1&titleTransparent=3&cm=M8010001",
}

SIGN_HEADERS = {
    "Host": "n.cmread.com",
    "Connection": "keep-alive",
    "Accept": "*/*",
    "X-Requested-With": "XMLHttpRequest",
    "User-Agent": "CMREADBC_Android_1080*2073_V12.12.0(1080*2073;HUAWEI;ANA-AN00;Android 12;cn;JSBridge=1.0;https;normalTextMode) AndroidAmberV2.9.26",
    "x-tptoken": "f1vXfg+PoK7x/PLKc7l/BWfFrV5OGPMqS8zpvun8Q8q+7CkeIi75QZ0E0Vu+CCA/",
    "Referer": "https://n.cmread.com/nap/p/qdnew.jsp?hideAllTitleBar=1&titleTransparent=3&cm=M801005N",
}

# 辅助函数
def parse_cookie(cookie_str):
    return dict(item.strip().split('=', 1) for item in cookie_str.split(';') if '=' in item)

def query_balance(cookie, ds_token, name):
    session = requests.Session()
    session.cookies.update(parse_cookie(cookie))
    try:
        resp = session.get(QUERY_URL, headers=QUERY_HEADERS, params={"dSDaipTi": ds_token}, verify=False, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            for chip in data.get("myLeftChipsData", []):
                if chip.get("chipName") == "悦看专属AI豆":
                    print(f"[{name}] ✅ AI豆余额: {chip.get('leftAmount')}")
                    return
            print(f"[{name}] ⚠️ 未找到AI豆余额字段")
        else:
            print(f"[{name}] ❌ 查询余额失败，状态码 {resp.status_code}")
    except Exception as e:
        print(f"[{name}] ❌ 查询余额异常: {e}")

def do_signin(cookie, ds_token, name):
    session = requests.Session()
    session.cookies.update(parse_cookie(cookie))
    try:
        resp = session.get(SIGNIN_URL, headers=SIGN_HEADERS, params={"dSDaipTi": ds_token}, verify=False, timeout=10)
        result = resp.json()
        print(f"[{name}] 签到响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
        if result.get("status") in ("0", "5109", "200"):
            print(f"[{name}] ✅ 签到成功（或已签到）")
        else:
            print(f"[{name}] ❌ 签到失败: {result.get('message')}")
    except Exception as e:
        print(f"[{name}] ❌ 签到异常: {e}")

# 主程序
def main():
    if not GLOBAL_DS_TOKEN:
        print("❌ 未设置 DS_TOKEN 环境变量")
        return
    if not ACCOUNTS:
        print("❌ 未设置 ACCOUNTS 环境变量")
        return

    for account in ACCOUNTS:
        name = account["name"]
        cookie = account["cookie"]
        print(f"===== 处理账号: {name} =====")
        query_balance(cookie, GLOBAL_DS_TOKEN, name)
        do_signin(cookie, GLOBAL_DS_TOKEN, name)
        time.sleep(2)

if __name__ == "__main__":
    main()
