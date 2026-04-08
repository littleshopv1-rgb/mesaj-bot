import os
import time
import requests
import socketio
import re
import json
from urllib.parse import quote

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
PHPSESSID = os.environ.get("PHPSESSID")

seen_message_ids = set()

def send_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
        requests.post(url, data=data, timeout=10)
        print("Telegram mesajı gönderildi.")
    except Exception as e:
        print(f"Telegram hatası: {e}")

def get_temp_token():
    try:
        headers = {
            "Cookie": f"PHPSESSID={PHPSESSID}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
        }
        r = requests.get("https://www.itemsatis.com/mesajlarim.html", headers=headers, timeout=15)
        match = re.search(r'var tempToken\s*=\s*"([^"]+)"', r.text)
        if match:
            token = match.group(1)
            print(f"Token alındı: {token[:30]}...")
            return token
        else:
            print("Token bulunamadı! Sayfa içeriği:")
            print(r.text[:500])
            return None
    except Exception as e:
        print(f"Token alma hatası: {e}")
        return None

def clean_html(text):
    if not text:
        return "..."
    return re.sub(r'<[^>]+>', '', text).strip()

def start_socket(temp_token):
    sio = socketio.Client(reconnection=False)

    @sio.event
    def connect():
        print("Bağlantı kuruldu!")
        sio.emit("getMessageList")

    @sio.event
    def disconnect():
        print("Bağlantı kesildi...")

    @sio.on("receiveMessageList")
    def on_receive_message_list(data):
        try:
            if not data or not isinstance(data, list):
                return
            for chat in data:
                chat_id = chat.get("chatID", "")
                message = chat.get("Message", "") or chat.get("message", "")
                sender = chat.get("senderName", "") or "Bilinmeyen"
                receiver_seen = chat.get("receiverSeen", True)
                datetime_str = chat.get("Datetime", "") or chat.get("datetime", "")
                msg_key = f"{chat_id}_{datetime_str}"
                if msg_key not in seen_message_ids and not receiver_seen:
                    seen_message_ids.add(msg_key)
                    clean_msg = clean_html(message)
                    text = (
                        f"💬 <b>Yeni Mesaj!</b>\n"
                        f"👤 Gönderen: <b>{sender}</b>\n"
                        f"📝 {clean_msg[:200]}"
                    )
                    send_telegram(text)
                    print(f"Bildirim gönderildi: {sender}")
        except Exception as e:
            print(f"Hata: {e}")

    @sio.on("*")
    def catch_all(event, data):
        skip = ["ping", "pong", "connect", "disconnect"]
        if event not in skip:
            print(f"EVENT: {event} | DATA: {str(data)[:300]}")

    token_json = json.dumps(temp_token)
    encoded_token = quote(token_json, safe='')
    connect_url = f"https://chat.itemsatis.com?userData={encoded_token}"

    print("Socket'e bağlanılıyor...")
    sio.connect(connect_url, transports=["websocket"], wait_timeout=15)
    sio.wait()

if __name__ == "__main__":
    print("Bot başlatılıyor...")
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID or not PHPSESSID:
        print("HATA: Environment variables eksik! (TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, PHPSESSID)")
    else:
        send_telegram("✅ <b>Mesaj botu başlatıldı!</b>")
        while True:
            try:
                print("Token alınıyor...")
                token = get_temp_token()
                if not token:
                    print("Token alınamadı, 30 saniye sonra tekrar deneniyor...")
                    time.sleep(30)
                    continue
                start_socket(token)
            except Exception as e:
                print(f"Bağlantı hatası: {e}")
            print("5 saniye sonra yeniden bağlanılıyor...")
            time.sleep(5)
