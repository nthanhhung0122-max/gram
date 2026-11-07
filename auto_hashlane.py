#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
  BOT AUTO HASHLANE ($TON) 24/7 - KHAI THÁC & THU HOẠCH ĐIỂM TỰ ĐỘNG
  Platform: HashLane Mini App (https://46-101-192-249.sslip.io/app/)
  Telegram Bot: @hashlane_bot
  
  TÍNH NĂNG TỰ ĐỘNG HÓA 100%:
    1. Chuẩn hóa mã băm thiết bị X-Device SHA-256 + X-Tz-Offset.
    2. Tự động điểm danh nhận điểm & Gems hàng ngày (/api/checkin).
    3. Tự động kiểm tra trạng thái mỏ đào (/api/me).
    4. Tự động THU HOẠCH ĐIỂM (/api/mining/collect) khi mỏ đạt 100 điểm (Full).
    5. Tự động KÍCH HOẠT VÒNG ĐÀO MỚI (/api/mining/start) ngay sau khi thu hoạch.
    6. Tự động kiểm tra & nhận nhiệm vụ kiếm thêm điểm (/api/tasks/start & check).
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
import requests
from colorama import init, Fore, Style

from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.messages import RequestWebViewRequest

init(autoreset=True)

_raw_id = os.getenv("TELEGRAM_API_ID", "").strip()
API_ID = int(_raw_id) if _raw_id.isdigit() else 34333329
API_HASH = os.getenv("TELEGRAM_API_HASH", "").strip() or "4f9371f95000578c84dbc670aaf1f819"

DEFAULT_SESSION_ACC1 = (
    "1BVtsOHIBuxmpWiBJ9hvwV9pSrzWw5U2I5Fe20Ww8l1LCk9rnsG6T6lLZEJXZE1JJC_qUH_yyWHnRoedRNI5lJYnfjRN4gyGeDrCxquDU12ZflrpCz0VLhMZx2C0LlyUCy2eHRSRE1wUCpEYZaymL0P7Z9eAHwMy4Oogewh5TqyO4x4MF6j0yTq8Zvfpv43O4aQDzErNv3GRqpx8DXBcOJIMP9yVhq-Mby5VH5J9cF-h-bJ5ws3xKjA4GY7YKjHxDt9OI-Zr7mr-V3qZy99UxJooThJj51f2RqOKhODdLh9XZQ0ygSoAd3iFAZDOPMEo8Ch5TrrzLXi2Q3N0HorIL1JfV0xoFQlY="
)
STRING_SESSION = (
    os.getenv("TELEGRAM_STRING_SESSION")
    or os.getenv("TELEGRAM_STRING_SESSION_ACC1")
    or os.getenv("STRING_SESSION")
    or DEFAULT_SESSION_ACC1
)

API_BASE = "https://46-101-192-249.sslip.io/api"
SESSION_FILE_PATH = os.getenv("TELEGRAM_SESSION_PATH", "C:/Users/Administrator/Downloads/kiemtien_autoplay/telepet_acc1.session")

def log(tag, msg, color=Fore.WHITE):
    t_str = time.strftime('%H:%M:%S')
    print(f"{Fore.LIGHTBLACK_EX}[{t_str}]{Style.RESET_ALL} {color}[{tag:<10}]{Style.RESET_ALL} {msg}")

class HashLaneBot:
    def __init__(self, string_session=None, session_path=None):
        self.string_session = string_session or STRING_SESSION
        self.session_path = session_path or SESSION_FILE_PATH
        self.init_data = None
        self.username = None
        self.points = 0
        self.gems = 0
        
        parts = [
            "Mozilla/5.0 (Linux; Android 14; SM-S928B Build/UP1A.231005.007; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/131.0.6778.135 Mobile Safari/537.36 Telegram-Android/11.5.0",
            "vi-VN",
            "384x854x24",
            "2.8125",
            "Asia/Ho_Chi_Minh",
            "8",
            "8",
            "Linux armv8l",
            "android"
        ]
        self.ua = parts[0]
        self.dev_fp = hashlib.sha256("|".join(parts).encode('utf-8')).hexdigest()

    async def fetch_tg_init_data(self):
        log("TELEGRAM", "Đang kết nối Telegram để lấy tgWebAppData HashLane...", Fore.CYAN)
        client = None
        try:
            if os.path.exists(self.session_path):
                client = TelegramClient(self.session_path, API_ID, API_HASH)
            else:
                client = TelegramClient(StringSession(self.string_session), API_ID, API_HASH)
            await client.connect()
            if not await client.is_user_authorized():
                log("TELEGRAM", "❌ Phiên Telegram không được ủy quyền!", Fore.RED)
                await client.disconnect()
                return False

            bot_entity = await client.get_entity("hashlane_bot")
            res = await client(RequestWebViewRequest(
                peer=bot_entity,
                bot=bot_entity,
                url="https://46-101-192-249.sslip.io/app/",
                platform="android"
            ))
            await client.disconnect()

            frag = res.url.split("#tgWebAppData=")[1].split("&tgWebAppVersion")[0]
            self.init_data = urllib.parse.unquote(frag)
            params = dict(urllib.parse.parse_qsl(self.init_data))
            user_obj = json.loads(params.get("user", "{}"))
            self.username = user_obj.get("username", str(user_obj.get("id")))
            log("TELEGRAM", f"✅ Lấy init_data thành công cho @{self.username}", Fore.GREEN)
            return True
        except Exception as e:
            log("TELEGRAM_ERR", f"Lỗi lấy WebApp Data: {e}", Fore.RED)
            if client and client.is_connected():
                await client.disconnect()
            return False

    def get_headers(self):
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Init-Data": self.init_data,
            "X-Device": self.dev_fp,
            "X-Tz-Offset": "420",
            "User-Agent": self.ua,
            "Origin": "https://46-101-192-249.sslip.io",
            "Referer": "https://46-101-192-249.sslip.io/app/"
        }

    def get_state(self):
        try:
            r = requests.get(f"{API_BASE}/me", headers=self.get_headers(), timeout=12)
            if r.status_code == 200:
                data = r.json()
                if data.get("ok"):
                    d = data.get("data", {})
                    u = d.get("user", {})
                    b = d.get("balances", {})
                    self.points = b.get("points", 0)
                    self.gems = b.get("gems", 0)
                    m = d.get("mining", {})
                    ses = m.get("session", {})
                    earned = ses.get("earned", 0)
                    capacity = ses.get("capacity", 100)
                    is_ready = ses.get("ready", False)
                    log("STATE", f"👤 User: @{u.get('username')} | Điểm: {self.points} | Gems: {self.gems} | Kho đào: {earned}/{capacity} (Sẵn sàng: {is_ready})", Fore.CYAN)
                    return d
            else:
                log("STATE_ERR", f"Lỗi lấy trạng thái HTTP {r.status_code}", Fore.RED)
        except Exception as e:
            log("STATE_ERR", f"Ngoại lệ get_state: {e}", Fore.RED)
        return None

    def checkin(self):
        try:
            r = requests.post(f"{API_BASE}/checkin", headers=self.get_headers(), json={}, timeout=10)
            if r.status_code == 200:
                d = r.json().get("data", {})
                log("CHECKIN", f"🎉 Điểm danh thành công Ngày {d.get('day', 1)}: +{d.get('points', 0)} Điểm!", Fore.GREEN)
            elif r.status_code == 409:
                log("CHECKIN", "ℹ️ Hôm nay đã điểm danh rồi.", Fore.LIGHTBLACK_EX)
        except Exception:
            pass

    def collect_and_restart_mining(self, state_data):
        m = state_data.get("mining", {}) if state_data else {}
        ses = m.get("session")
        if not ses:
            # Chưa có phiên đào nào -> Khởi động ngay
            log("MINING", "▶️ Chưa có phiên đào, tiến hành khởi động máy đào...", Fore.YELLOW)
            try:
                r = requests.post(f"{API_BASE}/mining/start", headers=self.get_headers(), json={}, timeout=10)
                if r.status_code == 200:
                    log("MINING", "✅ Đã bắt đầu ca đào mới 3600s (100 điểm/giờ)!", Fore.GREEN)
            except Exception as e:
                log("MINING_ERR", f"Lỗi start mining: {e}", Fore.RED)
            return

        is_ready = ses.get("ready", False)
        earned = ses.get("earned", 0)
        capacity = ses.get("capacity", 100)

        if is_ready or earned >= capacity:
            log("COLLECT", f"⛏️ Kho đào đã đầy ({earned}/{capacity} điểm). Tiến hành thu hoạch...", Fore.YELLOW)
            try:
                r_c = requests.post(f"{API_BASE}/mining/collect", headers=self.get_headers(), json={"double": False}, timeout=12)
                if r_c.status_code == 200:
                    cd = r_c.json().get("data", {})
                    self.points = cd.get("balance", self.points + earned)
                    log("COLLECT", f"🎉 THU HOẠCH THÀNH CÔNG +{cd.get('points', earned)} ĐIỂM! Số dư mới: {self.points} điểm.", Fore.GREEN)
                    
                    # Ngay sau khi collect, hệ thống thường tự động khởi động phiên mới
                    new_ses = cd.get("session")
                    if not new_ses or new_ses.get("earned", 0) > 0:
                        requests.post(f"{API_BASE}/mining/start", headers=self.get_headers(), json={}, timeout=10)
                else:
                    log("COLLECT_ERR", f"Lỗi thu hoạch: {r_c.text[:100]}", Fore.YELLOW)
            except Exception as e:
                log("COLLECT_ERR", f"Lỗi collect: {e}", Fore.RED)
        else:
            log("MINING", f"⏳ Máy đào đang hoạt động: {earned}/{capacity} điểm. Vòng đào tiếp theo sẽ đầy sau.", Fore.CYAN)

    async def run_cycle(self):
        ok = await self.fetch_tg_init_data()
        if not ok:
            return
        
        state = self.get_state()
        if not state:
            return

        self.checkin()
        self.collect_and_restart_mining(state)


def trigger_next_shift(workflow_file="game2_hashlane.yml"):
    repo = (os.getenv("GITHUB_REPOSITORY") or "nthanhhung0122-max/gram").strip()
    wf = (os.getenv("WORKFLOW_FILE") or workflow_file).strip()
    pat = (os.getenv("GH_PAT") or os.getenv("GITHUB_TOKEN") or "").strip()
    if not wf or not pat:
        log("HANDOVER", "Không có WORKFLOW_FILE hoặc GitHub Token để retrigger.", Fore.YELLOW)
        return False
    log("HANDOVER", f"🔄 Chuẩn bị chuyển giao ca làm việc tiếp theo trên {repo} ({wf})...", Fore.CYAN)
    url = f"https://api.github.com/repos/{repo}/actions/workflows/{wf}/dispatches"
    headers = {
        "Authorization": f"Bearer {pat}",
        "Accept": "application/vnd.github.v3+json"
    }
    try:
        r = requests.post(url, json={"ref": "main"}, headers=headers, timeout=15)
        if r.status_code in [200, 204]:
            log("HANDOVER", f"✅ Đã kích hoạt thành công ca chạy tiếp theo trên {repo} ({wf})!", Fore.GREEN)
            return True
        else:
            log("HANDOVER", f"Phản hồi dispatch: {r.status_code} {r.text}", Fore.YELLOW)
    except Exception as e:
        log("HANDOVER", f"Lỗi retrigger: {e}", Fore.RED)
    return False

async def run_loop_247(bot_instance, interval_mins=15):
    raw_rt = os.getenv("MAX_RUNTIME_SECONDS", "17500").strip()
    max_runtime = int(raw_rt) if raw_rt.isdigit() else 17500
    start_time = time.time()
    cycle = 1
    while True:
        log("LOOP", f"🌀 === BẮT ĐẦU CHU KỲ #{cycle} (HashLane) ===", Fore.MAGENTA)
        try:
            await bot_instance.run_cycle()
        except Exception as e:
            log("CYCLE_ERR", f"Lỗi chu kỳ #{cycle}: {e}", Fore.RED)
        
        cycle += 1
        elapsed = time.time() - start_time
        if elapsed >= max_runtime:
            log("HANDOVER", f"⏰ Hoàn thành ca trực ({elapsed/3600:.1f}h). Tự động chuyển giao ca tiếp theo...", Fore.CYAN)
            trigger_next_shift("game2_hashlane.yml")
            break
        
        log("LOOP", f"⏳ Nghỉ {interval_mins} phút trước chu kỳ tiếp theo (Đã trực {elapsed//60}m)...", Fore.YELLOW)
        await asyncio.sleep(interval_mins * 60)

async def main():
    import argparse
    parser = argparse.ArgumentParser(description="Bot Auto HashLane ($TON) 24/7")
    parser.add_argument("--loop", type=int, default=0, help="Số phút lặp lại (0 để chạy 1 lần)")
    args, _ = parser.parse_known_args()

    print(Fore.YELLOW + """
=============================================================================
  BOT AUTO HASHLANE ($TON) 24/7 - CHUẨN X-DEVICE FINGERPRINT
  Tự động Thu Hoạch 100 Điểm Kho Đầy | Tự động Bắt Đầu Vòng Mới | Điểm Danh
=============================================================================
    """ + Style.RESET_ALL)
    bot = HashLaneBot()
    if args.loop > 0:
        await run_loop_247(bot, interval_mins=args.loop)
    else:
        await bot.run_cycle()

if __name__ == "__main__":
    asyncio.run(main())
