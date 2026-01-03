import os
import google.generativeai as genai
import requests
import time

# Ortam değişkenlerinden şifreleri alıyoruz
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

genai.configure(api_key=GEMINI_API_KEY)

# Model ismini guncelledik
# --- GEMINI 1.5 PRO (Kararlı ve Çok Zeki) ---
model = genai.GenerativeModel(
    'gemini-1.5-pro', 
    tools='google_search_retrieval'
)

def arastirma_yap():
    konu = "Nasdaq'da Yapay zeka ve teknoloji dünyasında son 24 saatteki en önemli gelişmeleri ver. Hangi hisseler swing trade icin uygun"
    try:
        # Grounding (Google Arama) ile prompt
        prompt = f"Şu konuda internette güncel bir arama yap ve önemli başlıkları özetle: {konu}. Yanıtı Türkçe, emoji kullanarak ve maddeler halinde ver. Kaynak linkleri ekleme."
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Hata oluştu: {str(e)}"

def telegrama_gonder(mesaj):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': f"🤖 **Günlük Teknoloji Raporu**\n\n{mesaj}",
        'parse_mode': 'Markdown'
    }
    requests.post(url, data=payload)

if __name__ == "__main__":
    print("Bot çalışıyor...")
    icerik = arastirma_yap()
    if icerik:
        telegrama_gonder(icerik)
        print("Mesaj gönderildi.")
    else:
        print("İçerik üretilemedi.")
