import requests
import time
import json
import os
from bs4 import BeautifulSoup

# --- AYARLAR ---
ITEMSATIS_USERNAME = os.environ.get("ITEMSATIS_USERNAME")
ITEMSATIS_PASSWORD = os.environ.get("ITEMSATIS_PASSWORD")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
CHECK_INTERVAL = 60  # Her 60 saniyede bir kontrol eder

# Daha önce görülen mesaj ID'lerini saklar
seen_messages = set()

def telegram_bildirim_gonder(mesaj):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mesaj,
        "parse_mode": "HTML"
    }
    try:
        requests.post(url, data=data)
        print("Telegram bildirimi gönderildi.")
    except Exception as e:
        print(f"Telegram hatası: {e}")

def itemsatis_giris_yap(session):
    login_url = "https://www.itemsatis.com/giris"
    payload = {
        "username": ITEMSATIS_USERNAME,
        "password": ITEMSATIS_PASSWORD,
    }
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://www.itemsatis.com/giris"
    }
    r = session.post(login_url, data=payload, headers=headers)
    if "hesabim" in r.url or r.status_code == 200:
        print("Giriş başarılı.")
        return True
    print("Giriş başarısız!")
    return False

def mesajlari_kontrol_et(session):
    global seen_messages
    mesaj_url = "https://www.itemsatis.com/mesajlar"
    headers = {"User-Agent": "Mozilla/5.0"}
    r = session.get(mesaj_url, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")

    # Mesaj listesini bul (itemsatis.com yapısına göre ayarlandı)
    mesaj_satirlari = soup.select(".message-item, .msg-row, .conversation-item")

    if not mesaj_satirlari:
        print("Mesaj öğesi bulunamadı, sayfa yapısı değişmiş olabilir.")
        return

    for satir in mesaj_satirlari:
        # Okunmamış mesajları tespit et
        okunmamis = satir.select_one(".unread, .badge, .new-message")
        mesaj_id = satir.get("data-id") or satir.get("id") or str(satir)[:100]

        if mesaj_id not in seen_messages:
            seen_messages.add(mesaj_id)

            gonderen = satir.select_one(".sender, .username, .from")
            gonderen_adi = gonderen.text.strip() if gonderen else "Bilinmiyor"

            on_izleme = satir.select_one(".preview, .message-preview, .last-message")
            mesaj_metni = on_izleme.text.strip() if on_izleme else "Mesaj içeriği yok"

            bildirim = (
                f"📩 <b>Yeni Mesaj!</b>\n"
                f"👤 Gönderen: {gonderen_adi}\n"
                f"💬 Mesaj: {mesaj_metni}\n"
                f"🔗 <a href='https://www.itemsatis.com/mesajlar'>Mesajları Görüntüle</a>"
            )
            telegram_bildirim_gonder(bildirim)

def main():
    session = requests.Session()
    print("Bot başlatılıyor...")
    telegram_bildirim_gonder("✅ Mesaj bildirim botu başlatıldı! Yeni mesajları takip ediyorum.")

    giris_basarili = itemsatis_giris_yap(session)
    if not giris_basarili:
        telegram_bildirim_gonder("❌ itemsatis.com'a giriş yapılamadı! Kullanıcı adı/şifreyi kontrol edin.")
        return

    while True:
        try:
            print("Mesajlar kontrol ediliyor...")
            mesajlari_kontrol_et(session)
        except Exception as e:
            print(f"Hata: {e}")
            # Oturum düşmüş olabilir, tekrar giriş yap
            itemsatis_giris_yap(session)
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
