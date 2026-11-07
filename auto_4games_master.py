#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
  MASTER BOT AUTO 4 GAMES AIRDROP & MINING ($TON / $GRAM / MẬT RẮN) 24/7
  Danh sách 4 Game tích hợp:
    1. Gramstone (@gramstone_bot) - Chuẩn cơ chế mới 100% (x-gs-fp & deviceInfo)
    2. HashLane (@hashlane_bot) - Tự động thu hoạch 100 điểm & khởi động đào
    3. REDRIG (@redrig_bot) - Tự động thu hoạch két sắt TON & nâng cấp GPU
    4. Rắn Cute Kiếm Tiền (@rancutekiemtien_bot) - Thu hoạch Mật Rắn & làm nhiệm vụ
=============================================================================
"""

import os
import sys
import time
import asyncio
from colorama import init, Fore, Style

# Import 4 bot engines
from auto_gramstone import GramstoneBot
from auto_hashlane import HashLaneBot
from auto_redrig import RedRigBot
from auto_rancutekiemtien import RanCuteBot

init(autoreset=True)

def print_banner():
    print(Fore.YELLOW + """
=============================================================================
  🔥 HỆ THỐNG AUTO 4 GAMES AIRDROP & MINING 24/7 (CHUẨN CHỈ MOONPOOL ENGINE) 🔥
  1. 💎 Gramstone: Cơ chế Moonpool | Thẻ Mỏ Safir Tier 3 (+4 GH/s) | Vault 100% | Tap 240
  2. ⛏️ HashLane: Thu hoạch 100 điểm kho đầy | Khởi động mỏ đào mới | Điểm danh
  3. 🔌 REDRIG: Cơ chế Moonpool | Cày Card GPU Tier 3 (+12⚡ Power) | Thu hoạch Két Safe
  4. 🐍 Rắn Cute: Thu hoạch Mật Rắn định kỳ | Điểm danh | Làm nhiệm vụ
=============================================================================
    """ + Style.RESET_ALL)

def log_master(tag, msg, color=Fore.CYAN):
    t_str = time.strftime('%H:%M:%S')
    print(f"\n{Fore.LIGHTBLACK_EX}[{t_str}]{Style.RESET_ALL} {Fore.WHITE}=== {color}[{tag.upper()}]{Style.RESET_ALL} {msg} ===")

async def run_all_4_games(session_path=None, string_session=None):
    print_banner()

    # GAME 1: GRAMSTONE (CƠ CHẾ MỚI)
    log_master("GAME 1/4: GRAMSTONE", "Bắt đầu chu trình Gramstone...", Fore.YELLOW)
    try:
        gram_bot = GramstoneBot(session_path=session_path, string_session=string_session)
        await gram_bot.run_cycle()
    except Exception as e:
        print(f"{Fore.RED}[GRAMSTONE_ERR] Lỗi: {e}{Style.RESET_ALL}")

    await asyncio.sleep(3)

    # GAME 2: HASHLANE
    log_master("GAME 2/4: HASHLANE", "Bắt đầu chu trình HashLane...", Fore.MAGENTA)
    try:
        hash_bot = HashLaneBot(session_path=session_path, string_session=string_session)
        await hash_bot.run_cycle()
    except Exception as e:
        print(f"{Fore.RED}[HASHLANE_ERR] Lỗi: {e}{Style.RESET_ALL}")

    await asyncio.sleep(3)

    # GAME 3: REDRIG
    log_master("GAME 3/4: REDRIG", "Bắt đầu chu trình REDRIG...", Fore.BLUE)
    try:
        redrig_bot = RedRigBot(session_path=session_path, string_session=string_session)
        await redrig_bot.run_cycle()
    except Exception as e:
        print(f"{Fore.RED}[REDRIG_ERR] Lỗi: {e}{Style.RESET_ALL}")

    await asyncio.sleep(3)

    # GAME 4: RẮN CUTE KIẾM TIỀN
    log_master("GAME 4/4: RẮN CUTE", "Bắt đầu chu trình Rắn Cute Kiếm Tiền...", Fore.GREEN)
    try:
        rancute_bot = RanCuteBot(session_path=session_path, string_session=string_session)
        await rancute_bot.run_cycle()
    except Exception as e:
        print(f"{Fore.RED}[RANCUTE_ERR] Lỗi: {e}{Style.RESET_ALL}")

    print(Fore.GREEN + f"\n{'='*75}\n  🎉 ĐÃ HOÀN THÀNH TOÀN BỘ 1 CHU KỲ TỰ ĐỘNG CHO CẢ 4 GAMES!\n{'='*75}\n" + Style.RESET_ALL)

async def loop_247(interval_minutes=15):
    while True:
        try:
            await run_all_4_games()
            sleep_sec = interval_minutes * 60
            print(f"{Fore.YELLOW}⏳ Nghỉ {interval_minutes} phút trước chu kỳ kiểm tra và thu hoạch tiếp theo...{Style.RESET_ALL}")
            await asyncio.sleep(sleep_sec)
        except KeyboardInterrupt:
            print(f"{Fore.YELLOW}Người dùng dừng chương trình.{Style.RESET_ALL}")
            break
        except Exception as e:
            print(f"{Fore.RED}Lỗi vòng lặp Master: {e}{Style.RESET_ALL}")
            await asyncio.sleep(60)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--loop":
        mins = int(sys.argv[2]) if len(sys.argv) > 2 else 15
        asyncio.run(loop_247(interval_minutes=mins))
    else:
        asyncio.run(run_all_4_games())
