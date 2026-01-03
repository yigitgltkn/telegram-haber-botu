import os
import google.generativeai as genai
import requests
import datetime

# --- AYARLAR ---
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

# Tarihi alalım (Analizin güncelliği için)
bugun = datetime.date.today().strftime("%d %B %Y")

genai.configure(api_key=GEMINI_API_KEY)

# --- MODEL SEÇİMİ: GEMINI 1.5 PRO ---
# Finansal analiz ve mantık yürütme için en güçlü model budur.
model = genai.GenerativeModel(
    'gemini-3.0-pro', 
    tools='google_search_retrieval'
)

def piyasa_analizi_yap():
    # Swing Trader Prompt Mühendisliği
    prompt = f"""
    Sen, Wall Street tecrübesi olan kıdemli bir Swing Trader ve Teknik Analistsin.
    Bugünün tarihi: {bugun}.
    
    Görevin: İnternetteki güncel finansal verileri, teknik analiz raporlarını ve haber akışını tarayarak bana (bir Swing Trader'a) özel bir rapor hazırlamak.
    
    Lütfen şu adımları izleyerek derinlemesine bir araştırma yap (Google Search kullan):
    
    1. **GENEL PİYASA YÖNÜ (NASDAQ & ALTIN):**
       - NASDAQ 100 ve ONS ALTIN (XAU/USD) için son 24 saatteki en kritik haberler neler?
       - Teknik görünüm ne diyor? (RSI, MACD ve EMA 50/200 ortalamalarının üzerinde miyiz, altında mıyız? Trend yukarı mı aşağı mı?)
       - Korku ve Açgözlülük endeksi ne durumda?

    2. **SWING TRADE İÇİN TOP 5 NASDAQ HİSSESİ:**
       - Şu an momentumu yüksek, teknik olarak "AL" sinyali veren veya dipten dönüş yapan 5 NASDAQ hissesini belirle.
       - Neden bunları seçtiğini 1 cümleyle açıkla (Örn: "RSI aşırı satımdan dönüyor" veya "Hacimli kırılım var").

    3. **STRATEJİ VE SONUÇ:**
       - Bugün nakitte mi kalmalıyım, mal mı toplamalıyım yoksa kar satışı mı yapmalıyım?
       - Net bir strateji önerisi ver.

    **Çıktı Formatı:**
    Yanıtı Telegram mesajı olarak okunacak şekilde, bol emojili, maddeler halinde ve Türkçe olarak ver. Finansal terimleri (Support, Resistance, EMA) kullanabilirsin.
    """
    
    try:
        print("Piyasa taranıyor ve teknik analizler inceleniyor...")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Analiz hatası: {str(e)}"

def telegrama_gonder(mesaj):
    # Mesaj çok uzunsa Telegram hata verebilir, 4096 karaktere bölelim
    max_uzunluk = 4000
    parcalar = [mesaj[i:i+max_uzunluk] for i in range(0, len(mesaj), max_uzunluk)]
    
    for parca in parcalar:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': parca, # Markdown hatası almamak için düz text veya HTML denenebilir, şimdilik text.
            'parse_mode': '' # Markdown bazen * karakterlerinde hata verir, boş bıraktık.
        }
        requests.post(url, data=payload)

if __name__ == "__main__":
    analiz = piyasa_analizi_yap()
    if analiz:
        baslik = f"📈 **GÜNLÜK SWING TRADE RAPORU ({bugun})**\n\n"
        telegrama_gonder(baslik + analiz)
        print("Rapor gönderildi.")
    else:
        print("İçerik oluşturulamadı.")
