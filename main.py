import requests
import time
import os
from bs4 import BeautifulSoup

PHPSESSID = os.environ.get("PHPSESSID")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
CHECK_INTERVAL = 60

seen_ids = set()

def telegram_bildirim_gonder(mesaj):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mesaj,
        "parse_mode": "HTML"
    }
    try:
        requests.post(url, data=data, timeout=10)
        print("Telegram bildirimi gönderildi.")
    except Exception as e:
        print(f"Telegram hatası: {e}")

def mesajlari_kontrol_et(ilk_yukleme=False):
    global seen_ids
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Cookie": f"PHPSESSID={PHPSESSID}"
    }
    try:
        r = requests.get("https://www.itemsatis.com/mesajlar", headers=headers, timeout=15)
        
        if "giris" in r.url or "login" in r.url:
            print("Oturum süresi dolmuş!")
            telegram_bildirim_gonder("⚠️ itemsatis.com oturum süresi doldu! Cookie'yi yenilemeniz gerekiyor.")
            return

        soup = BeautifulSoup(r.text, "html.parser")
        
        # data-id özelliği olan tüm li elementlerini bul
        konusmalar = soup.find_all("li", attrs={"data-id": True})
        print(f"{len(konusmalar)} konuşma bulundu.")

        for konusma in konusmalar:
            data_id = konusma.get("data-id")
            username = konusma.get("data-username", "Bilinmiyor")
            classes = konusma.get("class", [])
            
            # İlk yüklemede sadece ID'leri kaydet, bildirim gönderme
            if ilk_yukleme:
                seen_ids.add(data_id)
                continue

            # Yeni mesaj mı?
            if data_id not in seen_ids:
                seen_ids.add(data_id)
                bildirim = (
                    f"📩 <b>Yeni Mesaj!</b>\n"
                    f"👤 Gönderen: {username}\n"
                    f"🔗 <a href='https://www.itemsatis.com/mesajlar'>Mesajları Görüntüle</a>"
                )
                telegram_bildirim_gonder(bildirim)
                print(f"Yeni mesaj: {username}")
            
            # Okunmamış mesaj var mı? (notSeenClass)
            elif "notSeenClass" in classes and data_id not in seen_ids:
                bildirim = (
                    f"📩 <b>Okunmamış Mesaj!</b>\n"
                    f"👤 Gönderen: {username}\n"
                    f"🔗 <a href='https://www.itemsatis.com/mesajlar'>Mesajları Görüntüle</a>"
                )
                telegram_bildirim_gonder(bildirim)

    except Exception as e:
        print(f"Hata: {e}")

def main():
    print("Bot başlatılıyor...")
    telegram_bildirim_gonder("✅ Mesaj bildirim botu başlatıldı! Yeni mesajları takip ediyorum.")

    print("Mevcut mesajlar yükleniyor...")
    mesajlari_kontrol_et(ilk_yukleme=True)
    print(f"Hazır! {len(seen_ids)} mevcut konuşma kaydedildi. Yeni mesajlar bekleniyor...")

    while True:
        time.sleep(CHECK_INTERVAL)
        print("Mesajlar kontrol ediliyor...")
        mesajlari_kontrol_et(ilk_yukleme=False)

if __name__ == "__main__":
    main()
