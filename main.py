import os
import requests
import datetime
import pytz
import yfinance as yf
import pandas_ta as ta
from google import genai
from google.genai import types

# --- AYARLAR ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# SafeBlade Stratejisi için Seçilmiş Nasdaq Hisseleri
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
    print("🔍 Matematiksel tarama başlıyor...")
    adaylar = []
    
    for symbol in HISSE_LISTESI:
        try:
            # Son 6 ayın verisini çek
            df = yf.download(symbol, period="6mo", interval="1d", progress=False)
            if len(df) < 50: continue

            # İndikatörler
            df['EMA_50'] = ta.ema(df['Close'], length=50)
            df['EMA_20'] = ta.ema(df['Close'], length=20)
            df['RSI'] = ta.rsi(df['Close'], length=14)

            son = df.iloc[-1]
            fiyat = float(son['Close'])
            ema50 = float(son['EMA_50'])
            ema20 = float(son['EMA_20'])
            rsi = float(son['RSI'])

            # STRATEJİ: SafeBlade
            # 1. Trend Yukarı (Fiyat > EMA50)
            # 2. Düzeltme (Fiyat EMA20'ye yakın - %3 tolerans)
            # 3. Güç (RSI 35 ile 65 arası)
            
            if (fiyat > ema50) and (ema20 * 0.97 <= fiyat <= ema20 * 1.03) and (35 < rsi < 65):
                bilgi = f"🔹 {symbol} | Fiyat: {fiyat:.2f} | EMA20: {ema20:.2f} | RSI: {rsi:.1f}"
                adaylar.append(bilgi)
                print(bilgi)
        except Exception as e:
            continue
            
    return adaylar

def gemini_analizi(adaylar):
    if not adaylar:
        return "📉 Bugün SafeBlade stratejisine uyan hisse çıkmadı. Nakitte beklemeye devam."
    
    hisseler_str = "\n".join(adaylar)
    tarih = datetime.datetime.now(pytz.timezone('Europe/Istanbul')).strftime("%d %B %Y")
    
    prompt = f"""
    TARİH: {tarih}
    GÖREV: Aşağıdaki hisseler teknik olarak ALIM bölgesinde (Trend yukarı, EMA20 desteğinde).
    Ancak temel riskleri kontrol etmem lazım.
    
    HİSSELER:
    {hisseler_str}
    
    YAPMAN GEREKEN:
    Google Aramayı kullanarak bu hisseler için "son dakika haberi", "bilanço tarihi" ve "analist notu" araması yap.
    
    ÇIKTI (Telegram mesajı formatında):
    🦁 **SAFEBLADE GÜNLÜK RAPOR**
    
    (Her hisse için):
    ✅ **Hisse Kodu**
    * 📊 **Teknik:** EMA20 desteğinde, trend pozitif.
    * 📰 **Haber/Risk:** (Varsa kötü haber, yoksa "Temiz")
    * 🗓 **Bilanço:** (Yakın zamanda bilanço var mı?)
    * 🎯 **Karar:** "ALINABİLİR" veya "RİSKLİ/BEKLE"
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
    rapor = gemini_analizi(bulunanlar)
    telegrama_gonder(rapor)
