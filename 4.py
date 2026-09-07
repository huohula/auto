#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
泰豪商城 act67 每日签到脚本（优化版）
逆向依据：前端 act67.js + commons.js 完整流程
  主页 -> userInfo -> clubInfo -> init -> signed
修复点：
  1. get_jsessionid 参数名 bug（terminalId 被误传为 openid）
  2. 全程复用同一 session（原脚本只手动传 JSESSIONID）
  3. 补全前端必调的 userInfo 接口（建立服务端用户会话绑定）
  4. 签到前校验会员状态（flag1/flag5/flag5_12/flag10/flag25）
  5. 签到失败自动重试（间隔递增）
  6. 移除无效的浏览器打开/关闭逻辑
  7. 完整输出：手机号、会员类型、金币、连续天数、签到状态
"""

import requests
import time
import json
import sys
from urllib.parse import urlparse, parse_qs

# ===== 用户配置 =====
LINK_LIST = [
    "http://mall.tellhowdm.cn/activity/act67/open/home?openid=obJT21TdFBT_uX8ZAKgEBxaipr68&channel=share",
    "http://mall.tellhowdm.cn/activity/act67/open/home?openid=obJT21aOxa_lJMPrq8djUbtF8zxY&channel=share",
    "https://mall.tellhowdm.cn/activity/act67/open/home?terminalId=Uld7lY83AUzNxc69qzzMLA%3D%3D&channel=share",
    "https://mall.tellhowdm.cn/activity/act67/open/home?terminalId=DD3amwP0iKtdsYM3ogVcag%3D%3D&channel=share",
    "https://mall.tellhowdm.cn/activity/act67/open/home?terminalId=9WqaO4BKBzLUXDK4y%2BqprQ%3D%3D&channel=share",
    "https://mall.tellhowdm.cn/activity/act67/open/home?terminalId=o8i7fm%2BnOLFdsYM3ogVcag%3D%3D&channel=share",
]
BASE = "https://mall.tellhowdm.cn"
INTERVAL = 3          # 账号间间隔（秒），避免服务端限流
SIGN_RETRY = 2        # 签到失败重试次数
RETRY_DELAY = 3       # 重试间隔（秒）
TIMEOUT = 15
# ====================

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:146.0) "
      "Gecko/20100101 Firefox/146.0")

VIP_FLAGS = {
    "flag1": "次元君会员",
    "flag5": "次元皇会员",
    "flag5_12": "次元皇年会员",
    "flag10": "次元俱乐部会员",
    "flag25": "高阶会员",
}


def parse_identifier(url):
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    openid = params.get("openid", [None])[0]
    terminal_id = params.get("terminalId", [None])[0]
    channel = params.get("channel", ["share"])[0]
    if openid:
        return openid, channel, True
    return terminal_id, channel, False


def build_headers(uid, channel, is_openid, ajax=False):
    h = {
        "User-Agent": UA,
        "Accept": ("application/json, text/javascript, */*; q=0.01"
                   if ajax else
                   "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"),
    }
    if ajax:
        id_key = "openid" if is_openid else "terminalId"
        h["X-Requested-With"] = "XMLHttpRequest"
        h["Referer"] = (f"{BASE}/activity/act67/open/home?"
                        f"{id_key}={uid}&channel={channel}")
    return h


def create_session(uid, channel, is_openid):
    """访问主页建立会话，使用正确的参数名"""
    s = requests.Session()
    s.headers.update(build_headers(uid, channel, is_openid))
    params = {"channel": channel}
    if is_openid:
        params["openid"] = uid
    else:
        params["terminalId"] = uid
    resp = s.get(f"{BASE}/activity/act67/open/home",
                 params=params, timeout=TIMEOUT, allow_redirects=True)
    return s, resp.status_code, s.cookies.get("JSESSIONID")


def api_get(session, path, uid, channel, is_openid, extra_params=None):
    """统一 AJAX GET，复用 session 的 cookie"""
    params = {"channel": channel}
    if is_openid:
        params["openid"] = uid
    else:
        params["terminalId"] = uid
    if extra_params:
        params.update(extra_params)
    headers = build_headers(uid, channel, is_openid, ajax=True)
    resp = session.get(f"{BASE}{path}", params=params, headers=headers, timeout=TIMEOUT)
    try:
        return resp.status_code, resp.json()
    except Exception:
        return resp.status_code, {"_raw": resp.text[:300]}


def get_user_info(session, uid, channel, is_openid):
    """前端流程第一步：建立用户会话绑定"""
    sc, data = api_get(session, "/activity/data/userInfo", uid, channel, is_openid)
    if sc == 200 and isinstance(data, dict) and "userInfo" in data:
        ui = data["userInfo"]
        return {
            "id": ui.get("id", ""),
            "nickName": ui.get("nickName", ""),
            "menbType": ui.get("menbType", ""),
            "regTime": ui.get("regTime", ""),
        }
    return None


def get_club_info(session, uid, channel, is_openid):
    """前端流程第二步：获取会员信息与手机号"""
    sc, data = api_get(session, "/activity/vip/book2/queryByBossAll",
                       uid, channel, is_openid)
    if sc == 200 and isinstance(data, dict) and data.get("retCode") == "0":
        club = data.get("data", {})
        vip_types = [name for flag, name in VIP_FLAGS.items()
                     if str(club.get(flag, 0)) == "1"]
        return {
            "phone": data.get("phone", "未知"),
            "vip_types": vip_types if vip_types else ["非会员"],
            "is_vip": any(str(club.get(flag, 0)) == "1" for flag in VIP_FLAGS),
            "raw": club,
        }
    return None


def get_sign_status(session, uid, channel, is_openid):
    """前端流程第三步：查询签到状态"""
    sc, data = api_get(session, "/activity/act67/init", uid, channel, is_openid)
    if sc == 200 and isinstance(data, dict) and data.get("statusCode") == 0:
        d = data.get("data", {})
        return {
            "signed": str(d.get("signed", "0")) == "1",
            "weekNum": d.get("weekNum", 0),
            "luckCount": d.get("luckCount", 0),
        }
    return None


def do_sign(session, uid, channel, is_openid):
    """执行签到，返回 (success, message, data)"""
    sc, data = api_get(session, "/activity/newYear20/signed",
                       uid, channel, is_openid,
                       extra_params={"actId": "67"})
    if sc != 200 or not isinstance(data, dict):
        return False, f"HTTP {sc}", {}
    code = data.get("statusCode")
    if code == 0:
        d = data.get("data", {})
        return True, "签到成功", d
    # statusCode=1 且 desc 含"稍后"通常是已签到或限流
    desc = data.get("statusDesc", "未知错误")
    return False, desc, data.get("data", {})


def process_one(url, index, total):
    uid, channel, is_openid = parse_identifier(url)
    id_type = "openid" if is_openid else "terminalId"
    tag = f"[{index + 1}/{total}]"

    print(f"\n{'='*64}")
    print(f"{tag} 标识类型: {id_type}  值: {uid}")
    print(f"{'='*64}")

    if not uid:
        print("  [跳过] 未提取到用户标识")
        return {"uid": uid, "error": "no identifier"}

    # 1. 建立会话
    session, sc, jsid = create_session(uid, channel, is_openid)
    if not jsid:
        print(f"  [警告] 未获取到 JSESSIONID，继续尝试")
    else:
        print(f"  [会话] JSESSIONID={jsid}  (HTTP {sc})")

    # 2. userInfo（前端必调，建立用户会话绑定）
    user_info = get_user_info(session, uid, channel, is_openid)
    if user_info:
        print(f"  [用户] ID={user_info['id']}  会员等级={user_info['menbType']}  "
              f"注册时间={user_info['regTime']}")
    else:
        print(f"  [用户] userInfo 获取失败（不影响签到，继续）")

    # 3. clubInfo（会员信息 + 手机号）
    club = get_club_info(session, uid, channel, is_openid)
    if club:
        print(f"  [会员] 手机号={club['phone']}  类型={' / '.join(club['vip_types'])}")
    else:
        print(f"  [会员] clubInfo 获取失败")
        club = {"phone": "未知", "vip_types": ["未知"], "is_vip": True}

    # 4. 查询签到状态
    status = get_sign_status(session, uid, channel, is_openid)
    if not status:
        print(f"  [状态] init 接口返回异常，跳过")
        return {"uid": uid, "phone": club["phone"], "error": "init failed"}

    print(f"  [状态] 今日{'已签到' if status['signed'] else '未签到'}  "
          f"连续签到={status['weekNum']}天  金币={status['luckCount']}")

    result = {
        "uid": uid,
        "phone": club["phone"],
        "vip": " / ".join(club["vip_types"]),
        "weekNum": status["weekNum"],
        "luckCount": status["luckCount"],
        "signed": status["signed"],
        "sign_result": "already",
    }

    # 5. 未签到则执行签到（含重试）
    if not status["signed"]:
        if not club["is_vip"]:
            print(f"  [签到] 非会员，无法签到（前端逻辑：非会员点击签到会弹窗提示开通）")
            result["sign_result"] = "not_vip"
        else:
            for attempt in range(1, SIGN_RETRY + 2):
                ok, msg, data = do_sign(session, uid, channel, is_openid)
                if ok:
                    result["signed"] = True
                    result["sign_result"] = "success"
                    result["weekNum"] = data.get("weekNum", status["weekNum"])
                    result["luckCount"] = data.get("luckCount", status["luckCount"])
                    print(f"  [签到] 成功 (第{attempt}次)  "
                          f"连续={result['weekNum']}天  金币={result['luckCount']}")
                    break
                else:
                    print(f"  [签到] 第{attempt}次失败: {msg}")
                    if attempt <= SIGN_RETRY:
                        print(f"         {RETRY_DELAY}秒后重试...")
                        time.sleep(RETRY_DELAY)
            else:
                result["sign_result"] = "failed"
                print(f"  [签到] 重试{SIGN_RETRY}次后仍失败")

    # 6. 汇总
    sign_text = {"already": "已签到", "success": "签到成功",
                 "failed": "签到失败", "not_vip": "非会员无法签到"}
    print(f"\n  >>> 汇总: 手机号 {result['phone']} | {result['vip']} | "
          f"金币 {result['luckCount']} | 连续 {result['weekNum']}天 | "
          f"{sign_text.get(result['sign_result'], result['sign_result'])}")
    return result


def main():
    total = len(LINK_LIST)
    if total == 0:
        print("链接列表为空")
        return

    print(f"泰豪商城 act67 签到  共 {total} 个账号  间隔 {INTERVAL}秒")
    print(f"开始时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    results = []
    for i, url in enumerate(LINK_LIST):
        r = process_one(url, i, total)
        results.append(r)
        if i < total - 1:
            time.sleep(INTERVAL)

    # 最终汇总表
    print(f"\n{'='*64}")
    print(f"全部处理完成  结束时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*64}")
    print(f"{'#':<4}{'手机号':<14}{'会员类型':<16}{'金币':<8}{'连续天数':<8}{'结果'}")
    print(f"{'-'*64}")
    success_count = 0
    for i, r in enumerate(results):
        if r.get("signed"):
            success_count += 1
        sign_text = {"already": "已签到", "success": "新签到",
                     "failed": "失败", "not_vip": "非会员"}
        print(f"{i+1:<4}{r.get('phone','?'):<14}{r.get('vip','?'):<16}"
              f"{str(r.get('luckCount','?')):<8}{str(r.get('weekNum','?')):<8}"
              f"{sign_text.get(r.get('sign_result','?'), r.get('sign_result','?'))}")
    print(f"{'-'*64}")
    print(f"已签到/成功: {success_count}/{total}")


if __name__ == "__main__":
    main()
