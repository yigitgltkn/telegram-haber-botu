import os
import requests
import datetime
from google import genai
from google.genai import types

# --- AYARLAR ---
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

# Tarih (Analiz güncelliği için)
bugun = datetime.date.today().strftime("%d %B %Y")

# --- YENİ NESİL CLIENT TANIMLAMASI ---
client = genai.Client(api_key=GEMINI_API_KEY)

def piyasa_analizi_yap():
    prompt = f"""
    GÖREV: Sen, 20 yıllık deneyime sahip, teknik analiz ve piyasa psikolojisi uzmanı kıdemli bir 'Swing Trader'sın.
    Tarih: {bugun}.
    
    AMAÇ: Google Arama özelliğini kullanarak güncel verileri tara ve bana net, kararsızlık içermeyen, işleme girilebilir bir ticaret planı hazırla.
    
    ANALİZ KURALLARI:
    - VADE: Analizlerini 'Günlük (D1)' ve '4 Saatlik (H4)' grafiklerin trendine göre yap.
    - İNDİKATÖRLER: RSI (Uyumsuzluk var mı?), MACD (Kesişim var mı?), EMA (20, 50 ve 200 günlük ortalamalara göre fiyat nerede?).
    
    RAPOR FORMATI (Aynen bu başlıkları kullan):
    
    1. 🌍 PİYASA MODU & GENEL BAKIŞ
       - Piyasa şu an "Risk İştahı Açık" mı yoksa "Güvenli Liman (Risk Off)" modunda mı?
       - Bugün takip edilmesi gereken kritik ekonomik veri var mı? (Fed konuşması, TÜFE, İşsizlik vb.)
    
    2. 📉 ENDEKS VE EMTIA ANALİZİ (NASDAQ & ALTIN)
       - NASDAQ 100: Trend yönü ne? Kritik Destek ve Direnç seviyeleri rakamsal olarak neresi? (Örn: 18.500 altı stop).
       - ONS ALTIN (XAU/USD): Düzeltme mi yapıyor yoksa yükseliş trendinde mi? Alım bölgesinde miyiz?
    
    3. 🎯 GÜNÜN FIRSATLARI (TOP 3 SWING TRADE)
       - Hacim artışı olan, teknik kırılım yapan veya destekte olan 3 adet hisse (ABD Borsaları) veya Kripto/Emtia bul.
       - Her biri için şu formatı kullan:
         * Varlık: [Hisse Kodu]
         * Yön: [AL / SAT]
         * Neden: [Teknik gerekçe, örn: "RSI Pozitif Uyumsuzluk + 50 EMA desteği"]
         * Giriş Bölgesi: [Fiyat Aralığı]
         * Hedef (TP): [Fiyat]
         * Zarar Kes (SL): [Fiyat]
    
    4. 🧠 STRATEJİ VE SONUÇ
       - Nakitte mi beklemeliyim (% kaç?), yoksa oyuna girmeli miyim?
       - Tek cümlelik günün mottosu.
    
    Yanıtı Türkçe ver. Finansal terimleri (Bullish, Bearish, Breakout) parantez içinde Türkçe açıklamasıyla kullanabilirsin. Cok fazla emoji kullanma okunabilirliği bozma.
    """
    
    try:
        print("Yeni nesil Gemini 3.0 Pro piyasayı tarıyor...")
        
        response = client.models.generate_content(
            model='gemini-3-pro-preview', # Şu an erişebileceğin en güçlü model
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(
                    google_search=types.GoogleSearch() # Google Arama Aracı
                )]
            )
        )
        
        # Yanıtın içinden metni alıyoruz
        return response.text
        
    except Exception as e:
        return f"Analiz hatası: {str(e)}"

def telegrama_gonder(mesaj):
    # Mesajı Telegram'a gönder
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    # Çok uzun mesajları bölmek gerekebilir ama şimdilik tek parça deneyelim
    if len(mesaj) > 4000:
        mesaj = mesaj[:4000] + "...(devamı kesildi)"

    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': f"🚀 **SWING TRADE RAPORU**\n📅 {bugun}\n\n{mesaj}",
        # Markdown kullanmıyoruz çünkü finansal semboller (*, _) bazen hata verdiriyor
    }
    requests.post(url, data=payload)

if __name__ == "__main__":
    rapor = piyasa_analizi_yap()
    if rapor:
        telegrama_gonder(rapor)
        print("Rapor başarıyla gönderildi.")
    else:
        print("Rapor oluşturulamadı.")
