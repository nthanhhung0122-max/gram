"""
=============================================================================
 TOOL AUTO GRAMSTONE (@gramstone_bot) - TỰ ĐỘNG KHAI THÁC, NÂNG CẤP & GAMES 24/7
 - Dành riêng cho tài khoản: hungzai22
 - Tự động lặp lại liên tục: CANH VÀ THU HOẠCH (CLAIM) MỎ ĐÀO MỖI 1 GIỜ (3600s)
 - Tự động lấy x-telegram-init-data tươi mới qua Telethon ở mỗi chu kỳ
 - Tự động Điểm danh hàng ngày Streak (/api/streak/claim -> Nhận +10 -> +100 GH/s)
 - Tự động Thu hoạch mỏ đào Vault khi đầy 100% (Hoàn toàn miễn phí 0 cần xem QC)
 - Tự động Nâng cấp 6 Dụng cụ đào mỏ qua quảng cáo (/api/equipment/upgrade)
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
STRING_SESSION = os.getenv("TELEGRAM_STRING_SESSION_ACC1") or "1BVtsOHIBuxmpWiBJ9hvwV9pSrzWw5U2I5Fe20Ww8l1LCk9rnsG6T6lLZEJXZE1JJC_qUH_yyWHnRoedRNI5lJYnfjRN4gyGeDrCxquDU12ZflrpCz0VLhMZx2C0LlyUCy2eHRSRE1wUCpEYZaymL0P7Z9eAHwMy4Oogewh5TqyO4x4MF6j0yTq8Zvfpv43O4aQDzErNv3GRqpx8DXBcOJIMP9yVhq-Mby5VH5J9cF-h-bJ5ws3xKjA4GY7YKjHxDt9OI-Zr7mr-V3qZy99UxJooThJj51f2RqOKhODdLh9XZQ0ygSoAd3iFAZDOPMEo8Ch5TrrzLXi2Q3N0HorIL1JfV0xoFQlY="

API_BASE = "https://gramstone.46-101-143-24.sslip.io"

EQUIP_NAMES = {
    1: "Titanyum Kazma (Cuốc đá titan)",
    2: "Satchel (Túi quặng)",
    3: "Goggles (Kính bảo hộ)",
    4: "Gauntlets (Găng tay đào)",
    5: "Furnace (Lò luyện)",
    6: "Chest (Rương kho báu)"
}

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

def check_and_upgrade_equipment(headers, tg_id, equip_list):
    """
    Tự động nâng cấp 6 loại dụng cụ đào bằng cách xem quảng cáo.
    """
    if not equip_list:
        return

    for eq in equip_list:
        slot = eq.get("slot")
        name = EQUIP_NAMES.get(slot, f"Dụng cụ #{slot}")
        lvl = eq.get("level", 0)
        is_maxed = eq.get("isMaxed", False)
        ads_prog = eq.get("adsProgress", 0)
        req_ads = eq.get("reqAds", 1)

        if is_maxed:
            continue

        if ads_prog < req_ads:
            try:
                # 1. Báo bắt đầu xem quảng cáo
                requests.post(f"{API_BASE}/api/ads/start", headers=headers, json={"telegram_id": tg_id}, verify=False, timeout=8)
                time.sleep(7) # Yêu cầu tối thiểu 6s theo luật server

                # 2. Gửi request nâng cấp
                payload = {
                    "telegram_id": tg_id,
                    "slot": slot,
                    "mode": "ad",
                    "ad_network": "richads"
                }
                r_up = requests.post(f"{API_BASE}/api/equipment/upgrade", headers=headers, json=payload, verify=False, timeout=10).json()
                if r_up.get("ok"):
                    log("EQUIP_UP", f"Nâng cấp thành công {name}! {Fore.GREEN}{r_up.get('message', 'Thành công')}{Style.RESET_ALL}", Fore.GREEN)
                else:
                    err = r_up.get("error", "")
                    if "richads_cap" in str(r_up.get("code", "")) or "Bugünkü yedek reklam" in err:
                        log("EQUIP_INFO", f"Slot {slot} [{name}]: Đạt quota QC dự phòng ({ads_prog}/{req_ads}). Cần xem Adsgram trên app hoặc chờ ngày mới.", Fore.LIGHTBLACK_EX)
                        break
                    elif "Adsgram" in err:
                        log("EQUIP_INFO", f"Slot {slot} [{name}]: Cần xác thực Adsgram từ ứng dụng Telegram ({ads_prog}/{req_ads} QC).", Fore.LIGHTBLACK_EX)
                    else:
                        log("EQUIP_WARN", f"Slot {slot} [{name}]: {err}", Fore.LIGHTBLACK_EX)
            except Exception as e:
                log("EQUIP_ERR", f"Lỗi nâng cấp slot {slot}: {e}", Fore.LIGHTBLACK_EX)
            time.sleep(1)

def run_gramstone():
    print(f"""
{Fore.CYAN}======================================================================
     TOOL AUTO GRAMSTONE MINING 24/7 (@gramstone_bot)
     - Canh và tự động Thu hoạch (Claim) mỏ đào MỖI 1 GIỜ (3600s)
     - Tự động lấy x-telegram-init-data tươi mới mỗi chu kỳ
     - Tự động Đăng nhập & Báo danh Streak nhận GH/s
     - Tự động Tap đào đá liên tục cho tới khi đủ 240/240
     - Tự động Nâng cấp Dụng cụ đào mỏ qua QC (Equipment Upgrade)
     - Tự động Chơi Mini Games buff tốc độ đào GH/s
======================================================================{Style.RESET_ALL}
    """)

    cycle = 1
    start_time = time.time()
    # Nếu chạy trên GitHub Actions thì giới hạn 5.4 tiếng (~19500s) để ca sau vào thay thế mượt mà
    # Nếu chạy trên máy tính thì chạy vô hạn (0)
    MAX_RUNTIME = 19500 if os.getenv("GITHUB_ACTIONS") else 0

    while True:
        try:
            if MAX_RUNTIME > 0 and (time.time() - start_time) >= MAX_RUNTIME:
                log("DONE", f"Hoàn thành ca làm việc {MAX_RUNTIME//3600} tiếng trên GitHub Actions. Nghỉ ngơi chuyển giao ca trực!", Fore.GREEN)
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
                equip_list = data.get("equipment", [])
                log("PROFILE", f"Đăng nhập: {Fore.YELLOW}{u.get('username') or tg_id}{Style.RESET_ALL} | Số dư: {Fore.GREEN}{u.get('balance', 0):.8f} TON/GRAM{Style.RESET_ALL} | Tốc độ: {Fore.CYAN}{m.get('totalGhs', 0)} GH/s{Style.RESET_ALL}", Fore.GREEN)
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

            # 3. Nâng cấp dụng cụ đào mỏ qua quảng cáo
            check_and_upgrade_equipment(headers, tg_id, equip_list)

            # 4. Tap đào đá liên tục cho đến khi đủ lượt ngày (240/240)
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

            # 5. Chơi Mini Games để tăng tốc độ đào GH/s
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

            # 6. Canh thời gian nghỉ cho tới lần CLAIM mỏ tiếp theo (Đúng 1h = 3600s)
            cycle += 1
            wait_time = int(rem_sec) if rem_sec and rem_sec > 30 else 3600
            wait_time += 15  # Thêm 15 giây dự phòng để chắc chắn hầm mỏ đạt 100% đầy

            log("SLEEP", f"Hoàn tất việc chu kỳ. Đang canh mỏ đào... Sẽ tự động THU HOẠCH (CLAIM) sau {Fore.CYAN}{wait_time // 60} phút ({wait_time}s){Style.RESET_ALL} nữa!", Fore.GREEN)

            while wait_time > 0:
                step_sleep = min(wait_time, 300) # Cứ mỗi 5 phút in cập nhật tiến độ 1 lần
                time.sleep(step_sleep)
                wait_time -= step_sleep
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
