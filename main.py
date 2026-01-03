import os
import requests
import datetime
from google import genai
from google.genai import types

# --- AYARLAR ---
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

bugun = datetime.date.today().strftime("%d %B %Y")
client = genai.Client(api_key=GEMINI_API_KEY)

def piyasa_analizi_yap():
    # --- SAFEBLADE STRATEJİSİ ---
    prompt = f"""
    GÖREV: Sen benim 'Algoritmik Ön Tarama Asistanımsın'. Tarih: {bugun}.
    
    STRATEJİM (SafeBlade): Ben sadece "Yükseliş Trendindeki Düzeltmeleri" (Trend Pullback) satın alırım.
    Bana rastgele hisse önerme, sadece aşağıdaki TEKNİK KRİTERLERE uyan varlıkları Google'da tara ve bul.
    
    ARAMA FİLTRELERİ (Buna uymayanı getirme):
    1. 📈 ANA TREND (EMA 50): Fiyat kesinlikle 50 Günlük Hareketli Ortalamanın (EMA 50) ÜZERİNDE olmalı. (Trend Yukarı).
    2. 🧲 DÜZELTME (PULLBACK - EMA 20): Fiyat son 1-2 gün içinde kısa vadeli ortalamasına (EMA 20) geri çekilmiş veya temas etmiş olmalı. (Fiyatın EMA 20'den çok uzaklaştığı "uçmuş" hisseleri istemiyorum).
    3. 📊 MOMENTUM (RSI): RSI değeri 35 ile 65 arasında olmalı. (Ne aşırı satımda ölü, ne de aşırı alımda şişmiş olacak).
    4. ⚠️ HACİM: Düşüşler hacimsiz, yükselişler hacimli olmalı.
    
    İSTENEN RAPOR FORMATI:
    
    1. 🌍 PİYASA GENELİ & VIX
       - Endeksler (NASDAQ/SPX) EMA 50 üstünde mi? (Stratejim sadece piyasa iyiyken çalışır).
    
    2. 🎯 SAFEBLADE ADAY LİSTESİ (En az 3 Aday)
       - NASDAQ, Kripto veya Emtia piyasalarından yukarıdaki kriterlere en çok uyan 3 varlığı listele.
       - Format:
         * Varlık: [Kod]
         * Mevcut Durum: [Örn: EMA 50 üstünde, EMA 20'ye dokundu]
         * RSI Tahmini: [Örn: Nötr, 55 civarı]
         * Neden Uygun: [Haber/Temel neden]
    
    3. 🚫 UZAK DURULACAKLAR
       - Bugün çok popüler olsa bile "RSI değeri 70'in üzerine çıkmış" (aşırı şişmiş) 2 varlığı yaz ki yanlışlıkla girmeyeyim.
    
    Yanıtı Türkçe, kısa, öz ve tamamen teknik odaklı ver.
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
