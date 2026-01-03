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
    
   try:
        # --- GÖREVİ BAŞLAT (Asenkron) ---
        interaction = client.interactions.create(
            input=prompt,
            agent='deep-research-pro-preview-12-2025', # En güncel ajan
            background=True
        )
        
        print(f"Araştırma Kimliği: {interaction.id}")
        
        # --- SONUÇ BEKLEME DÖNGÜSÜ ---
        # Ajan araştırma yaparken biz burada bekliyoruz
        while True:
            # Durumu kontrol et
            check_interaction = client.interactions.get(name=interaction.name)
            
            if check_interaction.status == "completed":
                print("✅ Araştırma başarıyla tamamlandı!")
                # En son çıktıyı alıyoruz
                return check_interaction.outputs[-1].text
                
            elif check_interaction.status == "failed":
                return f"❌ Araştırma hatası oluştu: {check_interaction.error}"
            
            else:
                print("⏳ Ajan çalışıyor... (Haberleri ve verileri okuyor...)")
                time.sleep(15) # 15 saniyede bir kontrol et
                
    except Exception as e:
        return f"Sistem hatası: {str(e)}"

def telegrama_gonder(mesaj):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    # Mesaj çok uzunsa 4000 karakterde bölüyoruz
    limit = 4000
    parcalar = [mesaj[i:i+limit] for i in range(0, len(mesaj), limit)]

    for parca in parcalar:
        payload = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': f"🚀 **DERİN SWING ANALİZİ**\n📅 {bugun}\n\n{parca}",
            # Markdown kapalı çünkü finansal semboller hata verebiliyor
        }
        requests.post(url, data=payload)
        time.sleep(1) # Mesajlar arası bekleme

if __name__ == "__main__":
    rapor = piyasa_analizi_yap()
    if rapor:
        telegrama_gonder(rapor)
        print("Rapor gönderildi.")
    else:
        print("Rapor oluşturulamadı.")
