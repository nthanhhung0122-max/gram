"""
=============================================================================
 TOOL AUTO GRAMSTONE (@gramstone_bot) - TỰ ĐỘNG KHAI THÁC, NÂNG CẤP & QC 24/7
 - Dành riêng cho tài khoản: hungzai22
 - Canh và tự động THU HOẠCH (CLAIM) mỏ đào MỖI 1 GIỜ (3600s)
 - Tự động Điểm danh hàng ngày Streak (/api/streak/claim -> Nhận +10 -> +100 GH/s)
 - Tự động Thu hoạch mỏ đào Vault khi đầy 100% (0 cần xem QC)
 - Tự động NÂNG CẤP DUY NHẤT XE MỎ (Slot 6: Armored Bullion Minecart / Zırhlı Maden Vagonu)
 - Tự động XEM QUẢNG CÁO 45 LƯỢT/NGÀY (/api/ads/reward: +0.5 GH/s mỗi 5 phút + bậc thang Ad Ladder)
 - Tự động ĐỒNG BỘ SURVEYS & TIMEWALL (/api/timewall/surveys) & HOÀN THÀNH NHIỆM VỤ (/api/tasks/complete)
 - Tự động Tap đào đá liên tục cho tới khi đủ 240/240 lượt trong ngày
 - Tự động thắng 5 Mini Games (/api/game/start & /api/game/finish) để buff GH/s
 - Hỗ trợ chạy liên tục 24/7 trên GitHub Actions hoặc máy tính cá nhân
=============================================================================
"""

import os
import sys
import time
import json
import random
import hashlib
import asyncio
import urllib.parse
import urllib3
import requests
from colorama import Fore, Style, init

from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.messages import RequestAppWebViewRequest
from telethon.tl.types import InputBotAppShortName

urllib3.disable_warnings()
init(autoreset=True)

# THÔNG TIN TELEGRAM API
API_ID = 39182276
API_HASH = "f02b155d895a3a3fbf8a1cbe810b5338"
STRING_SESSION = (
    os.getenv("TELEGRAM_STRING_SESSION_ACC1")
    or os.getenv("TELEGRAM_STRING_SESSION")
    or os.getenv("TELEGRAM_SESSION_B64_ACC1")
    or os.getenv("STRING_SESSION")
    or "1BVtsOHIBuxmpWiBJ9hvwV9pSrzWw5U2I5Fe20Ww8l1LCk9rnsG6T6lLZEJXZE1JJC_qUH_yyWHnRoedRNI5lJYnfjRN4gyGeDrCxquDU12ZflrpCz0VLhMZx2C0LlyUCy2eHRSRE1wUCpEYZaymL0P7Z9eAHwMy4Oogewh5TqyO4x4MF6j0yTq8Zvfpv43O4aQDzErNv3GRqpx8DXBcOJIMP9yVhq-Mby5VH5J9cF-h-bJ5ws3xKjA4GY7YKjHxDt9OI-Zr7mr-V3qZy99UxJooThJj51f2RqOKhODdLh9XZQ0ygSoAd3iFAZDOPMEo8Ch5TrrzLXi2Q3N0HorIL1JfV0xoFQlY="
)

API_BASE = "https://gramstone.46-101-143-24.sslip.io"

def log(tag, msg, color=Fore.WHITE):
    t_str = time.strftime('%H:%M:%S')
    print(f"{Fore.LIGHTBLACK_EX}[{t_str}]{Style.RESET_ALL} {color}[{tag}]{Style.RESET_ALL} {msg}")

async def fetch_gramstone_init():
    try:
        client = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)
        await client.connect()
        if not await client.is_user_authorized():
            await client.disconnect()
            return None

        bot = await client.get_input_entity("gramstone_bot")
        bot_app = InputBotAppShortName(bot_id=bot, short_name="mine")
        res = await client(RequestAppWebViewRequest(peer=bot, app=bot_app, platform="android"))
        await client.disconnect()

        frag = urllib.parse.urlparse(res.url).fragment
        init_data = urllib.parse.parse_qs(frag).get("tgWebAppData", [None])[0]
        return init_data
    except Exception as e:
        log("ERR", f"Lỗi Telethon lấy init-data: {e}", Fore.RED)
        return None

def build_headers_and_body(init_data):
    sub_parsed = urllib.parse.parse_qs(init_data)
    user_obj = json.loads(sub_parsed.get("user", ["{}"])[0])
    
    ua = "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
    raw_fp = f"{ua}||Linux armv8l||vi-VN,vi||Asia/Saigon||393x873x24||2.75||8||8||5||Mali-G76 MC4||sig"
    fp_hash = hashlib.sha256(raw_fp.encode('utf-8')).hexdigest()

    headers = {
        "Content-Type": "application/json",
        "x-telegram-init-data": init_data,
        "x-gs-fp": fp_hash,
        "user-agent": ua,
        "origin": API_BASE,
        "referer": f"{API_BASE}/"
    }

    body = {
        "telegram_id": str(user_obj.get("id")),
        "username": user_obj.get("username", ""),
        "first_name": user_obj.get("first_name", ""),
        "start_param": "",
        "device": {
            "ua": ua,
            "platform": "Linux armv8l",
            "tgPlatform": "android",
            "tgVersion": "9.6",
            "lang": "vi-VN,vi",
            "tz": "Asia/Saigon",
            "screen": "393x873x24",
            "dpr": 2.75,
            "cores": 8,
            "mem": 8,
            "touch": 5,
            "gpu": "ARM / Mali-G76 MC4"
        }
    }
    return headers, body, user_obj

# =============================================================================
# 1. NÂNG CẤP DUY NHẤT XE MỎ (SLOT 6: Zırhlı Maden Vagonu / Armored Minecart)
# =============================================================================
def check_and_upgrade_minecart(headers, tg_id, equip_list):
    """
    Theo yêu cầu người dùng: CHỈ XEM VIDEO ĐỂ NÂNG CẤP XE MỎ (Slot 6: Armored Minecart).
    Bỏ qua toàn bộ các slot 1, 2, 3, 4, 5.
    """
    if not equip_list:
        return

    # Tìm đúng Slot 6 (Xe mỏ)
    slot6 = next((eq for eq in equip_list if eq.get("slot") == 6), None)
    if not slot6:
        log("EQUIP", "Không tìm thấy thông tin Xe mỏ (Slot 6).", Fore.YELLOW)
        return

    lvl = slot6.get("level", 0)
    max_lvl = slot6.get("maxLevel", 5)
    is_maxed = slot6.get("isMaxed", False)
    ads_prog = slot6.get("adsProgress", 0)
    req_ads = slot6.get("reqAds", 6)
    is_unlocked = slot6.get("isUnlocked", False)

    log("MINE_CART", f"Xe mỏ (Slot 6): Level {lvl}/{max_lvl} | Đã xem QC: {ads_prog}/{req_ads} | Mở khóa: {is_unlocked}", Fore.CYAN)

    if is_maxed or lvl >= max_lvl:
        log("MINE_CART", f"Xe mỏ đã đạt cấp tối đa (Level {lvl}/{max_lvl})!", Fore.GREEN)
        return

    if ads_prog < req_ads:
        try:
            log("MINE_CART", f"Bắt đầu xem quảng cáo nâng cấp Xe mỏ ({ads_prog + 1}/{req_ads})...", Fore.YELLOW)
            requests.post(f"{API_BASE}/api/ads/start", headers=headers, json={"telegram_id": tg_id}, verify=False, timeout=8)
            time.sleep(7)  # Yêu cầu tối thiểu 6s theo luật máy chủ

            payload = {
                "telegram_id": tg_id,
                "slot": 6,
                "mode": "ad",
                "ad_network": "richads"
            }
            r_up = requests.post(f"{API_BASE}/api/equipment/upgrade", headers=headers, json=payload, verify=False, timeout=10).json()
            if r_up.get("ok"):
                new_msg = r_up.get("message", "Thành công")
                log("MINE_CART", f"Nâng cấp Xe mỏ thành công! {Fore.GREEN}{new_msg}{Style.RESET_ALL}", Fore.GREEN)
            else:
                err = r_up.get("error", "")
                code = r_up.get("code", "")
                if "richads_cap" in code or "Bugünkü yedek reklam" in err:
                    log("MINE_CART", f"Quota QC dự phòng cho Xe mỏ hôm nay đã hết ({ads_prog}/{req_ads}). Sẽ tự động nâng tiếp vào ngày mai!", Fore.LIGHTBLACK_EX)
                elif "ad_unverified" in code or "Adsgram" in err:
                    log("MINE_CART", f"Cần xác thực Adsgram trong Mini App Telegram ({ads_prog}/{req_ads} QC).", Fore.LIGHTBLACK_EX)
                else:
                    log("MINE_CART", f"Trạng thái nâng cấp Xe mỏ: {err}", Fore.LIGHTBLACK_EX)
        except Exception as e:
            log("MINE_CART", f"Lỗi xem QC Xe mỏ: {e}", Fore.LIGHTBLACK_EX)

# =============================================================================
# 2. XEM QUẢNG CÁO HÀNG NGÀY (45 QC / NGÀY - TĂNG +0.5 GH/s + AD LADDER)
# =============================================================================
def check_and_watch_ad_45(headers, tg_id, user_data, config):
    """
    Tự động xem quảng cáo nhận +0.5 GH/s (Giới hạn tối đa 45 cái/ngày, cooldown 300s = 5 phút).
    Đồng thời nhận thưởng Ad Ladder ở các mốc 5, 10, 20, 30, 45 QC.
    """
    watched_today = user_data.get("ads_watched_today", 0)
    daily_limit = config.get("watch_ad_daily_limit", 45)
    last_ad_at = user_data.get("last_ad_at", 0)
    cooldown_sec = config.get("watch_ad_cooldown_sec", 300)
    reward_ghs = config.get("watch_ad_reward_ghs", 0.5)

    if watched_today >= daily_limit:
        log("WATCH_AD", f"Đã hoàn thành toàn bộ chỉ tiêu {watched_today}/{daily_limit} quảng cáo hôm nay!", Fore.GREEN)
        return False

    elapsed = (time.time() * 1000 - last_ad_at) / 1000
    if elapsed < cooldown_sec:
        remain_wait = int(cooldown_sec - elapsed)
        log("WATCH_AD", f"Tiến độ QC hôm nay: {Fore.YELLOW}{watched_today}/{daily_limit}{Style.RESET_ALL} (Còn cooldown {Fore.CYAN}{remain_wait}s{Style.RESET_ALL} nữa mới được xem tiếp).", Fore.LIGHTBLACK_EX)
        return False

    try:
        log("WATCH_AD", f"Bắt đầu xem quảng cáo #{watched_today + 1}/{daily_limit} để nhận +{reward_ghs} GH/s...", Fore.YELLOW)
        requests.post(f"{API_BASE}/api/ads/start", headers=headers, json={"telegram_id": tg_id}, verify=False, timeout=8)
        time.sleep(7)

        payload = {
            "telegram_id": tg_id,
            "ad_network": "richads"
        }
        r_ad = requests.post(f"{API_BASE}/api/ads/reward", headers=headers, json=payload, verify=False, timeout=10).json()
        if r_ad.get("ok"):
            new_ghs = r_ad.get("rewardGhs", reward_ghs)
            user_data["ads_watched_today"] = watched_today + 1
            user_data["last_ad_at"] = time.time() * 1000
            log("WATCH_AD", f"Xem QC #{watched_today + 1}/{daily_limit} thành công! {Fore.GREEN}+{new_ghs} GH/s{Style.RESET_ALL}", Fore.GREEN)
            return True
        else:
            err = r_ad.get("error", "")
            code = r_ad.get("code", "")
            if "richads_cap" in code or "Bugünkü yedek reklam" in err:
                log("WATCH_AD", f"Hạn mức QC dự phòng hôm nay đã hết ({watched_today}/{daily_limit}). Sẽ tiếp tục vào ngày mai!", Fore.LIGHTBLACK_EX)
            else:
                log("WATCH_AD", f"Trạng thái xem QC: {err}", Fore.LIGHTBLACK_EX)
            return False
    except Exception as e:
        log("WATCH_AD", f"Lỗi xem quảng cáo: {e}", Fore.LIGHTBLACK_EX)
        return False

# =============================================================================
# 3. ĐỒNG BỘ SURVEYS & TIMEWALL & HOÀN THÀNH NHIỆM VỤ
# =============================================================================
def process_surveys_and_tasks(headers, tg_id, user_obj, tasks_list):
    """
    Tự động đồng bộ các khảo sát Timewall Surveys và hoàn thành các nhiệm vụ Tasks.
    """
    # 1. Đồng bộ Timewall Surveys
    try:
        tw_payload = {
            "telegram_id": tg_id,
            "username": user_obj.get("username", ""),
            "first_name": user_obj.get("first_name", ""),
            "sw": 393,
            "sh": 873,
            "force": True
        }
        r_tw = requests.post(f"{API_BASE}/api/timewall/surveys", headers=headers, json=tw_payload, verify=False, timeout=10).json()
        if r_tw.get("ok"):
            s_count = len(r_tw.get("surveys", []))
            has_pre = r_tw.get("prescreener", False)
            log("SURVEY", f"Đồng bộ Timewall Surveys thành công: {s_count} khảo sát sẵn sàng (Prescreener: {has_pre})", Fore.GREEN)
        else:
            log("SURVEY", f"Khảo sát Timewall: {r_tw.get('error', 'Chưa có khảo sát mới')}", Fore.LIGHTBLACK_EX)
    except Exception as e:
        log("SURVEY", f"Lỗi đồng bộ khảo sát: {e}", Fore.LIGHTBLACK_EX)

    # 2. Hoàn thành các nhiệm vụ Tasks khả dụng
    if not tasks_list:
        return

    for t in tasks_list:
        t_id = t.get("id")
        t_title = t.get("title", f"Task #{t_id}")
        is_done = t.get("isCompleted", False)
        is_active = t.get("is_active", 0)

        if not is_done and is_active:
            try:
                payload = {
                    "telegram_id": tg_id,
                    "task_id": t_id,
                    "ad_network": "richads"
                }
                r_task = requests.post(f"{API_BASE}/api/tasks/complete", headers=headers, json=payload, verify=False, timeout=10).json()
                if r_task.get("ok"):
                    log("TASK", f"Hoàn thành nhiệm vụ [{t_title}]! {Fore.GREEN}+{r_task.get('rewardGhs', 0)} GH/s{Style.RESET_ALL}", Fore.GREEN)
                else:
                    err = r_task.get("error", "Chưa hoàn tất")
                    log("TASK", f"Nhiệm vụ [{t_title}]: {err}", Fore.LIGHTBLACK_EX)
                time.sleep(1.5)
            except Exception as e:
                log("TASK", f"Lỗi làm nhiệm vụ [{t_title}]: {e}", Fore.LIGHTBLACK_EX)

# =============================================================================
# CHƯƠNG TRÌNH CHÍNH (VÒNG LẶP KHAI THÁC 24/7)
# =============================================================================
def run_gramstone():
    print(f"""
{Fore.CYAN}======================================================================
     TOOL AUTO GRAMSTONE MINING 24/7 (@gramstone_bot)
     - Tự động Thu hoạch (Claim) mỏ đào MỖI 1 GIỜ (3600s)
     - Tự động Đăng nhập & Báo danh Streak nhận GH/s
     - Tự động NÂNG CẤP DUY NHẤT XE MỎ (Slot 6) qua QC
     - Tự động XEM QUẢNG CÁO 45 LƯỢT/NGÀY (+0.5 GH/s + Ad Ladder)
     - Tự động ĐỒNG BỘ SURVEYS & TIMEWALL & TASKS
     - Tự động Tap đào đá liên tục cho tới khi đủ 240/240
     - Tự động Chơi Mini Games buff tốc độ đào GH/s
======================================================================{Style.RESET_ALL}
    """)

    cycle = 1
    start_time = time.time()
    # Chạy ca trực trên GitHub Actions tối đa 5.4 tiếng (~19500s)
    MAX_RUNTIME = 19500 if os.getenv("GITHUB_ACTIONS") else 0

    while True:
        try:
            if MAX_RUNTIME > 0 and (time.time() - start_time) >= MAX_RUNTIME:
                log("DONE", f"Hoàn thành ca làm việc {MAX_RUNTIME//3600} tiếng trên GitHub Actions. Chuyển ca trực tiếp theo!", Fore.GREEN)
                break

            print("\n" + "=" * 60)
            log("CYCLE", f"=== BẮT ĐẦU CHU KỲ #{cycle} ===", Fore.CYAN)
            print("=" * 60)

            # Lấy init-data mới nhất cho chu kỳ này
            log("AUTH", "Đang kết nối Telegram lấy x-telegram-init-data tươi mới...", Fore.CYAN)
            init_data = asyncio.run(fetch_gramstone_init())
            if not init_data:
                log("ERR", "Không thể lấy init-data. Chờ 60s thử lại...", Fore.RED)
                time.sleep(60)
                continue

            headers, body, user_obj = build_headers_and_body(init_data)
            tg_id = str(user_obj.get("id"))

            # Đăng nhập lấy dữ liệu người chơi
            try:
                r_auth = requests.post(f"{API_BASE}/api/auth", headers=headers, json=body, verify=False, timeout=12)
                if r_auth.status_code != 200 or not r_auth.json().get("ok"):
                    log("ERR", f"Đăng nhập thất bại: {r_auth.text}. Chờ 60s...", Fore.RED)
                    time.sleep(60)
                    continue
                data = r_auth.json()
                u = data.get("user", {})
                m = data.get("mining", {})
                cfg = data.get("config", {})
                tasks_list = data.get("tasks", [])
                equip_list = data.get("equipment", [])
                log("PROFILE", f"Đăng nhập: {Fore.YELLOW}{u.get('username') or tg_id}{Style.RESET_ALL} | Số dư: {Fore.GREEN}{u.get('balance', 0):.8f} TON/GRAM{Style.RESET_ALL} | Tốc độ: {Fore.CYAN}{m.get('totalGhs', 0)} GH/s{Style.RESET_ALL} | QC hôm nay: {u.get('ads_watched_today', 0)}/45", Fore.GREEN)
            except Exception as e:
                log("ERR", f"Lỗi kết nối /api/auth: {e}. Chờ 60s...", Fore.RED)
                time.sleep(60)
                continue

            # 1. Điểm danh Streak hàng ngày
            try:
                r_streak = requests.post(f"{API_BASE}/api/streak/claim", headers=headers, json={}, verify=False, timeout=10).json()
                if r_streak.get("ok"):
                    log("STREAK", f"Điểm danh Streak thành công! {Fore.GREEN}+{r_streak.get('rewardGhs')} GH/s{Style.RESET_ALL} (Ngày {r_streak.get('streakDay')})", Fore.GREEN)
                else:
                    log("STREAK", f"Trạng thái điểm danh: {r_streak.get('error', 'Đã điểm danh hôm nay')}", Fore.LIGHTBLACK_EX)
            except Exception:
                pass

            # 2. Thu hoạch hầm chứa (Vault Claim) mỗi khi hầm đầy 100% (chu kỳ 3600s = 1 giờ)
            is_full = m.get("isFull", False)
            rem_sec = m.get("remainingSec", 0)

            if is_full or rem_sec <= 5:
                try:
                    r_claim = requests.post(f"{API_BASE}/api/claim", headers=headers, json={"telegram_id": tg_id, "watched_ad": False}, verify=False, timeout=10).json()
                    if r_claim.get("ok"):
                        log("CLAIM", f"Thu hoạch Vault thành công! {Fore.GREEN}+{r_claim.get('claimedAmount', 0):.8f} TON/GRAM{Style.RESET_ALL} (Kho đầy 100% sau 1 giờ)", Fore.GREEN)
                        rem_sec = 3600  # Vừa claim xong, kho bắt đầu chu kỳ 1 giờ mới
                    else:
                        log("CLAIM", f"Trạng thái hầm đào: {r_claim.get('error')}", Fore.YELLOW)
                except Exception as e:
                    log("WARN", f"Lỗi gửi yêu cầu thu hoạch: {e}", Fore.YELLOW)
            else:
                pct = m.get("progressPercent", 0)
                mined = m.get("pendingMinedTon", 0)
                log("CLAIM", f"Hầm mỏ đang tích lũy: {Fore.YELLOW}{pct:.1f}%{Style.RESET_ALL} (+{mined:.8f} GRAM) - Còn {Fore.CYAN}{rem_sec // 60} phút ({rem_sec}s){Style.RESET_ALL} nữa sẽ đầy.", Fore.LIGHTBLACK_EX)

            # 3. Nâng cấp DUY NHẤT Xe mỏ (Slot 6) qua quảng cáo
            check_and_upgrade_minecart(headers, tg_id, equip_list)

            # 4. Xem quảng cáo nhận GH/s (45 QC / ngày)
            check_and_watch_ad_45(headers, tg_id, u, cfg)

            # 5. Đồng bộ Surveys & Timewall & Làm tasks
            process_surveys_and_tasks(headers, tg_id, user_obj, tasks_list)

            # 6. Tap đào đá liên tục cho đến khi đủ lượt ngày (240/240)
            log("TAP", "Kiểm tra và tap đào đá...", Fore.CYAN)
            err_count = 0
            while True:
                try:
                    r_tap = requests.post(f"{API_BASE}/api/tap", headers=headers, json={}, verify=False, timeout=10).json()
                    if r_tap.get("ok"):
                        err_count = 0
                        msg = r_tap.get("message", "")
                        t_today = r_tap.get("tapsToday", 0)
                        d_limit = r_tap.get("dailyLimit", 240)
                        log("TAP", f"Tap thành công: {Fore.GREEN}{msg}{Style.RESET_ALL} ({t_today}/{d_limit})")
                        if t_today >= d_limit:
                            log("TAP", f"Đã hoàn thành toàn bộ lượt tap hôm nay ({t_today}/{d_limit})!", Fore.GREEN)
                            break
                        time.sleep(random.uniform(2.1, 2.3))
                    else:
                        err = r_tap.get("error", "Đã hết lượt tap hôm nay")
                        log("TAP", f"Trạng thái tap: {err}", Fore.LIGHTBLACK_EX)
                        break
                except Exception as e:
                    err_count += 1
                    log("WARN", f"Mạng chập chờn khi tap ({err_count}/3): {e}", Fore.YELLOW)
                    if err_count >= 3:
                        break
                    time.sleep(2.5)

            # 7. Chơi Mini Games để tăng tốc độ đào GH/s
            log("GAMES", "Kiểm tra và chơi Mini Games để buff tốc độ đào...", Fore.CYAN)
            game_list = ["jetpack", "breaker", "catcher", "memory", "match3"]
            for g_name in game_list:
                try:
                    r_start = requests.post(f"{API_BASE}/api/game/start", headers=headers, json={"telegram_id": tg_id, "game": g_name}, verify=False, timeout=10).json()
                    if r_start.get("ok"):
                        p_id = r_start.get("playId")
                        target = r_start.get("target", 30)
                        log("GAME_START", f"Bắt đầu game {g_name} (Mục tiêu: {target})...", Fore.YELLOW)
                        time.sleep(15)  # Chờ 15s để giả lập người chơi thực tế
                        r_finish = requests.post(f"{API_BASE}/api/game/finish", headers=headers, json={"telegram_id": tg_id, "play_id": p_id, "score": target + 3}, verify=False, timeout=10).json()
                        if r_finish.get("ok"):
                            log("GAME_WIN", f"Thắng game {g_name}! {Fore.GREEN}+{r_finish.get('rewardGhs', 2)} GH/s{Style.RESET_ALL}", Fore.GREEN)
                        else:
                            log("GAME_ERR", f"Lỗi hoàn thành game: {r_finish.get('error')}", Fore.YELLOW)
                    else:
                        log("GAME_SKIP", f"Game {g_name}: {r_start.get('error', 'Chưa sẵn sàng')}", Fore.LIGHTBLACK_EX)
                    time.sleep(2)
                except Exception as e:
                    log("WARN", f"Lỗi chơi game {g_name}: {e}", Fore.YELLOW)

            # 8. Canh thời gian nghỉ cho tới lần CLAIM mỏ tiếp theo (Đúng 1h = 3600s)
            cycle += 1
            wait_time = int(rem_sec) if rem_sec and rem_sec > 30 else 3600
            wait_time += 15  # Thêm 15 giây dự phòng

            log("SLEEP", f"Hoàn tất việc chu kỳ. Đang canh mỏ đào... Sẽ tự động THU HOẠCH (CLAIM) sau {Fore.CYAN}{wait_time // 60} phút ({wait_time}s){Style.RESET_ALL} nữa!", Fore.GREEN)

            # Trong lúc chờ 1 tiếng, cứ mỗi 5 phút (300s) kiểm tra xem có thể xem 1 QC nhận GH/s hoặc nâng Xe mỏ hay không!
            while wait_time > 0:
                step_sleep = min(wait_time, 300)
                time.sleep(step_sleep)
                wait_time -= step_sleep

                # Kiểm tra xen kẽ xem QC 45 lần và nâng Xe mỏ trong lúc chờ
                if wait_time > 30:
                    check_and_watch_ad_45(headers, tg_id, u, cfg)
                    check_and_upgrade_minecart(headers, tg_id, equip_list)

                if wait_time > 0:
                    log("TIMER", f"Đang chờ kho đầy... Còn {Fore.CYAN}{wait_time // 60} phút ({wait_time}s){Style.RESET_ALL} nữa tới giờ thu hoạch!", Fore.LIGHTBLACK_EX)

        except KeyboardInterrupt:
            log("STOP", "Đã dừng tool theo yêu cầu người dùng.", Fore.YELLOW)
            break
        except Exception as e:
            log("CRASH", f"Lỗi chu kỳ: {e}. Sẽ thử lại sau 60 giây...", Fore.RED)
            time.sleep(60)

if __name__ == "__main__":
    run_gramstone()
