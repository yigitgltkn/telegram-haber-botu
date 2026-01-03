import os
import requests
import datetime
from google import genai
from google.genai import types

# --- AYARLAR ---
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

# Saat ayarları (Veri güncelliğini kontrol etmek için)
tr_timezone = pytz.timezone('Europe/Istanbul')
simdi = datetime.datetime.now(tr_timezone)
bugun_tarih = simdi.strftime("%d %B %Y")
bugun_kisa = simdi.strftime("%Y-%m-%d")
saat = simdi.hour

def piyasa_analizi_yap():
    # --- SAFEBLADE STRATEJİSİ ---
    prompt = f"""
        GÖREV: SafeBlade stratejime uygun hisseleri bulmak için Google'da 'Derinlemesine Canlı Arama' yap.
        
        ÖNEMLİ KURAL: Asla kendi hafızandaki eski veriyi kullanma. Mutlaka "Technical Analysis {bugun_kisa}" veya "Live RSI levels today" sorgularını çalıştır.
        
    ARAMA FİLTRELERİ (Buna uymayanı getirme):
    1. 📈 ANA TREND (EMA 50): Fiyat kesinlikle 50 Günlük Hareketli Ortalamanın (EMA 50) ÜZERİNDE olmalı. (Trend Yukarı).
    2. 🧲 DÜZELTME (PULLBACK - EMA 20): Fiyat son 1-2 gün içinde kısa vadeli ortalamasına (EMA 20) geri çekilmiş veya temas etmiş olmalı. (Fiyatın EMA 20'den çok uzaklaştığı "uçmuş" hisseleri istemiyorum).
    3. 📊 MOMENTUM (RSI): RSI değeri 35 ile 65 arasında olmalı. (Ne aşırı satımda ölü, ne de aşırı alımda şişmiş olacak).
    4. ⚠️ HACİM: Düşüşler hacimsiz, yükselişler hacimli olmalı.
        
        ARAŞTIRMA ADIMLARI (Bunu uygula):
        1. Önce "Nasdaq 100 technical analysis {bugun_kisa}" araması yapıp genel trendi teyit et.
        2. Sonra "Best swing trade stocks pullback strategy {bugun_kisa}" veya "Stocks near EMA 20 support today" araması yap.
        3. Bulduğun hisselerin verilerini "Investing.com" veya "TradingView" kaynaklı güncel verilerle doğrula.
        
        RAPOR ÇIKTISI:
        - Eğer verisi bugüne ({bugun_tarih}) ait olmayan bir hisse bulursan listeye ekleme.
        - 3 adet aday hisse ve nedenleri (RSI ve EMA değerleriyle).
        """
    
    print("Gemini 3.0 Pro (Varsayılan Thinking: HIGH + Search) çalışıyor...")
    
    try:
        response = client.models.generate_content(
            model='gemini-3-pro-preview',
            contents=prompt,
            config=types.GenerateContentConfig(
                # thinking_config kısmını sildik, model zaten varsayılan olarak en yüksek seviyede düşünür.
                
                # Sadece Google Arama aracını bırakıyoruz:
                tools=[types.Tool(
                    google_search=types.GoogleSearch()
                )],
                response_mime_type="text/plain"
            )
        )
        return response.text
        
    except Exception as e:
        return f"❌ Hata: {str(e)}"

def telegrama_gonder(mesaj):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    # Mesaj çok uzunsa 4000 karakterde bölüyoruz
    limit = 4000
    parcalar = [mesaj[i:i+limit] for i in range(0, len(mesaj), limit)]

    for parca in parcalar:
        payload = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': f"🧠 **SAFEBLADE AI**\n📅 {bugun}\n\n{parca}",
        }
        requests.post(url, data=payload)

if __name__ == "__main__":
    rapor = piyasa_analizi_yap()
    if rapor:
        telegrama_gonder(rapor)
        print("Rapor gönderildi.")
    else:
        print("Rapor oluşturulamadı.")
