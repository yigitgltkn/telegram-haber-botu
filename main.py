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
    Sen kıdemli bir Swing Trader ve Teknik Analistsin. Tarih: {bugun}.
    
    Görevin: Google Arama özelliğini kullanarak güncel piyasayı tara.
    1. NASDAQ ve ALTIN (XAU/USD) teknik görünümü ne? (EMA, RSI durumu)
    2. Swing Trade için uygun potansiyeli olan 3 hisse veya emtia bul.
    3. Genel strateji: Alıcı mı olmalıyım, satıcı mı?
    
    Yanıtı Türkçe, emojili ve Telegram'da okunacak şekilde maddeler halinde ver.
    """
    
    try:
        print("Yeni nesil Gemini 1.5 Pro piyasayı tarıyor...")
        
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
