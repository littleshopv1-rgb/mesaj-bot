import requests
import time
import os
from bs4 import BeautifulSoup

# --- AYARLAR ---
PHPSESSID = os.environ.get("PHPSESSID")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
CHECK_INTERVAL = 60  # Her 60 saniyede bir kontrol eder

seen_messages = set()

def telegram_bildirim_gonder(mesaj):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mesaj,
        "parse_mode": "HTML"
    }
    try:
        r = requests.post(url, data=data)
        print("Telegram bildirimi gönderildi.")
    except Exception as e:
        print(f"Telegram hatası: {e}")

def mesajlari_kontrol_et():
    global seen_messages
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Cookie": f"PHPSESSID={PHPSESSID}"
    }
    try:
        r = requests.get("https://www.itemsatis.com/mesajlar", headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")

        if "giris" in r.url or "login" in r.url:
            print("Oturum süresi dolmuş!")
            telegram_bildirim_gonder("⚠️ itemsatis.com oturum süresi doldu! Cookie'yi yenilemeniz gerekiyor.")
            return

        mesaj_satirlari = soup.select(".conversation-item, .message-row, .msg-item, .chat-item, li.media")

        if not mesaj_satirlari:
            mesaj_satirlari = soup.select("li, .list-group-item")

        print(f"{len(mesaj_satirlari)} mesaj öğesi bulundu.")

        for satir in mesaj_satirlari:
            mesaj_id = satir.get("data-id") or satir.get("id") or str(hash(str(satir)))

            if mesaj_id not in seen_messages:
                seen_messages.add(mesaj_id)

                gonderen = satir.select_one(".username, .name, strong, b, .sender")
                gonderen_adi = gonderen.text.strip() if gonderen else "Bilinmiyor"

                on_izleme = satir.select_one(".preview, .message-preview, p, .last-msg, small")
                mesaj_metni = on_izleme.text.strip()[:100] if on_izleme else "Mesaj içeriği yok"

                if gonderen_adi and gonderen_adi != "Bilinmiyor":
                    bildirim = (
                        f"📩 <b>Yeni Mesaj!</b>\n"
                        f"👤 Gönderen: {gonderen_adi}\n"
                        f"💬 {mesaj_metni}\n"
                        f"🔗 <a href='https://www.itemsatis.com/mesajlar'>Mesajları Görüntüle</a>"
                    )
                    telegram_bildirim_gonder(bildirim)

    except Exception as e:
        print(f"Hata: {e}")

def main():
    print("Bot başlatılıyor...")
    telegram_bildirim_gonder("✅ Mesaj bildirim botu başlatıldı! Yeni mesajları takip ediyorum.")

    print("Mevcut mesajlar yükleniyor...")
    mesajlari_kontrol_et()
    print("Hazır! Yeni mesajlar bekleniyor...")

    while True:
        time.sleep(CHECK_INTERVAL)
        print("Mesajlar kontrol ediliyor...")
        mesajlari_kontrol_et()

if __name__ == "__main__":
    main()
