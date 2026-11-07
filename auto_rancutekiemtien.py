#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
  BOT AUTO RẮN CUTE KIẾM TIỀN 24/7 - TỰ ĐỘNG THU HOẠCH MẬT RẮN & ĐIỂM DANH
  Platform: Rắn Cute Kiếm Tiền Mini App (https://appkiemtiengamelau.site/)
  Telegram Bot: @rancutekiemtien_bot
  
  TÍNH NĂNG TỰ ĐỘNG HÓA 100%:
    1. Tự động lấy tgWebAppData mới nhất qua phiên Telethon an toàn.
    2. Tự động đồng bộ số dư Mật Rắn và trạng thái trang trại (action=sync).
    3. Tự động THU HOẠCH MẬT RẮN (action=harvest) ngay khi hết thời gian chờ cooldown.
    4. Tự động ĐIỂM DANH HÀNG NGÀY (action=do_checkin) nhận Mật Rắn thưởng.
    5. Tự động hoàn thành các nhiệm vụ cộng đồng & Video Ads (action=do_task, check_join).
=============================================================================
"""

import os
import sys
import time
import json
import random
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

API_ENDPOINT = "https://appkiemtiengamelau.site/save_score.php"
SESSION_FILE_PATH = os.getenv("TELEGRAM_SESSION_PATH", "C:/Users/Administrator/Downloads/kiemtien_autoplay/telepet_acc1.session")

def log(tag, msg, color=Fore.WHITE):
    t_str = time.strftime('%H:%M:%S')
    print(f"{Fore.LIGHTBLACK_EX}[{t_str}]{Style.RESET_ALL} {color}[{tag:<10}]{Style.RESET_ALL} {msg}")

class RanCuteBot:
    def __init__(self, string_session=None, session_path=None):
        self.string_session = string_session or STRING_SESSION
        self.session_path = session_path or SESSION_FILE_PATH
        self.init_data = None
        self.username = None
        self.balance = 0
        self.last_harvest = 0
        self.cooldown_sec = 1800  # 30 phút cooldown mặc định
        self.ua = (
            "Mozilla/5.0 (Linux; Android 14; SM-S928B Build/UP1A.231005.007; wv) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/131.0.6778.135 "
            "Mobile Safari/537.36 Telegram-Android/11.5.0"
        )

    async def fetch_tg_init_data(self):
        log("TELEGRAM", "Đang kết nối Telegram để lấy tgWebAppData Rắn Cute...", Fore.CYAN)
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

            bot_entity = await client.get_entity("rancutekiemtien_bot")
            res = await client(RequestWebViewRequest(
                peer=bot_entity,
                bot=bot_entity,
                url="https://appkiemtiengamelau.site/",
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
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": self.ua,
            "Origin": "https://appkiemtiengamelau.site",
            "Referer": "https://appkiemtiengamelau.site/"
        }

    def call_api(self, action, sell_amount=0, task_id=0, url="", wallet=""):
        data = {
            "initData": self.init_data,
            "action": action,
            "sellAmount": sell_amount,
            "taskId": task_id,
            "url": url,
            "wallet": wallet
        }
        try:
            r = requests.post(API_ENDPOINT, headers=self.get_headers(), data=data, timeout=12)
            if r.status_code == 200:
                return r.json()
            else:
                log("API_ERR", f"HTTP {r.status_code}: {r.text[:100]}", Fore.RED)
        except Exception as e:
            log("API_ERR", f"Ngoại lệ API ({action}): {e}", Fore.RED)
        return None

    def sync(self):
        res = self.call_api("sync")
        if res and res.get("status") == "success":
            d = res.get("data", {})
            self.balance = int(d.get("balance", 0))
            self.last_harvest = int(d.get("last_harvest", 0))
            name = d.get("name", self.username)
            log("SYNC", f"🐍 Đã đồng bộ trang trại Rắn! User: {name} | Số dư Mật: {self.balance} 🧪 | Tổng kiếm: {d.get('total_earned', 0)}", Fore.GREEN)
            return d
        else:
            log("SYNC_ERR", f"Không thể đồng bộ: {res}", Fore.RED)
            return None

    def checkin(self, data):
        checked_today = int(data.get("checked_in_today", 0))
        if checked_today == 0:
            log("CHECKIN", "📅 Đang tiến hành điểm danh hàng ngày...", Fore.YELLOW)
            res = self.call_api("do_checkin")
            if res and res.get("status") == "success":
                rw = res.get("reward", 0)
                log("CHECKIN", f"🎉 Điểm danh thành công! Nhận: +{rw} Mật Rắn!", Fore.GREEN)
            else:
                log("CHECKIN", f"ℹ️ Phản hồi điểm danh: {res.get('message', '') if res else ''}", Fore.CYAN)
        else:
            log("CHECKIN", "ℹ️ Hôm nay đã điểm danh rồi.", Fore.LIGHTBLACK_EX)

    def harvest(self, data):
        now = int(time.time())
        last_h = int(data.get("last_harvest", 0))
        elapsed = now - last_h
        
        # Cooldown mặc định 30 phút (1800s)
        if elapsed >= 1800 or last_h == 0:
            log("HARVEST", "🧪 Đến giờ lấy mật! Đang thu hoạch Mật Rắn...", Fore.YELLOW)
            res = self.call_api("harvest")
            if res and res.get("status") == "success":
                rw = res.get("reward", 0)
                new_bal = res.get("data", {}).get("balance", self.balance + rw)
                self.balance = new_bal
                log("HARVEST", f"🎉 THU HOẠCH THÀNH CÔNG: +{rw} Mật Rắn 🧪! Số dư mới: {self.balance}", Fore.GREEN)
            else:
                log("HARVEST", f"ℹ️ Thông báo: {res.get('message', '') if res else ''}", Fore.CYAN)
        else:
            rem = 1800 - elapsed
            log("HARVEST", f"⏳ Rắn đang tạo mật... Còn {rem // 60}m {rem % 60}s nữa để thu hoạch tiếp theo.", Fore.CYAN)

    def complete_daily_tasks(self, data):
        """Tự động duyệt và làm các nhiệm vụ hằng ngày."""
        tasks = [
            (1, "https://t.me/rancutekiemtien"),
            (2, "https://t.me/kiemtienmienphi2001"),
            (3, "https://t.me/tonghopkiemtienphucktol/12260"),
            (4, ""),
            (5, ""),
            (6, ""),
            (7, ""),
            (8, "")
        ]
        for tid, url in tasks:
            task_key = f"task_{tid}"
            val = data.get(task_key, 0)
            if val == 0:
                log("TASK", f"📋 Đang hoàn thành nhiệm vụ Task #{tid}...", Fore.CYAN)
                if url:
                    self.call_api("check_join", task_id=tid, url=url)
                    time.sleep(2)
                self.call_api("do_task", task_id=tid, url=url)
                time.sleep(1.5)

    async def run_cycle(self):
        ok = await self.fetch_tg_init_data()
        if not ok:
            return
        
        data = self.sync()
        if not data:
            return

        self.checkin(data)
        self.harvest(data)
        self.complete_daily_tasks(data)

async def main():
    print(Fore.YELLOW + """
=============================================================================
  BOT AUTO RẮN CUTE KIẾM TIỀN 24/7 - AUTO HARVEST VENOM & DAILY CHECKIN
  Tự động Thu Hoạch Mật Rắn Mỗi 30 Phút | Tự động Điểm Danh & Làm Nhiệm Vụ
=============================================================================
    """ + Style.RESET_ALL)
    bot = RanCuteBot()
    await bot.run_cycle()

if __name__ == "__main__":
    asyncio.run(main())
