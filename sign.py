#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
咪咕阅读 nldh2026 签到脚本（优化版）
输出：签到获得豆子、签到状态、签到前后总余额
"""

import requests
import json
import time
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ================= 全局配置 =================
GLOBAL_DS_TOKEN = "0rDtJoalqEm.aBVuKondEHsufa4dGzVEmu78dkBcS3inuhSmUTwLsWW2apdztrq6cppNkdee6zvq95HzebasiAgAXnIzW.PBUarZvP69I9GYyMsRF9qhQPa"

ACCOUNTS = [
    {"name": "6881", "cookie": "cm=M8010001; _clientid=e85de977c7f9e4e56bec216c851e5dd5; _authtoken=cloud152290a30475422a8cba189b0e5eb455; iszIdvaqC1gOO=60vA1ey98RpkXIpZhj5BKnSOg0RsrsMxlhftuyiOPICVfLPBVP2gWxmsGQqH4.d.C8qC.G1XVTMGzzBmIBxk8nfq; mg_uem_user_id_eb94d3ee70624bb5ac15ee1a9a594cb4=904379e7-2269-4a7d-a2a6-05c67791ff08; cm=M8010001; JSESSIONID=ED5C82102C4A8D9B0D6BEBF2A9D92D69; _at=AXrh5BTHVztQOSqNi1N0YRNex+S9LsGpc2KnJCJNPnlGJkL+SA==; _ts=1788596526743; iszIdvaqC1gOP=0gAHhu0HkM_6h.CO1Tk9jz5d7dgtQ3HKfZuUaRZUKtEhfs99j2TF39SYrIAZnGmWwWlbUHvzjBsk.4ElZeMQES96O3VN8AW6ASVtUzuAqKsmSwaQHNu04T741ai0MQJ.XgVYJz1w2D0oyMce_MTkA6HTrVJRiRwsIhFZQwZ0eSwuZBeQCiM7SVUOzt5Kmggc4Ns1GWAusTkhEHxz6raUMRLO679XQ1od151P_RF3nui5wGvfpD2Mgv9bK7ykXLq4HXk6Svxoo7V..yU.C34wXrydib0V3xyX23y0YQwzs7OwVh7jf7GxOZTUFpFNafRfV65t13UE6xg1BKPdvwIStnB5kCNXF__k.HxNgA1ce3ayrh0vdJA8yjCteqg.T7DfuZS6wtb6RQwfN0FpZ_mwNgP9avolPRgpFhCyqUiS51y9"},
    {"name": "7792", "cookie": "mg_uem_user_id_eb94d3ee70624bb5ac15ee1a9a594cb4=ccb8f920-2d93-4fe2-b291-ce683207e08b; cm=M801005N; _clientid=ed8e5665bb5127aa74910ed885d873d5; _authtoken=cloude0740445f173430784f7f6bb51e0385f; iszIdvaqC1gOO=60eaxum1WMto_sz7hptG_ik.miXYgetH3AT3Eyup4i4t1xhhFVKWzlnWoL4m7jqxseF.3cVREKytnQRpBIfieeOa; cm=M801005N; JSESSIONID=C58CC80B50560E1319A9BCADAF01C511; _at=Ty1WlNePG/GMbqs81gcA/l+4ZloGZtYeIPfX8wEfc1DF288I4Q==; _ts=1788597958318; iszIdvaqC1gOP=0nbkoEXnf_rH7r_bVjWoxVHPY54V9jrbqcHdacr9GzWsSi3epsNhyXIEWnECp8yvz7Opr7liaHCy3PZKBthVR96jCIiZn92edIwgrOeL60l4X_V5M8wKQRaowGPAUIzIPc65ITmAAb6Zw3_2Af_jYXYYwUVJ4KZQvuIQ3ua92g2ukO.IuzoUg_C0dZ891aYRhzHzWPuxIk_av2ogExU7OcIvM7ppjq8eP0BX0E5L7b1rXi_PHsrhUJIToxtSGJxHQ4vmMKRqoW54x5LMeXh3deQOqKeb_Q_EC1zBMsyWcDudREKxbPWF80aIn9j8jHa.f4Y0.tQdf5cVKpFM3YV9pdXz4Saqx58_vLwaKfW6Ek5vGmOgVu8T1XhuMWTVy.p7J_Tb9xEU0iKcE4BMa8rOsMsA_jmEdwYvQiw_tShInXRZ"},
    {"name": "0130", "cookie": "mg_uem_user_id_eb94d3ee70624bb5ac15ee1a9a594cb4=fd5acdf1-7f9b-4f8f-beed-20ef77bb5ca7; cm=M801005N; _clientid=f91721ec4640c92dc76799f42581651d; _authtoken=cloudc49dff665ea242fe8cb16b60d1dadf98; iszIdvaqC1gOO=60SZIhqtrY.L4fyHWdqhG.fPV86Nz9UIqVRw3pd0PbRJjekn5tdVCBfRWqAsai6Ucuz4iOAFGhl5jY4CHjColfMG; JSESSIONID=61320D0BD548A19A513707B4C6F1143E; _at=9aqqFT312PR5wL5M+JFoa7KP0CgOmpAxth6eL3/oOnecuHmbgA==; _ts=1788598223550; iszIdvaqC1gOP=0cPfQ.oDL8bwLdAab9HiSlP9P0shjPZf1IWM8Z_nELTdjjdhOuTXWgXryhJosB_uPpFWTWdnTFVw0jRSd9dsQDvKge5uRgq_sk7FWljuZYAX0EoiJipy3MMAeHlVQtcTPvEGZDC_6nb.naamogEYQHEuOguiX96.1O0.sAzdLbsiD8uOymsdlWSK96wRHR5CZ7fbz6jvfoDp4LsdSb6ZDbBA1Om1lM7iFa59EdNYCPFV1NvS48MuSWtzLTDGYJ9RZlVp.A8jgnD.UQ3JPOvVkR2Q2y7cKRolEeieZ11gV311a_JKBrRA7v4kwgIe47mYgipZLkcH3MpMP9ddrZv4VFlzOjVQD1Gu.BuMJqe6AJxtbNK7FqMyBUGgfNGSJvM5GnG_DLMbxyoc.3uF37S5sLCRldg3.DdAmNJMTWMwSaSQ"},
    {"name": "6601", "cookie": "mg_uem_user_id_eb94d3ee70624bb5ac15ee1a9a594cb4=f1f8729a-17b3-4751-a0b7-bf64c17dfd21; cm=M801005N; _clientid=cb1bcb985410551655b39b58b4fdd5f4; _authtoken=cloud3c8f3958c2454af3ab0b063f63ff0ade; iszIdvaqC1gOO=60SEp0kZcyLuqRmbTl_HIMI6t8aunzYiu5E.qDXVzWUGgIMwuYqeJ5T8Qf261SPItg_tsP8bPHLsZZ9CzVAcXD0q; JSESSIONID=008BE92DD88ABA77162FF1E9EC6C9765; _at=FrDfP5cz3GhesPrqjkgRVb+lzv/v1VCA+iqLh++gq3OdMvU0lw==; _ts=1788598292698; iszIdvaqC1gOP=0OrY3cLFH3ZYzlIuiJgw.z_AsnBUl8.lo6Mp5kchkUyX0IWhRJ0clO057q5RPFP7HKArAhqQZ7xezaqZU0emFULUFbMStmIa7eHm7Ttk6AF7R20SI0gwJScqCZuW_IlL1tjEqfjZlKcPU73F2kH_8GB8glIXXe5Q.wNZfAmgXzCq8N7AnxnbVvmi7R6BCoZeUbWbvpYfBN8SlcCoJHEMq10745_ah7qeo1LBtM_MG5NQfSAzl0OvymQ7gVxb1nLMKO3oXvL9hQMy0Vstb0z1hv7NiCbZZpJxP85GoYBvXK0CEdAb..BUFWmAXt4ZCvZgm4Q8bJ_QFpGJd6mgQxTj.clQEn.az8lIQPhqjQGNS117W0mmNEtbYHJrqvvnkS3b6.VN_xs.2VVKpCNGjd5sGZO0FclFmizbU0kQGoohbVta"},
    {"name": "7881", "cookie": "JSESSIONID=5F20ADF73816A81C66A7607168AA61F2; _clientid=fc23a6ca9482658ad5df94c24646c793; _authtoken=cloudd7dc873f99f249268beb225aabb0b544; cm=M80100EU; iszIdvaqC1gOO=60HPZfGnEpwzYWkTUxC4lL_TfqWTswj7LhhLLbxVWMxRPsCulsoAVeo0S0DFv7bzWDUAAscHmhG7gdnHQFlQnKIG; mg_uem_user_id_eb94d3ee70624bb5ac15ee1a9a594cb4=9f515499-7f9a-4b24-8c3e-c605a492c1dd; tabIndex=0; WT_FPC=id=2056f342e54c9e4a2b61785873979555:lv=1785873979555:ss=1785873979555; cm=M80100EU; JSESSIONID=FA89C67C88AE123F1E45DC78A1F71842; _at=C4XzwdW66dJxJ+WSojr54WF991LruEHgnmGM9be1UltRlY+u9Q==; _ts=1788651599556; iszIdvaqC1gOP=0HITaZYTSgOiq3YBrpPmpJBIrLEchlUdz3LkcxOQMGcz4gIbjquKS9Nigx4A9RYZmEbQT3hcsAYlm_yJVGlaRGM9X4sou2fRF95afgmRpAeksdQ8X4iiTOEqTyrjEoMqPIeURJq1bKIsZbXH.fJXivy7XCTV_RQ_QUS5OhqyVVglcRCd89aOQ5u5muHH0jufqWwAo8VNszbkos65GI4KrAAng_ZAgyWnHclVKd07uObQj2xSsGVHg1VPaVJs092nrdJaL6Tdd68WzQsXXocQcT_6kk3vxSy9Nkbx5sIScEEDvsLevEkUN0sLqiK015XI1ZPwbailRpvpQaTnZpviCLQI5bPS2D3zalCVkT6iPBu_8bKEI9RT3S0XD5ZTI_5pY"},
    {"name": "7855", "cookie": "mg_uem_user_id_eb94d3ee70624bb5ac15ee1a9a594cb4=872fd9c7-5d38-4b85-9ead-0940fb779972; cm=M801005N; _clientid=a1f3d1873e5e8326ee0085f2f67fb0eb; _authtoken=cloud78b2409c2d144d55af0b4796d4fad66e; iszIdvaqC1gOO=60M4jvOxGwGvRnQjRlqfNeFqeKkmef4CdWU7KlRXARtfTQopz7hmNLr3aF2RdkLIFOat0_mP8QcrZjis4U4KkmLa; JSESSIONID=6D91793E93F30540F92597C7510E5545; _at=NcDYtzMoX4xyTiKUINWOsiCn19i7D3TGFOAYv4RFR/wRKaBaCw==; _ts=1788598422164; iszIdvaqC1gOP=0qP0T2yec.T.1LLF8id_F4myu7HEWQ4PfdHoKkHOa6zRjWLGBhYwqRFsjvNUkmZ5uPLipODPwZO2fZdf.oGoX6Q21jw6tSaVIm3KAmJU8fIddPbeVKuEms4mnjbBusMzT1ODf7KoBRnfcvZ6ySQfValZjpq9PRfEXClZtaykdQ7eJWTLoR.tnhQvV9aXQNOJhu0ex4hpjnLRn5DXQ8o6kXOT9O_4_G5YpaJp_5yGhTmtuhvhWA7Tzv7nfSUJnTeIR_MxvaXZaZIf_szL3t9q41aHD10Sxi4sWU_tONQ1IyY2qN04gGPLet.AjKO_TOLuARUHCyC0GqK6UBJG_BixkX0YvrOWgITACFppZlTI4gtYDumTlFJcSl_r4DMwcsDywtw4Ozdt5grUyg0f9eo3Y0YmDVLtMWWtk5sdDnO3aLeL"},
    {"name": "9982", "cookie": "cm=M801005N; _clientid=a648ee3851df9a0e4e83b1393dcf6347; _authtoken=cloud4c4aeb81e0ea4af3a3782e3f03f986a6; JSESSIONID=7AC1FC120EEA4D20F02336C54FEE9C5F; _at=9gFSO4HSnEMOCA77X4sBnzYcN+Q/H3O9vsY6R0C7BTbkxmXkww==; _ts=1788598799947; iszIdvaqC1gOO=60Nmm5KRFlc3omsbBv.Gmsc47GMfx7oChjFKDpNiKsuVTTHhAazrWC9UlIdWBVviTE5r.q_5iU6ahkDSaZk9hhGA; cm=M801005N; mg_uem_user_id_eb94d3ee70624bb5ac15ee1a9a594cb4=ea9dbfbd-9f9e-4674-894d-eb621e94c146; iszIdvaqC1gOP=0leQMwge6F_mmEGbn7JuKeqXu1BkLiRlMxyGkW5_mpR64jMe22PvqhqF_paBeqmVmxC7.hHDAB6qpLrvv04w_0eU15K8svQXzfcLZRlOBshmm.9FZkajPeLbcuT6tM58H82xPPTv3z4vTQz1NJez0s6f0MVt148VBiXDmVzyBAVyWs2F8eiAGrfHhIzxTMx1jbUJ0OxusdYL.hw1ZT6sAx56cYTHt3JJBj9KD0pg4YJa5KYbea.DohbFolOdnC.kaTy0zIhV7O8p401tuA2LxNarbrZPZieutmk3uNF9sM8oz7s8kyIM49Cb.0e19pk939lXo3RSEv05zyur65kIcsXuJ5AEZ8nTAte6e6MNXk9CAmL8jMRpWuRscUHb6ScM8vKCVKBG2FX0dA2Fo7KCUvs3bz693SsQEBSF7tRgzfvV"},
    {"name": "1812", "cookie": "mg_uem_user_id_eb94d3ee70624bb5ac15ee1a9a594cb4=9620ecd4-5cba-43af-bc65-de20069015b6; cm=M801005N; _clientid=7c14dadd7ca68002807a77abe08cd5c7; _authtoken=cloudf5b8bda3b0a94515819d094648dfa505; JSESSIONID=46B1E96C32B0D9232B1554DB9C4E8C7E; _ts=1788703051203; _at=fjwA3PPQzJpzqD1CjwXSLMLZJj4IruQgSGI1Gus79FymNwvObw==; iszIdvaqC1gOO=60QED.376uDm7J71HZr8qHsq7ZZceGJLRjve5AP4Cm1EqMBKYzTLnF5EtLdRuhf6HhEhi0T0.YHCKJXIImMSw0na; iszIdvaqC1gOP=0tkKzejwi4JjWoh3DQ8Pjz1hkbU7q.vOkUVCV4M23TzMLZktEescnXlvyJVcTkQcQjGArFzMdaTOw3nzmpUq4YddLrEWLNQ7A_BN4QCKR0J3nDwpum0fimAy3rIme6T08rfmXYCFD6yLv85SWFgb7wOs3kTsAyTFQA26M_Vwew.tdah2WJDBHDFv9ARSzLfNckg4vzREHaHMTkitKSTp1MOHqiRkEjAJodamGruEKdWC_lqLM1bp0SAXHeSMiFhrJ73M6jnOL9CcrMK9H5kBj.BW4nHENT4_dxf8nZnovm0DXL9mnoISZBfMkVfwrWT38Zb.uorScxFCdSkGa39G8l03w4KX_Ptd1axMWyZtZX_dUGaf8HB3WGeobrGCg8p9byoZRWar8.bHnS6LuYPlyUT8ujPLg6F9I8CBIPlRK_Z0"},
]

BASE_URL = "https://n.cmread.com"
QUERY_URL = f"{BASE_URL}/nap/p/nldh2026.jsp"
SIGNIN_URL = f"{BASE_URL}/nap/a/ms.sns.snsService/signinAction.json"
INTERVAL = 2

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


def parse_cookie(cookie_str):
    return dict(item.strip().split("=", 1) for item in cookie_str.split(";") if "=" in item)


def get_ai_dou_balance(session):
    """
    从查询接口提取 AI 豆余额。
    返回结构是插件字典，遍历找到 pluginCode=chip_number 的插件，
    其 data.myLeftChipsData.leftAmount 即为余额。
    """
    try:
        resp = session.get(QUERY_URL, headers=QUERY_HEADERS,
                           params={"dSDaipTi": GLOBAL_DS_TOKEN},
                           verify=False, timeout=15)
        if resp.status_code != 200:
            return None, f"HTTP {resp.status_code}"
        data = resp.json()
        for key, plugin in data.items():
            if isinstance(plugin, dict) and plugin.get("pluginCode") == "chip_number":
                chips = plugin.get("data", {}).get("myLeftChipsData", {})
                if chips:
                    return {
                        "balance": chips.get("leftAmount", 0),
                        "chipName": chips.get("chipName", ""),
                        "dayLeft": chips.get("dayLeftAmount", 0),
                        "monthLeft": chips.get("monthLeftAmount", 0),
                        "deadTime": chips.get("deadTime", ""),
                    }, None
        return None, "未找到 chip_number 插件"
    except Exception as e:
        return None, str(e)


def do_signin(session):
    """执行签到，返回 (status_code, message, prize_list)"""
    try:
        resp = session.get(SIGNIN_URL, headers=SIGN_HEADERS,
                           params={"dSDaipTi": GLOBAL_DS_TOKEN},
                           verify=False, timeout=15)
        if resp.status_code != 200:
            return None, f"HTTP {resp.status_code}", []
        result = resp.json()
        return result.get("status"), result.get("message", ""), result.get("signInPrizeList", [])
    except Exception as e:
        return None, str(e), []


def extract_prize_dou(prize_list):
    """从签到奖品列表中提取获得的豆子数"""
    total = 0
    names = []
    for prize in prize_list:
        if isinstance(prize, dict):
            # 尝试常见字段
            amount = prize.get("prizeNum") or prize.get("num") or prize.get("amount") or prize.get("count") or 0
            name = prize.get("prizeName") or prize.get("name") or ""
            try:
                total += int(amount)
            except (ValueError, TypeError):
                pass
            if name:
                names.append(f"{name}x{amount}")
    return total, ", ".join(names) if names else ""


def process_account(acc, index, total):
    name = acc["name"]
    session = requests.Session()
    session.cookies.update(parse_cookie(acc["cookie"]))

    print(f"\n{'='*60}")
    print(f"[{index+1}/{total}] 账号: {name}")
    print(f"{'='*60}")

    # 1. 签到前余额
    before, err = get_ai_dou_balance(session)
    if err:
        print(f"  [查询] 失败: {err}")
        before_balance = 0
    else:
        before_balance = before["balance"]
        print(f"  [签到前] {before['chipName']}: {before_balance}")

    # 2. 执行签到
    status, message, prizes = do_signin(session)
    prize_dou, prize_desc = extract_prize_dou(prizes)

    # 状态判定
    SIGN_SUCCESS = {"0", "200"}
    SIGN_ALREADY = {"5109"}
    if status in SIGN_SUCCESS:
        sign_status = "签到成功"
    elif status in SIGN_ALREADY:
        sign_status = "今日已签到"
    else:
        sign_status = f"签到失败(status={status})"

    if prize_desc:
        print(f"  [签到] {sign_status}  获得: {prize_desc}")
    else:
        print(f"  [签到] {sign_status}  消息: {message}")

    # 3. 签到后余额（稍等再查，确保服务端已更新）
    time.sleep(1)
    after, err2 = get_ai_dou_balance(session)
    if err2:
        after_balance = before_balance
        print(f"  [签到后] 查询失败: {err2}")
    else:
        after_balance = after["balance"]
        gained = after_balance - before_balance
        if gained > 0:
            print(f"  [签到后] {after['chipName']}: {after_balance}  (本次 +{gained})")
        elif status in SIGN_ALREADY:
            print(f"  [签到后] {after['chipName']}: {after_balance}  (已签到，无新增)")
        else:
            print(f"  [签到后] {after['chipName']}: {after_balance}")

    # 4. 汇总
    print(f"\n  >>> {name} | 签到前 {before_balance} -> 签到后 {after_balance} "
          f"| 本次 +{after_balance - before_balance if status in SIGN_SUCCESS else 0}豆 "
          f"| {sign_status}")

    return {
        "name": name,
        "before": before_balance,
        "after": after_balance,
        "gained": after_balance - before_balance if status in SIGN_SUCCESS else 0,
        "status": sign_status,
        "raw_status": status,
    }


def main():
    total = len(ACCOUNTS)
    print(f"咪咕阅读 nldh2026 签到  共 {total} 个账号  间隔 {INTERVAL}秒")
    print(f"开始时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    results = []
    for i, acc in enumerate(ACCOUNTS):
        r = process_account(acc, i, total)
        results.append(r)
        if i < total - 1:
            time.sleep(INTERVAL)

    # 汇总表
    print(f"\n{'='*60}")
    print(f"全部完成  结束时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    print(f"{'账号':<8}{'签到前':<10}{'签到后':<10}{'本次获得':<10}{'状态'}")
    print(f"{'-'*60}")
    total_before = total_after = total_gained = 0
    success_count = 0
    for r in results:
        total_before += r["before"]
        total_after += r["after"]
        total_gained += r["gained"]
        if r["raw_status"] in ("0", "200", "5109"):
            success_count += 1
        print(f"{r['name']:<8}{r['before']:<10}{r['after']:<10}"
              f"+{r['gained']:<9}{r['status']}")
    print(f"{'-'*60}")
    print(f"{'合计':<8}{total_before:<10}{total_after:<10}+{total_gained:<9}"
          f"成功/已签到 {success_count}/{total}")


if __name__ == "__main__":
    main()
