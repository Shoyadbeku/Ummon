"""Telegram bot: yuborilgan o'zbekcha matnni klonlangan ovozda voice qilib qaytaradi.

Ishga tushirish:
  export BOT_TOKEN=123:ABC...         # @BotFather bergan token
  export OVOZ_EGALAR=111111111,222    # ruxsat berilgan Telegram ID'lar
  ~/.ovoz-venv/bin/python ovoz-klon/bot.py

OVOZ_EGALAR bo'sh bo'lsa, bot hech kimga ovoz yaratmaydi, faqat yozgan
odamning ID'sini aytadi: o'z ID'ingizni shu yo'l bilan bilib oling.
"""
import os
import queue
import subprocess
import tempfile
import threading

import requests
import soundfile as sf

from klon import SR, oqit, yukla

TOKEN = os.environ["BOT_TOKEN"]
API = f"https://api.telegram.org/bot{TOKEN}"
EGALAR = {int(x) for x in os.environ.get("OVOZ_EGALAR", "").replace(" ", "").split(",") if x}
MAX_MATN = 1500

navbat = queue.Queue()


def tg(metod, **kw):
    r = requests.post(f"{API}/{metod}", timeout=70, **kw)
    r.raise_for_status()
    return r.json()["result"]


def yoz(chat, matn, javob=None):
    tg("sendMessage", data={"chat_id": chat, "text": matn, "reply_to_message_id": javob})


def ishchi():
    # Model bir marta yuklanadi; xabarlar navbat bilan bittadan o'qitiladi (CPU).
    m, prompt = yukla()
    print("model tayyor", flush=True)
    while True:
        chat, xabar_id, matn = navbat.get()
        try:
            tg("sendChatAction", data={"chat_id": chat, "action": "record_voice"})
            audio = oqit(m, prompt, matn, log=lambda s: print(chat, s, flush=True))
            with tempfile.TemporaryDirectory() as d:
                wav, ogg = os.path.join(d, "o.wav"), os.path.join(d, "o.ogg")
                sf.write(wav, audio, SR)
                # sendVoice faqat OGG/Opus'ni voice sifatida ko'rsatadi.
                subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", wav,
                                "-c:a", "libopus", "-b:a", "48k", ogg], check=True)
                with open(ogg, "rb") as f:
                    tg("sendVoice", data={"chat_id": chat, "reply_to_message_id": xabar_id},
                       files={"voice": f})
        except Exception as e:
            print("xato:", e, flush=True)
            yoz(chat, f"Xatolik: {e}", xabar_id)


def main():
    threading.Thread(target=ishchi, daemon=True).start()
    offset = None
    print("bot ishga tushdi", flush=True)
    while True:
        try:
            yangilar = tg("getUpdates", data={"timeout": 50, "offset": offset})
        except requests.RequestException as e:
            print("ulanish:", e, flush=True)
            continue
        for u in yangilar:
            offset = u["update_id"] + 1
            x = u.get("message")
            if not x:
                continue
            chat, kim, matn = x["chat"]["id"], x["from"]["id"], x.get("text", "")
            if kim not in EGALAR:
                yoz(chat, f"Ruxsat yo'q. Sizning ID: {kim}")
                continue
            if not matn or matn.startswith("/"):
                yoz(chat, "Matn yuboring, uni ovozingizda o'qib beraman.")
                continue
            if len(matn) > MAX_MATN:
                yoz(chat, f"Matn juda uzun ({len(matn)} belgi), {MAX_MATN} tagacha yuboring.", x["message_id"])
                continue
            navbat.put((chat, x["message_id"], matn))
            yoz(chat, f"Qabul qilindi, navbatda {navbat.qsize()}-o'rinda. "
                      "Har bir gap ~1-2 daqiqa oladi.", x["message_id"])


if __name__ == "__main__":
    main()
