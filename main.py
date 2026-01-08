import os
import requests
import datetime
import pytz
import yfinance as yf
import pandas as pd
import ta
from google import genai
from google.genai import types

# --- AYARLAR ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# SafeBlade Takip Listesi
HISSE_LISTESI = [
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "AMD", 
    "NFLX", "INTC", "CSCO", "PEP", "AVGO", "TXN", "QCOM", "ADBE", 
    "PYPL", "AMAT", "SBUX", "MDLZ", "MRNA", "BKNG", "ADP", "GILD",
    "COST", "TMUS", "CMCSA", "AZPN", "ZS", "CRWD", "PANW", "FTNT"
]

client = genai.Client(api_key=GEMINI_API_KEY)

def telegrama_gonder(mesaj):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram ayarları eksik.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    limit = 4000
    parcalar = [mesaj[i:i+limit] for i in range(0, len(mesaj), limit)]
    for parca in parcalar:
        payload = {'chat_id': TELEGRAM_CHAT_ID, 'text': parca, 'parse_mode': 'Markdown'}
        requests.post(url, data=payload)

def teknik_tarama():
    print("\n" + "="*50)
    print("🔍 DETAYLI VERİ DÖKÜMÜ (TEYİT EKRANI)")
    print("="*50)
    print(f"{'HİSSE':<6} | {'TARİH':<10} | {'FİYAT':<8} | {'EMA20':<8} | {'EMA50':<8} | {'RSI':<6} | DURUM")
    print("-" * 85)
    
    adaylar = []
    
    for symbol in HISSE_LISTESI:
        try:
            # Veri çekme (Son 6 ay)
            df = yf.download(symbol, period="6mo", interval="1d", progress=False)
            if len(df) < 50: continue
            
            # Multi-index düzeltmesi
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            # --- HESAPLAMALAR ---
            df['EMA_50'] = ta.trend.ema_indicator(close=df['Close'], window=50)
            df['EMA_20'] = ta.trend.ema_indicator(close=df['Close'], window=20)
            df['RSI'] = ta.momentum.rsi(close=df['Close'], window=14)

            # Son satırı al
            son = df.iloc[-1]
            
            # --- VERİ TEYİDİ İÇİN TARİH ALMA ---
            # Pandas timestamp'i string'e çeviriyoruz
            veri_tarihi = son.name.strftime('%Y-%m-%d')
            
            fiyat = float(son['Close'])
            ema50 = float(son['EMA_50'])
            ema20 = float(son['EMA_20'])
            rsi = float(son['RSI'])

            # STRATEJİ KONTROLÜ
            trend_yukari = fiyat > ema50
            pullback = (ema20 * 0.97) <= fiyat <= (ema20 * 1.03)
            rsi_uygun = 35 < rsi < 65
            
            durum_mesaji = "❌"
            if trend_yukari and pullback and rsi_uygun:
                durum_mesaji = "✅ Aday"
                bilgi = f"🔹 {symbol} ({veri_tarihi}) | Fiyat: {fiyat:.2f} | EMA20: {ema20:.2f}"
                adaylar.append(bilgi)
            
            # --- LOG EKRANINA BAS (BURASI SENİN İÇİN) ---
            print(f"{symbol:<6} | {veri_tarihi:<10} | {fiyat:<8.2f} | {ema20:<8.2f} | {ema50:<8.2f} | {rsi:<6.1f} | {durum_mesaji}")

        except Exception as e:
            print(f"{symbol:<6} | HATA: {str(e)}")
            continue
            
    print("="*50 + "\n")
    return adaylar

def gemini_analizi(adaylar):
    if not adaylar:
        return "📉 Bugün SafeBlade stratejisine uyan hisse çıkmadı. Nakitte beklemeye devam."
    
    hisseler_str = "\n".join(adaylar)
    tarih = datetime.datetime.now(pytz.timezone('Europe/Istanbul')).strftime("%d %B %Y")
    
    prompt = f"""
    TARİH: {tarih}
    GÖREV: Aşağıdaki hisseler teknik olarak ALIM bölgesinde.
    HİSSELER:
    {hisseler_str}
    
    YAPMAN GEREKEN:
    Google Aramayı kullanarak:
    1. Kötü haber var mı?
    2. Bilanço tarihi yakın mı?
    
    ÇIKTI FORMATI:
    🦁 **SAFEBLADE RAPOR**
    (Her hisse için):
    ✅ **Hisse Kodu**
    * 📊 **Durum:** Teknik onaylı.
    * 📰 **Haber:** (Özet)
    * 🎯 **Karar:** "ALINABİLİR" veya "BEKLE"
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-3-pro-preview',
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
                response_mime_type="text/plain"
            )
        )
        return response.text
    except Exception as e:
        return f"AI Hatası: {e}"

if __name__ == "__main__":
    bulunanlar = teknik_tarama()
    # Eğer aday varsa Gemini'ye gönder, yoksa boşuna AI kotası harcama
    if bulunanlar:
        rapor = gemini_analizi(bulunanlar)
        telegrama_gonder(rapor)
    else:
        print("Hiçbir hisse kriterlere uymadı.")
