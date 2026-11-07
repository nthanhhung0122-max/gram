#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
  BOT AUTO REDRIG ($TON) 24/7 - CHUẨN CƠ CHẾ MOONPOOL 100%
  Platform: REDRIG Mini App (https://redrig.159-198-44-230.sslip.io/)
  Telegram Bot: @redrig_bot
  
  TÍNH NĂNG TỰ ĐỘNG HÓA TOÀN DIỆN & CHUẨN XÁC:
    1. THU HOẠCH KÉT SẮT VAULT (/api/claim) định kỳ khi sẵn sàng.
    2. CHUYÊN CÀY CARD GPU (TIER 3 / TIER 2 / TIER 1) theo chuẩn Native Moonpool:
       - Tự động phát hiện dung lượng giàn Rack và chọn Tier cao nhất vừa slot.
       - Tự động tiếp tục open_session dở dang hoặc chờ cooldown thông minh.
       - Bước 1: Adsgram (Block 58154) với ping Reward URL thực tế.
       - Bước 2: Gigapub (Delay 6.5s) nếu Tier >= 2.
       - Bước 3: Monetag (Delay 6.5s) nếu Tier == 3.
       - Kết thúc: Đưa Card GPU mới vào giàn máy đào Rack!
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

    def boost_moonpool_gpu_chain(self, state):
        """
        CƠ CHẾ MOONPOOL CHUẨN XÁC TRÊN REDRIG:
        Tự động chọn Card Tier cao nhất (Tier 3 -> Tier 2 -> Tier 1) phù hợp với khe trống của Rack.
        Xem chuỗi QC theo tier (Adsgram -> Gigapub -> Monetag).
        Đưa Card GPU mới vào giàn máy đào Rack!
        """
        cfg = state.get("config", {})
        block_id = cfg.get("networks", {}).get("adsgram", {}).get("block_id") or "58154"
        srv_time = state.get("server_time", int(time.time() * 1000))

        ses_id = None
        tier = 3
        chain = ["adsgram", "gigapub", "monetag"]
        start_step = 1

        # 1. Kiểm tra session dở dang
        open_ses = state.get("open_session")
        if open_ses and open_ses.get("id"):
            exp = open_ses.get("expires_at", 0)
            if exp > srv_time:
                ses_id = open_ses.get("id")
                tier = open_ses.get("card_tier", 3)
                chain = open_ses.get("chain", ["adsgram", "gigapub", "monetag"])
                steps_done = open_ses.get("steps_done", 0)
                start_step = steps_done + 1
                log("GPU_MOONPOOL", f"Phát hiện ca GPU #{ses_id} (Tier {tier}) đang mở (Đã xong bước {steps_done}/{len(chain)}). Tiếp tục từ bước {start_step}!", Fore.MAGENTA)
            else:
                log("GPU_MOONPOOL", f"Phiên GPU #{open_ses.get('id')} đã hết hạn. Đang đóng...", Fore.YELLOW)
                requests.post(f"{API_BASE}/api/fish/finish", headers=self.get_headers(), json={"session_id": open_ses.get("id")}, timeout=8)
                time.sleep(2)

        # 2. Nếu chưa có session, chọn Tier tối ưu theo khe trống của Giàn Rack
        if not ses_id:
            cards = state.get("cards", [])
            # Tìm tier cao nhất mà fits == True
            fit_tier = None
            for t in [3, 2, 1]:
                c_info = next((c for c in cards if c.get("tier") == t), {})
                if c_info.get("fits"):
                    fit_tier = c_info
                    tier = t
                    chain = c_info.get("chain", ["adsgram"])
                    break

            if not fit_tier:
                log("GPU_MOONPOOL", "🖥️ Giàn máy đào Rack đã lấp đầy 100% tất cả các khe cắm! Đang vận hành ở công suất tối đa.", Fore.GREEN)
                return state

            cd_left = fit_tier.get("cooldown_left_sec", 0)
            if cd_left > 0:
                log("GPU_COOLDOWN", f"⏳ Ca cày GPU Tier {tier} đang hồi chiêu (còn {cd_left}s). Đang tự động chờ...", Fore.YELLOW)
                time.sleep(cd_left + 2)

            log("GPU_MOONPOOL", f"🚀 Kích hoạt quy trình xem QC cày Card GPU Tier {tier} (+{fit_tier.get('power')}⚡ Power)...", Fore.CYAN)
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
            chain = ses.get("chain", chain)
            start_step = 1
            log("GPU_MOONPOOL", f"✅ Khởi tạo thành công Phiên GPU #{ses_id}! Chuỗi {len(chain)} QC: {' -> '.join(chain)}", Fore.GREEN)

        try:
            # --- BƯỚC 1: ADSGRAM (nếu có trong chuỗi) ---
            if "adsgram" in chain and start_step <= 1:
                log("STEP1_ADSGRAM", f"Bước 1/{len(chain)}: Đang tải quảng cáo Adsgram (Block {block_id})...", Fore.YELLOW)
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
                    for u in re.findall(r'https://api\.adsgram\.ai/event\?[^\s\'"]+', r_adv.text):
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
                        log("STEP1_ADSGRAM", f"✓ Bước 1/{len(chain)} Adsgram hoàn thành thành công!", Fore.GREEN)
                        break
                    time.sleep(2)

                if not counted_s1:
                    log("STEP1_WARN", "Chưa xác nhận được Bước 1 Adsgram.", Fore.YELLOW)
                    requests.post(f"{API_BASE}/api/fish/finish", headers=self.get_headers(), json={"session_id": ses_id}, timeout=8)
                    return state

            # --- BƯỚC 2: GIGAPUB (nếu có trong chuỗi) ---
            if "gigapub" in chain and start_step <= 2:
                step_idx = chain.index("gigapub") + 1
                log("STEP2_GIGAPUB", f"Bước {step_idx}/{len(chain)}: Đang xem QC Gigapub (6.5s)...", Fore.YELLOW)
                time.sleep(6.5)
                counted_s2 = False
                for _ in range(5):
                    r_s2 = requests.post(f"{API_BASE}/api/fish/step", headers=self.get_headers(), json={"session_id": ses_id, "network": "gigapub"}, timeout=10).json()
                    if r_s2.get("counted"):
                        counted_s2 = True
                        log("STEP2_GIGAPUB", f"✓ Bước {step_idx}/{len(chain)} Gigapub hoàn thành thành công!", Fore.GREEN)
                        break
                    time.sleep(2)

                if not counted_s2:
                    log("STEP2_WARN", "Chưa xác nhận được Bước Gigapub.", Fore.YELLOW)

            # --- BƯỚC 3: MONETAG (nếu có trong chuỗi) ---
            if "monetag" in chain and start_step <= 3:
                step_idx = chain.index("monetag") + 1
                log("STEP3_MONETAG", f"Bước {step_idx}/{len(chain)}: Đang xem QC Monetag (6.5s)...", Fore.YELLOW)
                time.sleep(6.5)
                counted_s3 = False
                for _ in range(5):
                    r_s3 = requests.post(f"{API_BASE}/api/fish/step", headers=self.get_headers(), json={"session_id": ses_id, "network": "monetag"}, timeout=10).json()
                    if r_s3.get("counted"):
                        counted_s3 = True
                        log("STEP3_MONETAG", f"✓ Bước {step_idx}/{len(chain)} Monetag hoàn thành thành công!", Fore.GREEN)
                        break
                    time.sleep(2)

                if not counted_s3:
                    log("STEP3_WARN", "Chưa xác nhận được Bước Monetag.", Fore.YELLOW)

            # --- KẾT THÚC VÀ NHẬN CARD GPU VÀO RACK ---
            r_fin = requests.post(f"{API_BASE}/api/fish/finish", headers=self.get_headers(), json={"session_id": ses_id}, timeout=10).json()
            if r_fin.get("ok"):
                f = r_fin.get("fish", {})
                nst = r_fin.get("state", {})
                tot_pw = nst.get("power", {}).get("total", self.power)
                earn_new = nst.get("earn", {}).get("per_hour", self.earn_h)
                log("GPU_SUCCESS", f"🎉🎉🎉 ĐÃ NHẬN THÀNH CÔNG CARD GPU TIER {f.get('tier', tier)} (+{f.get('power')}⚡)! Tổng Power: {tot_pw}⚡ ({float(earn_new):.8f} TON/h)", Fore.GREEN)
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
        """Quản lý và hiển thị trạng thái các giàn máy đào Rack"""
        racks = state.get("racks", []) if state else []
        for rk in racks:
            idx = rk.get("idx", 1)
            active = rk.get("active", False)
            cards = rk.get("live_cards", 0)
            free = rk.get("free_spaces", 0)
            log("RACK", f"🖥️ Rack #{idx}: {'Đang hoạt động' if active else 'Chưa kích hoạt'} | Cắm {cards} Card GPU | Trống {free} chỗ", Fore.CYAN)

    def boost_rack_unlock_chain(self, state):
        """Xem chuỗi 3 QC để mở khóa thêm Rack máy đào mới (Chuẩn chống 429 & Resume Open Session)"""
        cfg = state.get("config", {})
        block_id = cfg.get("networks", {}).get("adsgram", {}).get("block_id") or "58154"
        ru = state.get("rack_unlock", {})
        done = ru.get("ads_done", 0)
        needed = ru.get("ads_needed", 9)
        srv_time = state.get("server_time", int(time.time() * 1000))

        # 1. Kiểm tra Cooldown hồi chiêu của Rack Unlock (ready_at)
        ready_at = ru.get("ready_at", 0)
        if ready_at and ready_at > srv_time:
            cd_left = int((ready_at - srv_time) / 1000)
            if cd_left > 0:
                log("RACK_COOLDOWN", f"⏳ Ca mở khóa Rack đang trong thời gian hồi chiêu (còn {cd_left}s). Đang tự động chờ...", Fore.YELLOW)
                time.sleep(min(cd_left + 2, 65))
                return state

        ses_id = None
        chain = ["adsgram", "gigapub", "monetag"]
        start_step = 1

        # 2. Tự động kiểm tra & khôi phục nếu đang có open_session cho Rack
        open_ses = state.get("open_session")
        if open_ses and open_ses.get("id"):
            exp = open_ses.get("expires_at", 0)
            purpose = open_ses.get("purpose", "")
            if purpose == "rack" and exp > srv_time:
                ses_id = open_ses.get("id")
                chain = open_ses.get("chain", chain)
                steps_done = open_ses.get("steps_done", 0)
                start_step = steps_done + 1
                log("RACK_UNLOCK", f"Phát hiện ca mở Rack #{ses_id} đang mở (Đã xong {steps_done}/{len(chain)} bước). Tiếp tục từ bước {start_step}!", Fore.MAGENTA)
            elif exp <= srv_time:
                log("RACK_UNLOCK", f"Phiên cũ #{open_ses.get('id')} đã hết hạn. Đang đóng...", Fore.YELLOW)
                try: requests.post(f"{API_BASE}/api/fish/finish", headers=self.get_headers(), json={"session_id": open_ses.get("id")}, timeout=8)
                except Exception: pass
                time.sleep(2)

        # 3. Khởi tạo phiên Unlock Rack nếu chưa có session
        if not ses_id:
            log("RACK_UNLOCK", f"🔓 Kích hoạt chuỗi QC mở khóa Giàn Máy Đào Rack mới (Tiến độ: {done}/{needed} ads)...", Fore.CYAN)
            r_start = requests.post(f"{API_BASE}/api/rack/start", headers=self.get_headers(), json={"target": "new"}, timeout=10)
            
            if r_start.status_code == 429:
                err_data = {}
                try: err_data = r_start.json()
                except Exception: pass
                log("RACK_COOLDOWN", f"Gặp giới hạn tần suất mở rack (HTTP 429: {err_data.get('code', 'cooldown')}). Chờ 65s...", Fore.YELLOW)
                time.sleep(65)
                return state

            if r_start.status_code != 200:
                log("RACK_WARN", f"Chưa thể mở khóa rack (HTTP {r_start.status_code})", Fore.YELLOW)
                return state

            d_start = r_start.json()
            if not d_start.get("ok"):
                log("RACK_WARN", f"Thông báo: {d_start.get('error')}", Fore.YELLOW)
                return state

            ses = d_start.get("session", {})
            ses_id = ses.get("id")
            chain = ses.get("chain", chain)
            start_step = 1
            log("RACK_UNLOCK", f"✅ Phiên Unlock Rack #{ses_id} đã mở! Chuỗi {len(chain)} QC: {' -> '.join(chain)}", Fore.GREEN)

        try:
            # Step 1: Adsgram
            if "adsgram" in chain and start_step <= 1:
                log("STEP1_ADSGRAM", "Bước 1/3: Xem QC Adsgram mở Rack...", Fore.YELLOW)
                ad_headers = {
                    'User-Agent': self.ua, 'Origin': API_BASE, 'Referer': f"{API_BASE}/",
                    'Accept': 'application/json', 'X-Requested-With': 'org.telegram.messenger'
                }
                adv_params = {
                    'blockId': block_id, 'tg_id': self.user_id, 'tg_platform': 'android',
                    'platform': 'Linux aarch64', 'language': 'vi', 'top_domain': 'sslip.io',
                    'signature': self.sig, 'data_check_string': self.dcs, 'sdk_version': '2.2.5'
                }
                r_adv = requests.get('https://api.adsgram.ai/adv', headers=ad_headers, params=adv_params, timeout=12)
                if r_adv.status_code == 200:
                    for u in re.findall(r'https://api\.adsgram\.ai/event\?[^\s\'"]+', r_adv.text):
                        if 'Reward' in u or 'type=Reward' in u:
                            time.sleep(6.5)
                            requests.get(u, headers=ad_headers, timeout=10)
                            time.sleep(3)
                            break
                for _ in range(6):
                    r_s1 = requests.post(f"{API_BASE}/api/fish/step", headers=self.get_headers(), json={"session_id": ses_id, "network": "adsgram"}, timeout=10).json()
                    if r_s1.get("counted"):
                        log("STEP1_ADSGRAM", "✓ Bước 1 Adsgram thành công!", Fore.GREEN)
                        break
                    time.sleep(2)

            # Step 2: Gigapub
            if "gigapub" in chain and start_step <= 2:
                log("STEP2_GIGAPUB", "Bước 2/3: Xem QC Gigapub (6.5s)...", Fore.YELLOW)
                time.sleep(6.5)
                for _ in range(5):
                    r_s2 = requests.post(f"{API_BASE}/api/fish/step", headers=self.get_headers(), json={"session_id": ses_id, "network": "gigapub"}, timeout=10).json()
                    if r_s2.get("counted"):
                        log("STEP2_GIGAPUB", "✓ Bước 2 Gigapub thành công!", Fore.GREEN)
                        break
                    time.sleep(2)

            # Step 3: Monetag
            if "monetag" in chain and start_step <= 3:
                log("STEP3_MONETAG", "Bước 3/3: Xem QC Monetag (6.5s)...", Fore.YELLOW)
                time.sleep(6.5)
                for _ in range(5):
                    r_s3 = requests.post(f"{API_BASE}/api/fish/step", headers=self.get_headers(), json={"session_id": ses_id, "network": "monetag"}, timeout=10).json()
                    if r_s3.get("counted"):
                        log("STEP3_MONETAG", "✓ Bước 3 Monetag thành công!", Fore.GREEN)
                        break
                    time.sleep(2)

            # Finish
            r_fin = requests.post(f"{API_BASE}/api/fish/finish", headers=self.get_headers(), json={"session_id": ses_id}, timeout=10).json()
            if r_fin.get("ok"):
                nst = r_fin.get("state", {})
                nru = nst.get("rack_unlock", {})
                rk = r_fin.get("rack", {})
                applied = rk.get("applied")
                if applied:
                    log("RACK_SUCCESS", f"🎉🎉🎉 CHÚC MỪNG! ĐÃ MỞ KHÓA THÀNH CÔNG RACK #{applied.get('idx', 2)}!", Fore.GREEN)
                else:
                    new_done = nru.get("ads_done", done + 3)
                    log("RACK_SUCCESS", f"🎉 HOÀN THÀNH CHUỖI MỞ RACK! Tiến độ mới: {new_done}/{needed} ads", Fore.GREEN)
                return nst
        except Exception as e:
            log("RACK_ERR", f"Lỗi trong chuỗi mở rack: {e}", Fore.RED)
            try: requests.post(f"{API_BASE}/api/fish/finish", headers=self.get_headers(), json={"session_id": ses_id}, timeout=8)
            except Exception: pass
        return state

    async def run_cycle(self):
        ok = await self.fetch_tg_init_data()
        if not ok:
            return
        
        state = self.authenticate()
        if not state:
            return

        # 1. Thu hoạch két sắt TON
        state = self.check_and_claim_vault(state)
        
        # 2. Cày Card GPU theo chuẩn Native Moonpool (Tự động chọn Tier phù hợp với Rack)
        state = self.boost_moonpool_gpu_chain(state)
        
        # 3. Kiểm tra & Nhận Daily Streak
        self.check_and_claim_streak(state)

        # 4. Kiểm tra & duy trì Rack
        self.manage_racks(state)


def trigger_next_shift(workflow_file="game3_redrig.yml"):
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

async def run_loop_247(bot_instance, interval_mins=0):
    raw_rt = os.getenv("MAX_RUNTIME_SECONDS", "17500").strip()
    max_runtime = int(raw_rt) if raw_rt.isdigit() else 17500
    start_time = time.time()
    last_vault_check = 0
    ad_cycle = 0
    
    log("CONTINUOUS", "🔥 CHẾ ĐỘ CÀY QC REDRIG (GPU & MỞ RACK) LIÊN TỤC 24/7 ĐÃ BẬT!", Fore.GREEN)
    
    ok = await bot_instance.fetch_tg_init_data()
    if not ok:
        log("INIT_ERR", "Không thể lấy init_data ban đầu.", Fore.RED)
        return

    while True:
        elapsed = time.time() - start_time
        if elapsed >= max_runtime:
            log("HANDOVER", f"⏰ Hoàn thành ca trực ({elapsed/3600:.1f}h). Tự động chuyển giao ca tiếp theo...", Fore.CYAN)
            trigger_next_shift("game3_redrig.yml")
            break

        now = time.time()
        state = bot_instance.authenticate()
        if not state:
            await asyncio.sleep(15)
            continue

        # 1. Thu hoạch Két Sắt TON & Check Daily Streak định kỳ
        if now - last_vault_check >= 300:
            state = bot_instance.check_and_claim_vault(state)
            bot_instance.check_and_claim_streak(state)
            last_vault_check = now

        # 2. XÁC ĐỊNH CÀY CARD GPU HAY MỞ KHÓA RACK MỚI
        racks = state.get("racks", [])
        # Kiểm tra xem có bất kỳ rack nào còn chỗ cắm card (fit 1, 2, hoặc 3)
        has_fit = any(any(r.get("fits", {}).values()) for r in racks)
        ru = state.get("rack_unlock", {})
        can_new_rack = ru.get("can_new", False)

        ad_cycle += 1
        if has_fit:
            log("CONTINUOUS", f"🚀 [CA #{ad_cycle}] Giàn Rack còn chỗ -> Tiến hành cày Card GPU...", Fore.CYAN)
            state = bot_instance.boost_moonpool_gpu_chain(state)
        elif can_new_rack:
            log("CONTINUOUS", f"🚀 [CA #{ad_cycle}] Giàn Rack 1 kín 100% -> Tiến hành cày QC mở khóa Rack mới...", Fore.MAGENTA)
            state = bot_instance.boost_rack_unlock_chain(state)
        else:
            log("CONTINUOUS", f"🚀 [CA #{ad_cycle}] Đang vận hành tối đa công suất.", Fore.GREEN)

        # Kiểm tra Streak sau mỗi ca xem QC
        bot_instance.check_and_claim_streak(state)

        # 3. NGHỈ COOLDOWN 62 GIÂY THEO QUY ĐỊNH CỦA SERVER RỒI CÀY TIẾP NGAY
        log("CONTINUOUS", "⏳ Chờ hồi chiêu 62s trước ca cày quảng cáo tiếp theo...", Fore.LIGHTBLACK_EX)
        await asyncio.sleep(62)

async def main():
    import argparse
    parser = argparse.ArgumentParser(description="Bot Auto REDRIG ($TON) 24/7")
    parser.add_argument("--loop", type=int, default=0, help="Số phút lặp lại (0 để chạy 1 lần)")
    args, _ = parser.parse_known_args()

    print(Fore.YELLOW + """
=============================================================================
  BOT AUTO REDRIG ($TON) 24/7 - CHUẨN CƠ CHẾ MOONPOOL 100%
  Tự động Thu Hoạch Két Sắt Mỗi Giờ | Cày Card GPU Phù Hợp Giàn Máy Đào
=============================================================================
    """ + Style.RESET_ALL)
    bot = RedRigBot()
    if args.loop > 0:
        await run_loop_247(bot, interval_mins=args.loop)
    else:
        await bot.run_cycle()

if __name__ == "__main__":
    asyncio.run(main())
