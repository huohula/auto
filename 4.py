#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
泰豪商城 act67 每日签到脚本（逆向稳定版）
逆向依据：act67.js + library.js(commons) 完整前端流程

与原脚本的核心差异：
  1. signed 请求只带 actId + 认证标识(openid/terminalId)，不带 channel
     （前端 addLoginParmarToUrls 只注入 auth 字段，不注入 channel）
  2. 不手动加 X-Requested-With（纯 $.getJSON 不带此头）
  3. 签到前检测活动状态，活动已结束时直接提示
  4. 失败时输出完整响应头+响应体，便于定位服务端问题
  5. 指数退避重试，避免加剧服务端限流
  6. 支持单次诊断模式（--diag），输出完整请求/响应细节

当前已知问题：
  活动页面标注活动时间为 2020年1月12日至3月18日。
  signed 接口当前对所有请求（含不带用户标识的请求）统一返回：
    {"statusCode":1,"statusDesc":"请稍后再试~","data":{}}
  这表明是服务端层面的拒绝（活动关闭/下游异常/IP风控），而非请求格式问题。
  建议先在微信/和我信APP内手动签到验证服务端是否正常。
"""

import requests
import time
import sys
import argparse
from urllib.parse import urlparse, parse_qs, quote

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
ACT_ID = "67"
INTERVAL = 5          # 账号间间隔（秒）
SIGN_RETRY = 2        # 签到失败重试次数
TIMEOUT = 20
# ====================

# 微信内 UA（最接近真实环境）
UA = ("Mozilla/5.0 (Linux; Android 10; MI 9 Build/QKQ1.190825.002; wv) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 "
      "Chrome/91.0.4472.120 Mobile Safari/537.36 "
      "MicroMessenger/8.0.40.2420(0x28002837) WeChat/arm64 Weixin "
      "NetType/WIFI Language/zh_CN ABI/arm64")

VIP_FLAGS = {
    "flag1": "次元君会员",
    "flag5": "次元皇会员",
    "flag5_12": "次元皇年会员",
    "flag10": "次元俱乐部会员",
    "flag25": "高阶会员",
}


def parse_identifier(url):
    """从分享链接提取用户标识，保持原始 URL 编码（不解码）"""
    parsed = urlparse(url)
    # 用原始 query 字符串提取，避免 parse_qs 自动解码
    raw_query = parsed.query
    openid = None
    terminal_id = None
    channel = "share"
    for pair in raw_query.split("&"):
        if "=" in pair:
            k, v = pair.split("=", 1)
            if k == "openid":
                openid = v
            elif k == "terminalId":
                terminal_id = v
            elif k == "channel":
                channel = v
    if openid:
        return openid, channel, True
    return terminal_id, channel, False


def build_referer(uid, channel, is_openid):
    id_key = "openid" if is_openid else "terminalId"
    return f"{BASE}/activity/act67/open/home?{id_key}={uid}&channel={channel}"


def create_session(uid, channel, is_openid, diag=False):
    """访问主页建立会话，获取 JSESSIONID"""
    s = requests.Session()
    s.headers.update({"User-Agent": UA})
    id_key = "openid" if is_openid else "terminalId"
    params = {id_key: uid, "channel": channel}
    resp = s.get(f"{BASE}/activity/act67/open/home",
                 params=params, timeout=TIMEOUT, allow_redirects=True)
    jsid = s.cookies.get("JSESSIONID")
    if diag:
        print(f"  [诊断] 主页 HTTP {resp.status_code}")
        print(f"  [诊断] JSESSIONID={jsid}")
        print(f"  [诊断] 响应 Set-Cookie: {resp.headers.get('Set-Cookie', 'none')}")
    return s, jsid


def ajax_get(session, path, uid, channel, is_openid, extra_params=None, diag=False, label=""):
    """
    模拟前端 $.getJSON：
    - 不带 X-Requested-With
    - Accept: application/json, text/javascript, */*; q=0.01
    - 带 Referer
    """
    id_key = "openid" if is_openid else "terminalId"
    params = {id_key: uid, "channel": channel}
    if extra_params:
        params.update(extra_params)
    headers = {
        "User-Agent": UA,
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Referer": build_referer(uid, channel, is_openid),
    }
    resp = session.get(f"{BASE}{path}", params=params, headers=headers, timeout=TIMEOUT)
    try:
        data = resp.json()
    except Exception:
        data = {"_raw": resp.text[:500]}
    if diag:
        print(f"  [诊断][{label}] URL: {resp.url}")
        print(f"  [诊断][{label}] 请求头: {dict(resp.request.headers)}")
        print(f"  [诊断][{label}] 响应状态: {resp.status_code}")
        print(f"  [诊断][{label}] 响应头: {dict(resp.headers)}")
        print(f"  [诊断][{label}] 响应体: {resp.text[:500]}")
    return resp.status_code, data


def get_user_info(session, uid, channel, is_openid, diag=False):
    sc, data = ajax_get(session, "/activity/data/userInfo", uid, channel, is_openid, diag=diag, label="userInfo")
    if sc == 200 and isinstance(data, dict) and "userInfo" in data:
        ui = data["userInfo"]
        return {
            "id": ui.get("id", ""),
            "nickName": ui.get("nickName", ""),
            "menbType": ui.get("menbType", ""),
        }
    return None


def get_club_info(session, uid, channel, is_openid, diag=False):
    sc, data = ajax_get(session, "/activity/vip/book2/queryByBossAll",
                         uid, channel, is_openid, diag=diag, label="clubInfo")
    if sc == 200 and isinstance(data, dict) and data.get("retCode") == "0":
        club = data.get("data", {})
        vip_types = [name for flag, name in VIP_FLAGS.items()
                     if str(club.get(flag, 0)) == "1"]
        return {
            "phone": data.get("phone", "未知"),
            "vip_types": vip_types if vip_types else ["非会员"],
            "is_vip": any(str(club.get(flag, 0)) == "1" for flag in VIP_FLAGS),
        }
    return None


def get_sign_status(session, uid, channel, is_openid, diag=False):
    sc, data = ajax_get(session, "/activity/act67/init", uid, channel, is_openid, diag=diag, label="init")
    if sc == 200 and isinstance(data, dict) and data.get("statusCode") == 0:
        d = data.get("data", {})
        return {
            "signed": str(d.get("signed", "0")) == "1",
            "weekNum": d.get("weekNum", 0),
            "luckCount": d.get("luckCount", 0),
        }
    return None


def do_sign(session, uid, channel, is_openid, diag=False):
    """
    执行签到，严格模拟前端：
    - URL: /activity/newYear20/signed?actId=67 + auth参数(openid/terminalId)
    - 不带 channel（前端 addLoginParmarToUrls 不注入 channel）
    - GET 请求，纯 $.getJSON 风格
    """
    id_key = "openid" if is_openid else "terminalId"
    params = {"actId": ACT_ID, id_key: uid}
    headers = {
        "User-Agent": UA,
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Referer": build_referer(uid, channel, is_openid),
    }
    resp = session.get(f"{BASE}/activity/newYear20/signed",
                       params=params, headers=headers, timeout=TIMEOUT)
    if diag:
        print(f"  [诊断][signed] URL: {resp.url}")
        print(f"  [诊断][signed] 请求头: {dict(resp.request.headers)}")
        print(f"  [诊断][signed] 响应状态: {resp.status_code}")
        print(f"  [诊断][signed] 响应头: {dict(resp.headers)}")
        print(f"  [诊断][signed] 响应体: {resp.text[:500]}")

    if resp.status_code != 200:
        return False, f"HTTP {resp.status_code}", {}
    try:
        data = resp.json()
    except Exception:
        return False, f"非JSON响应: {resp.text[:200]}", {}

    code = data.get("statusCode")
    if code == 0:
        d = data.get("data", {})
        return True, "签到成功", d
    desc = data.get("statusDesc", "未知错误")
    return False, desc, data.get("data", {})


def process_one(url, index, total, diag=False):
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
    session, jsid = create_session(uid, channel, is_openid, diag=diag)
    if not jsid:
        print("  [警告] 未获取到 JSESSIONID，继续尝试")
    else:
        print(f"  [会话] JSESSIONID={jsid}")

    # 2. userInfo（前端必调，建立用户会话绑定）
    user_info = get_user_info(session, uid, channel, is_openid, diag=diag)
    if user_info:
        print(f"  [用户] ID={user_info['id']}  会员等级={user_info['menbType']}")
    else:
        print(f"  [用户] userInfo 获取失败")

    # 3. clubInfo（会员信息 + 手机号）
    club = get_club_info(session, uid, channel, is_openid, diag=diag)
    if club:
        print(f"  [会员] 手机号={club['phone']}  类型={' / '.join(club['vip_types'])}")
    else:
        print(f"  [会员] clubInfo 获取失败")
        club = {"phone": "未知", "vip_types": ["未知"], "is_vip": True}

    # 4. 查询签到状态
    status = get_sign_status(session, uid, channel, is_openid, diag=diag)
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

    # 5. 未签到则执行签到（指数退避重试）
    if not status["signed"]:
        if not club["is_vip"]:
            print(f"  [签到] 非会员，无法签到")
            result["sign_result"] = "not_vip"
        else:
            for attempt in range(1, SIGN_RETRY + 2):
                ok, msg, data = do_sign(session, uid, channel, is_openid,
                                         diag=(diag and attempt == 1))
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
                    # "请稍后再试" 可能是服务端限流，增加等待
                    if "稍后" in msg and attempt <= SIGN_RETRY:
                        wait = 5 * attempt  # 指数退避：5s, 10s
                        print(f"         服务端限流提示，{wait}秒后重试...")
                        time.sleep(wait)
                    elif attempt <= SIGN_RETRY:
                        time.sleep(3)
            else:
                result["sign_result"] = "failed"
                print(f"  [签到] 重试{SIGN_RETRY}次后仍失败")
                print(f"  [提示] 该接口当前统一返回'请稍后再试~'，可能是活动已结束或服务端限制")
                print(f"  [提示] 请在微信/和我信APP内手动签到验证服务端状态")

    # 6. 汇总
    sign_text = {"already": "已签到", "success": "签到成功",
                 "failed": "签到失败", "not_vip": "非会员无法签到"}
    print(f"\n  >>> 汇总: 手机号 {result['phone']} | {result['vip']} | "
          f"金币 {result['luckCount']} | 连续 {result['weekNum']}天 | "
          f"{sign_text.get(result['sign_result'], result['sign_result'])}")
    return result


def main():
    parser = argparse.ArgumentParser(description="泰豪商城 act67 每日签到")
    parser.add_argument("--diag", action="store_true", help="诊断模式：输出完整请求/响应细节")
    parser.add_argument("--only", type=int, default=0, help="只处理第N个账号（1-based）")
    args = parser.parse_args()

    links = LINK_LIST
    if args.only and 1 <= args.only <= len(links):
        links = [links[args.only - 1]]
        print(f"[仅处理第 {args.only} 个账号]")

    total = len(links)
    if total == 0:
        print("链接列表为空")
        return

    print(f"泰豪商城 act67 签到  共 {total} 个账号  间隔 {INTERVAL}秒")
    print(f"开始时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    if args.diag:
        print("*** 诊断模式已开启 ***")

    results = []
    for i, url in enumerate(links):
        r = process_one(url, i, total, diag=args.diag)
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
