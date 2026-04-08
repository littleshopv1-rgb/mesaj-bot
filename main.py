import os
import time
import requests
import socketio

# Ayarlar
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
TEMP_TOKEN = os.environ.get("TEMP_TOKEN")
SOCKET_URL = "https://chat.itemsatis.com"

def send_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
        requests.post(url, data=data, timeout=10)
        print("Telegram mesajı gönderildi.")
    except Exception as e:
        print(f"Telegram hatası: {e}")

def start_socket():
    sio = socketio.Client(reconnection=True, reconnection_attempts=0, reconnection_delay=5)

    @sio.event
    def connect():
        print("Socket.io bağlantısı kuruldu!")
        send_telegram("✅ <b>Mesaj botu başlatıldı!</b>\nYeni mesajları takip ediyorum.")
        # Kimlik doğrulama
        sio.emit("authenticate", {"token": TEMP_TOKEN})

    @sio.event
    def disconnect():
        print("Bağlantı kesildi, yeniden bağlanılıyor...")

    @sio.event
    def connect_error(data):
        print(f"Bağlantı hatası: {data}")

    # Yeni mesaj geldiğinde
    @sio.on("newMessage")
    def on_new_message(data):
        try:
            print(f"Yeni mesaj alındı: {data}")
            sender = data.get("senderName") or data.get("sender") or "Bilinmeyen"
            message = data.get("message") or data.get("text") or data.get("content") or "..."
            
            text = (
                f"💬 <b>Yeni Mesaj!</b>\n"
                f"👤 Gönderen: <b>{sender}</b>\n"
                f"📝 Mesaj: {message}"
            )
            send_telegram(text)
        except Exception as e:
            print(f"Mesaj işleme hatası: {e}")
            send_telegram(f"💬 Yeni mesaj geldi! (detay alınamadı)\nVeri: {str(data)[:200]}")

    # Diğer olası event isimleri
    @sio.on("message")
    def on_message(data):
        on_new_message(data)

    @sio.on("chat")
    def on_chat(data):
        on_new_message(data)

    @sio.on("newChat")
    def on_new_chat(data):
        on_new_message(data)

    @sio.on("*")
    def catch_all(event, data):
        # Tüm eventleri logla - hangi event isminin geldiğini görmek için
        if event not in ["ping", "pong", "connect", "disconnect"]:
            print(f"Event: {event} | Data: {str(data)[:300]}")

    while True:
        try:
            print(f"Socket.io sunucusuna bağlanılıyor: {SOCKET_URL}")
            sio.connect(
                SOCKET_URL,
                headers={"Authorization": f"Bearer {TEMP_TOKEN}"},
                transports=["websocket"],
                wait_timeout=10
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
        print(f"TELEGRAM_TOKEN: {'✓' if TELEGRAM_TOKEN else '✗'}")
        print(f"TELEGRAM_CHAT_ID: {'✓' if TELEGRAM_CHAT_ID else '✗'}")
        print(f"TEMP_TOKEN: {'✓' if TEMP_TOKEN else '✗'}")
    else:
        start_socket()
