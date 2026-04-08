import os
import time
import requests
import socketio
import re
from urllib.parse import quote

# Ayarlar
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
TEMP_TOKEN = os.environ.get("TEMP_TOKEN")
SOCKET_URL = "https://chat.itemsatis.com"

seen_message_ids = set()

def send_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
        requests.post(url, data=data, timeout=10)
        print("Telegram mesajı gönderildi.")
    except Exception as e:
        print(f"Telegram hatası: {e}")

def clean_html(text):
    if not text:
        return "..."
    return re.sub(r'<[^>]+>', '', text).strip()

def start_socket():
    sio = socketio.Client(reconnection=True, reconnection_attempts=0, reconnection_delay=5)

    @sio.event
    def connect():
        print("Socket.io bağlantısı kuruldu!")
        send_telegram("✅ <b>Mesaj botu başlatıldı!</b>\nYeni mesajları takip ediyorum.")
        sio.emit("getMessageList")

    @sio.event
    def disconnect():
        print("Bağlantı kesildi, yeniden bağlanılıyor...")

    @sio.on("receiveMessageList")
    def on_receive_message_list(data):
        try:
            print(f"receiveMessageList: {str(data)[:500]}")
            if not data or not isinstance(data, list):
                return

            for chat in data:
                chat_id = chat.get("chatID", "")
                message = chat.get("Message", "") or chat.get("message", "")
                sender = chat.get("senderName", "") or chat.get("receiverName", "") or "Bilinmeyen"
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
                    print(f"Bildirim: {sender} - {clean_msg[:50]}")
        except Exception as e:
            print(f"receiveMessageList hatası: {e}")

    @sio.on("*")
    def catch_all(event, data):
        skip = ["ping", "pong", "connect", "disconnect"]
        if event not in skip:
            print(f"EVENT: {event} | DATA: {str(data)[:400]}")

    while True:
        try:
            # userData'yı JSON string olarak encode et ve query param olarak gönder
            encoded_token = quote(f'"{TEMP_TOKEN}"')
            connect_url = f"{SOCKET_URL}?userData={encoded_token}"
            
            print(f"Bağlanılıyor: {SOCKET_URL}")
            sio.connect(
                connect_url,
                transports=["websocket"],
                wait_timeout=15
            )
            sio.wait()
        except Exception as e:
            print(f"Bağlantı hatası: {e}")
            print("5 saniye sonra tekrar deneniyor...")
            time.sleep(5)

if __name__ == "__main__":
    print("Bot başlatılıyor...")
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID or not TEMP_TOKEN:
        print("HATA: Gerekli environment variables eksik!")
    else:
        start_socket()
