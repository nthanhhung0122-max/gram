#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
  BOT AUTO REDRIG ($TON) 24/7 - CHUẨN CƠ CHẾ MOONPOOL 100%
  Platform: REDRIG Mini App (https://redrig.159-198-44-230.sslip.io/)
  Telegram Bot: @redrig_bot
  
  TÍNH NĂNG TỰ ĐỘNG HÓA TOÀN DIỆN & CHUẨN XÁC:
    1. THU HOẠCH KÉT SẮT VAULT (/api/claim) định kỳ khi sẵn sàng.
    2. CHUYÊN CÀY CARD GPU TIER 3 (+12⚡ POWER) theo chuẩn Native Moonpool:
       - Tự động tiếp tục open_session dở dang hoặc chờ cooldown thông minh.
       - Bước 1: Adsgram (Block 58154) với ping Reward URL thực tế.
       - Bước 2: Gigapub (Delay 6.5s).
       - Bước 3: Monetag (Delay 6.5s).
       - Kết thúc: Đưa Card GPU Tier 3 (+12⚡) vào giàn máy đào Rack!
    3. NHẬN THƯỞNG DAILY STREAK (/api/tasks/streak/claim) khi đủ điều kiện.
    4. KIỂM TRA & DUY TRÌ GIÀN MÁY ĐÀO RACK (/api/rack/start) tối ưu hóa công suất.
=============================================================================
"""

import os
import sys
import time
import json
import random
import re
import base64
import asyncio
import urllib.parse
import urllib3
import requests
from colorama import init, Fore, Style

from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.messages import RequestWebViewRequest

urllib3.disable_warnings()
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

API_BASE = "https://redrig.159-198-44-230.sslip.io"
SESSION_FILE_PATH = os.getenv("TELEGRAM_SESSION_PATH", "C:/Users/Administrator/Downloads/kiemtien_autoplay/telepet_acc1.session")

def log(tag, msg, color=Fore.WHITE):
    t_str = time.strftime('%H:%M:%S')
    print(f"{Fore.LIGHTBLACK_EX}[{t_str}]{Style.RESET_ALL} {color}[{tag:<14}]{Style.RESET_ALL} {msg}", flush=True)

class RedRigBot:
    def __init__(self, string_session=None, session_path=None):
        self.string_session = string_session or STRING_SESSION
        self.session_path = session_path or SESSION_FILE_PATH
        self.init_data = None
        self.user_obj = None
        self.user_id = None
        self.username = None
        self.sig = ""
        self.dcs = ""
        self.balance = "0.0"
        self.power = 0
        self.earn_h = "0"
        self.ua = (
            "Mozilla/5.0 (Linux; Android 14; SM-S928B Build/UP1A.231005.007; wv) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/131.0.6778.135 "
            "Mobile Safari/537.36 Telegram-Android/11.5.0"
        )

    async def fetch_tg_init_data(self):
        log("TELEGRAM", "Đang kết nối Telegram để lấy tgWebAppData REDRIG...", Fore.CYAN)
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

            bot_entity = await client.get_entity("redrig_bot")
            res = await client(RequestWebViewRequest(
                peer=bot_entity,
                bot=bot_entity,
                url="https://redrig.159-198-44-230.sslip.io/",
                platform="android"
            ))
            await client.disconnect()

            frag = res.url.split("#tgWebAppData=")[1].split("&tgWebAppVersion")[0]
            self.init_data = urllib.parse.unquote(frag)
            params = dict(urllib.parse.parse_qsl(self.init_data))
            self.user_obj = json.loads(params.get("user", "{}"))
            self.user_id = str(self.user_obj.get("id"))
            self.username = self.user_obj.get("username", self.user_id)
            self.sig = params.get("signature", "")

            # Tính data_check_string chuẩn
            pairs = []
            for k, v in urllib.parse.parse_qsl(self.init_data):
                if k not in ['hash', 'signature']:
                    pairs.append(f"{k}={v}")
            pairs.sort()
            raw = "\n".join(pairs)
            self.dcs = base64.b64encode(raw.encode('utf-8')).decode('ascii').replace('+', '-').replace('/', '_').rstrip('=')

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
            "X-Telegram-Init-Data": self.init_data,
            "User-Agent": self.ua,
            "Origin": API_BASE,
            "Referer": f"{API_BASE}/"
        }

    def authenticate(self):
        try:
            r = requests.post(f"{API_BASE}/api/auth", headers=self.get_headers(), json={}, timeout=12)
            if r.status_code == 200:
                data = r.json()
                if data.get("ok"):
                    st = data.get("state", {})
                    u = st.get("user", {})
                    self.balance = st.get("balance", "0.0")
                    pw = st.get("power", {})
                    self.power = pw.get("total", 0)
                    self.earn_h = st.get("earn", {}).get("per_hour", "0")
                    log("AUTH", f"✅ Đăng nhập REDRIG! User: @{u.get('username')} | Số dư: {self.balance} TON | Công suất: {self.power} Power ({float(self.earn_h):.8f} TON/h)", Fore.GREEN)
                    return st
            log("AUTH_ERR", f"Lỗi xác thực HTTP {r.status_code}", Fore.RED)
        except Exception as e:
            log("AUTH_ERR", f"Ngoại lệ auth: {e}", Fore.RED)
        return None

    def check_and_claim_vault(self, state):
        v = state.get("vault", {}) if state else {}
        claimable = v.get("claimable", False)
        pending = v.get("pending", "0")
        capacity = v.get("capacity", "0")
        progress = float(v.get("progress", 0.0))
        sec_left = v.get("seconds_to_full", 0)

        log("VAULT", f"🔐 Két sắt: {pending}/{capacity} TON ({progress*100:.1f}%) | Đầy sau: ~{sec_left//60}p | Sẵn sàng: {claimable}", Fore.CYAN)

        if claimable or progress >= 0.99:
            log("CLAIM", f"🎉 Két sắt đã sẵn sàng! Tiến hành thu hoạch {pending} TON...", Fore.YELLOW)
            try:
                r_c = requests.post(f"{API_BASE}/api/claim", headers=self.get_headers(), json={}, timeout=12)
                if r_c.status_code == 200:
                    cd = r_c.json()
                    if cd.get("ok"):
                        amt = cd.get("amount", pending)
                        nst = cd.get("state", {})
                        self.balance = nst.get("balance", self.balance)
                        log("CLAIM", f"🎉 THU HOẠCH KÉT SẮT THÀNH CÔNG: +{amt} TON! Số dư mới: {self.balance} TON.", Fore.GREEN)
                        return nst
            except Exception as e:
                log("CLAIM_ERR", f"Lỗi thu hoạch két sắt: {e}", Fore.RED)
        return state

    def boost_moonpool_gpu_chain(self, state, tier=3):
        """
        CƠ CHẾ MOONPOOL CHUẨN XÁC TRÊN REDRIG:
        Xem chuỗi 3 QC để nhận Card GPU Tier 3 (+12⚡ Power khai thác trong 24h).
        Bước 1: Adsgram (Block 58154) với ping Reward URL thực tế.
        Bước 2: Gigapub (Delay 6.5s).
        Bước 3: Monetag (Delay 6.5s).
        Kết thúc: Nhận Card GPU Tier 3 (+12⚡ Power)!
        """
        log("GPU_MOONPOOL", f"🚀 Kích hoạt quy trình xem QC cày Card GPU Tier {tier} (+12⚡ Power)...", Fore.CYAN)
        
        cfg = state.get("config", {})
        block_id = cfg.get("networks", {}).get("adsgram", {}).get("block_id") or "58154"
        srv_time = state.get("server_time", int(time.time() * 1000))

        ses_id = None
        start_step = 1

        # 1. Kiểm tra session dở dang
        open_ses = state.get("open_session")
        if open_ses and open_ses.get("id"):
            exp = open_ses.get("expires_at", 0)
            if exp > srv_time:
                ses_id = open_ses.get("id")
                steps_done = open_ses.get("steps_done", 0)
                start_step = steps_done + 1
                log("GPU_MOONPOOL", f"Phát hiện ca GPU #{ses_id} đang mở (Đã xong bước {steps_done}/3). Tiếp tục từ bước {start_step}!", Fore.MAGENTA)
            else:
                log("GPU_MOONPOOL", f"Phiên GPU #{open_ses.get('id')} đã hết hạn. Đang đóng...", Fore.YELLOW)
                requests.post(f"{API_BASE}/api/fish/finish", headers=self.get_headers(), json={"session_id": open_ses.get("id")}, timeout=8)
                time.sleep(2)

        # 2. Nếu chưa có session, kiểm tra Cooldown và khởi tạo ca mới
        if not ses_id:
            # Kiểm tra thời gian hồi chiêu của Card Tier 3
            cards = state.get("cards", [])
            target_card = next((c for c in cards if c.get("tier") == tier), {})
            cd_left = target_card.get("cooldown_left_sec", 0)

            if cd_left > 0:
                log("GPU_COOLDOWN", f"⏳ Ca cày GPU Tier 3 đang hồi chiêu (còn {cd_left}s). Đang tự động chờ...", Fore.YELLOW)
                time.sleep(cd_left + 2)

            log("GPU_MOONPOOL", f"Bắt đầu mở ca cày Card GPU Tier {tier} mới (/api/fish/start)...", Fore.CYAN)
            r_start = requests.post(f"{API_BASE}/api/fish/start", headers=self.get_headers(), json={"tier": tier}, timeout=10)
            
            if r_start.status_code == 429:
                log("GPU_COOLDOWN", "Gặp giới hạn tần suất (HTTP 429). Chờ 15s để thử lại...", Fore.YELLOW)
                time.sleep(15)
                r_start = requests.post(f"{API_BASE}/api/fish/start", headers=self.get_headers(), json={"tier": tier}, timeout=10)

            if r_start.status_code != 200:
                log("GPU_WARN", f"Chưa thể bắt đầu ca mới (HTTP {r_start.status_code})", Fore.YELLOW)
                return state

            d_start = r_start.json()
            if not d_start.get("ok"):
                log("GPU_WARN", f"Thông báo từ REDRIG: {d_start.get('error', 'Chưa sẵn sàng')}", Fore.YELLOW)
                return state

            ses = d_start.get("session", {})
            ses_id = ses.get("id")
            start_step = 1
            log("GPU_MOONPOOL", f"✅ Khởi tạo thành công Phiên GPU #{ses_id}! Bắt đầu chuỗi 3 QC...", Fore.GREEN)

        try:
            # --- BƯỚC 1: ADSGRAM ---
            if start_step <= 1:
                log("STEP1_ADSGRAM", f"Bước 1/3: Đang tải quảng cáo Adsgram (Block {block_id})...", Fore.YELLOW)
                ad_headers = {
                    'User-Agent': self.ua,
                    'Origin': API_BASE,
                    'Referer': f"{API_BASE}/",
                    'Accept': 'application/json',
                    'X-Requested-With': 'org.telegram.messenger'
                }
                adv_params = {
                    'blockId': block_id,
                    'tg_id': self.user_id,
                    'tg_platform': 'android',
                    'platform': 'Linux aarch64',
                    'language': 'vi',
                    'top_domain': 'sslip.io',
                    'signature': self.sig,
                    'data_check_string': self.dcs,
                    'sdk_version': '2.2.5'
                }
                r_adv = requests.get('https://api.adsgram.ai/adv', headers=ad_headers, params=adv_params, timeout=12)
                if r_adv.status_code == 200:
                    reward_url = None
                    for u in re.findall(r'https://api\.adsgram\.ai/event\?[^\s\'"\\]+', r_adv.text):
                        if 'Reward' in u or 'type=Reward' in u:
                            reward_url = u
                            break
                    if reward_url:
                        log("STEP1_ADSGRAM", "Đang xem video Adsgram (6.5s)...", Fore.YELLOW)
                        time.sleep(6.5)
                        requests.get(reward_url, headers=ad_headers, timeout=10)
                        time.sleep(3)

                counted_s1 = False
                for _ in range(6):
                    r_s1 = requests.post(f"{API_BASE}/api/fish/step", headers=self.get_headers(), json={"session_id": ses_id, "network": "adsgram"}, timeout=10).json()
                    if r_s1.get("counted"):
                        counted_s1 = True
                        log("STEP1_ADSGRAM", "✓ Bước 1 Adsgram hoàn thành thành công!", Fore.GREEN)
                        break
                    time.sleep(2)

                if not counted_s1:
                    log("STEP1_WARN", "Chưa xác nhận được Bước 1 Adsgram.", Fore.YELLOW)
                    requests.post(f"{API_BASE}/api/fish/finish", headers=self.get_headers(), json={"session_id": ses_id}, timeout=8)
                    return state

            # --- BƯỚC 2: GIGAPUB ---
            if start_step <= 2:
                log("STEP2_GIGAPUB", "Bước 2/3: Đang xem QC Gigapub (6.5s)...", Fore.YELLOW)
                time.sleep(6.5)
                counted_s2 = False
                for _ in range(5):
                    r_s2 = requests.post(f"{API_BASE}/api/fish/step", headers=self.get_headers(), json={"session_id": ses_id, "network": "gigapub"}, timeout=10).json()
                    if r_s2.get("counted"):
                        counted_s2 = True
                        log("STEP2_GIGAPUB", "✓ Bước 2 Gigapub hoàn thành thành công!", Fore.GREEN)
                        break
                    time.sleep(2)

                if not counted_s2:
                    log("STEP2_WARN", "Chưa xác nhận được Bước 2 Gigapub.", Fore.YELLOW)

            # --- BƯỚC 3: MONETAG ---
            if start_step <= 3:
                log("STEP3_MONETAG", "Bước 3/3: Đang xem QC Monetag (6.5s)...", Fore.YELLOW)
                time.sleep(6.5)
                counted_s3 = False
                for _ in range(5):
                    r_s3 = requests.post(f"{API_BASE}/api/fish/step", headers=self.get_headers(), json={"session_id": ses_id, "network": "monetag"}, timeout=10).json()
                    if r_s3.get("counted"):
                        counted_s3 = True
                        log("STEP3_MONETAG", "✓ Bước 3 Monetag hoàn thành thành công!", Fore.GREEN)
                        break
                    time.sleep(2)

                if not counted_s3:
                    log("STEP3_WARN", "Chưa xác nhận được Bước 3 Monetag.", Fore.YELLOW)

            # --- KẾT THÚC VÀ NHẬN CARD GPU CẤP 3 (+12⚡ POWER) ---
            r_fin = requests.post(f"{API_BASE}/api/fish/finish", headers=self.get_headers(), json={"session_id": ses_id}, timeout=10).json()
            if r_fin.get("ok"):
                f = r_fin.get("fish", {})
                nst = r_fin.get("state", {})
                tot_pw = nst.get("power", {}).get("total", self.power)
                earn_new = nst.get("earn", {}).get("per_hour", self.earn_h)
                log("GPU_SUCCESS", f"🎉🎉🎉 ĐÃ NHẬN THÀNH CÔNG CARD GPU TIER {f.get('tier', 3)} (+{f.get('power', 12)}⚡)! Tổng Power: {tot_pw}⚡ ({float(earn_new):.8f} TON/h)", Fore.GREEN)
                return nst
            else:
                log("GPU_WARN", f"Kết thúc chuỗi: {r_fin.get('close_reason', 'done')}", Fore.YELLOW)
        except Exception as e:
            log("GPU_ERR", f"Lỗi trong chuỗi QC Moonpool: {e}", Fore.RED)
            try: requests.post(f"{API_BASE}/api/fish/finish", headers=self.get_headers(), json={"session_id": ses_id}, timeout=8)
            except Exception: pass
        return state

    def check_and_claim_streak(self, state):
        """Kiểm tra và nhận thưởng Daily Streak khi đủ điều kiện"""
        tasks = state.get("tasks", []) if state else []
        st_task = next((t for t in tasks if t.get("id") == "streak"), None)
        if not st_task:
            return

        prog = st_task.get("progress", {})
        cur = prog.get("current", 0)
        tgt = prog.get("target", 5)
        streak_info = st_task.get("streak", {})
        claimed = streak_info.get("claimed_today", False)
        day = streak_info.get("day", 1)
        days = streak_info.get("days", 7)

        if claimed:
            log("STREAK", f"✅ Hôm nay đã nhận thưởng Daily Streak (Ngày {day}/{days})!", Fore.GREEN)
            return

        log("STREAK", f"📅 Tiến độ Streak hôm nay: {cur}/{tgt} ads (Ngày {day}/{days})", Fore.CYAN)
        if cur >= tgt:
            log("STREAK", f"🎉 Đã đủ điều kiện nhận thưởng Daily Streak! Tiến hành nhận...", Fore.YELLOW)
            try:
                r = requests.post(f"{API_BASE}/api/tasks/streak/claim", headers=self.get_headers(), json={}, timeout=10)
                if r.status_code == 200:
                    d = r.json()
                    if d.get("ok"):
                        gr = d.get("granted", {})
                        pw = gr.get("power", 6)
                        log("STREAK", f"🎁 NHẬN THÀNH CÔNG DAILY STREAK: +{pw}⚡ Power!", Fore.GREEN)
                    elif d.get("already"):
                        log("STREAK", "✅ Hôm nay đã nhận thưởng Streak rồi.", Fore.GREEN)
            except Exception as e:
                log("STREAK_ERR", f"Lỗi nhận thưởng Streak: {e}", Fore.RED)

    def manage_racks(self, state):
        """Quản lý và kích hoạt giàn máy đào Rack"""
        racks = state.get("racks", []) if state else []
        for rk in racks:
            idx = rk.get("idx", 1)
            active = rk.get("active", False)
            cards = rk.get("live_cards", 0)
            free = rk.get("free_spaces", 0)
            log("RACK", f"🖥️ Rack #{idx}: {'Đang hoạt động' if active else 'Chưa kích hoạt'} | Cắm {cards} Card GPU | Trống {free} chỗ", Fore.CYAN)

        try:
            r = requests.post(f"{API_BASE}/api/rack/start", headers=self.get_headers(), json={"target": "new"}, timeout=10)
            if r.status_code == 200:
                pass
        except Exception:
            pass

    async def run_cycle(self):
        ok = await self.fetch_tg_init_data()
        if not ok:
            return
        
        state = self.authenticate()
        if not state:
            return

        # 1. Thu hoạch két sắt TON
        state = self.check_and_claim_vault(state)
        
        # 2. Cày Card GPU Tier 3 (+12⚡ Power) theo chuẩn Native Moonpool
        state = self.boost_moonpool_gpu_chain(state, tier=3)
        
        # 3. Kiểm tra & Nhận Daily Streak
        self.check_and_claim_streak(state)

        # 4. Kiểm tra & duy trì Rack
        self.manage_racks(state)

async def main():
    print(Fore.YELLOW + """
=============================================================================
  BOT AUTO REDRIG ($TON) 24/7 - CHUẨN CƠ CHẾ MOONPOOL 100%
  Tự động Thu Hoạch Két Sắt Mỗi Giờ | Cày Card GPU Tier 3 (+12⚡ Power)
=============================================================================
    """ + Style.RESET_ALL)
    bot = RedRigBot()
    await bot.run_cycle()

if __name__ == "__main__":
    asyncio.run(main())
