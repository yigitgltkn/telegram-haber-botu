import os
import requests
import datetime
import pytz
import time
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from google import genai
from google.genai import types

# --- ⚙️ AYARLAR ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# 🔥 GÖRSELDEKİ MODEL AYARI BURADA YAPILDI:
MODEL_NAME = "gemini-3-pro-preview" 

# --- 🛠️ YARDIMCI FONKSİYONLAR ---

def telegrama_gonder(mesaj):
    """Mesajı Telegram botuna gönderir."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ Telegram ayarları eksik! Mesaj konsola yazılıyor...")
        print(mesaj)
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    limit = 4000
    parcalar = [mesaj[i:i+limit] for i in range(0, len(mesaj), limit)]
    
    try:
        for parca in parcalar:
            payload = {'chat_id': TELEGRAM_CHAT_ID, 'text': parca, 'parse_mode': 'Markdown'}
            requests.post(url, data=payload)
        print("✅ Rapor Telegram'a gönderildi.")
    except Exception as e:
        print(f"❌ Telegram hatası: {e}")

def get_nasdaq100_tickers():
    """Wikipedia'dan güncel NASDAQ 100 listesini çeker."""
    print("🌍 NASDAQ 100 Listesi güncelleniyor...")
    fallback_list = ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "AMD", "QCOM", "INTC"]
    
    try:
        url = "https://en.wikipedia.org/wiki/Nasdaq-100"
        tables = pd.read_html(url)
        
        nasdaq_table = None
        for table in tables:
            if 'Ticker' in table.columns or 'Symbol' in table.columns:
                nasdaq_table = table
                break
        
        if nasdaq_table is not None:
            col = 'Ticker' if 'Ticker' in nasdaq_table.columns else 'Symbol'
            tickers = nasdaq_table[col].tolist()
            tickers = [t.replace('.', '-') for t in tickers]
            print(f"✅ {len(tickers)} hisse listeye alındı.")
            return tickers
        else:
            print("⚠️ Tablo bulunamadı, yedek liste kullanılıyor.")
            return fallback_list
            
    except Exception as e:
        print(f"❌ Liste çekme hatası: {e}. Yedek liste devrede.")
        return fallback_list

# --- 📊 ANALİZ MOTORU ---

def piyasa_genel_durumu():
    """QQQ ve VIX ile piyasanın genel yönünü belirler."""
    print("\n🌍 KÜRESEL PİYASA ANALİZİ...")
    try:
        tickers = ["QQQ", "^VIX", "^TNX"]
        data = yf.download(tickers, period="6mo", interval="1d", progress=False)
        
        if isinstance(data.columns, pd.MultiIndex):
            close = data.xs('Close', level=0, axis=1)
        else:
            close = data['Close']
            
        qqq_series = close["QQQ"].dropna()
        vix_price = close["^VIX"].dropna().iloc[-1]
        tnx_price = close["^TNX"].dropna().iloc[-1]
        
        qqq_ema50 = ta.ema(qqq_series, length=50).iloc[-1]
        qqq_price = qqq_series.iloc[-1]
        
        piyasa_puani = 0
        qqq_durum = "YUKARI" if qqq_price > qqq_ema50 else "AŞAĞI"
        if qqq_price > qqq_ema50: piyasa_puani += 1
        if vix_price < 22: piyasa_puani += 1
        
        ikon = "🟢" if piyasa_puani == 2 else "🟡" if piyasa_puani == 1 else "🔴"
        
        rapor = (
            f"🌍 **PİYASA KOKPİTİ** {ikon}\n"
            f"📈 **QQQ:** {qqq_price:.2f} (Trend: {qqq_durum})\n"
            f"😨 **VIX:** {vix_price:.2f} (Risk İştahı: {'Açık' if vix_price<20 else 'Kapalı'})\n"
            f"🇺🇸 **Faiz (TNX):** %{tnx_price:.2f}\n"
            f"---------------------------------"
        )
        print(rapor)
        return rapor, piyasa_puani

    except Exception as e:
        print(f"Piyasa analizi hatası: {e}")
        return "⚠️ Piyasa verisi alınamadı.", 1

def teknik_tarama(tickers_list):
    """Verilen listeyi SafeBlade stratejisine göre tarar."""
    print(f"\n🚀 {len(tickers_list)} Hisse taranıyor (Bulk Download)...")
    
    aday_listesi = []
    
    try:
        tickers_str = " ".join(tickers_list)
        data = yf.download(tickers_str, period="6mo", interval="1d", group_by='ticker', threads=True, progress=True)
    except Exception as e:
        print(f"Veri indirme hatası: {e}")
        return []

    print("\n⚡ Teknik indikatörler hesaplanıyor...")
    
    for symbol in tickers_list:
        try:
            if symbol not in data: continue
            df = data[symbol].copy()
            
            if df.empty or len(df) < 50: continue
            df.dropna(inplace=True)
            if len(df) < 50: continue

            # --- İNDİKATÖRLER (pandas_ta) ---
            df['EMA_50'] = ta.ema(df['Close'], length=50)
            df['EMA_20'] = ta.ema(df['Close'], length=20)
            df['RSI'] = ta.rsi(df['Close'], length=14)
            df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
            df['Vol_SMA'] = ta.sma(df['Volume'], length=20)

            son = df.iloc[-1]
            fiyat = float(son['Close'])
            ema50 = float(son['EMA_50'])
            ema20 = float(son['EMA_20'])
            rsi = float(son['RSI'])
            atr = float(son['ATR'])
            vol = float(son['Volume'])
            vol_sma = float(son['Vol_SMA'])

            # --- STRATEJİ: SafeBlade ---
            kosul_trend = fiyat > ema50
            kosul_pullback = (ema20 * 0.97) <= fiyat <= (ema20 * 1.03)
            kosul_rsi = 40 < rsi < 65
            kosul_hacim = vol < (vol_sma * 2.5)

            if kosul_trend and kosul_pullback and kosul_rsi and kosul_hacim:
                fark_yuzde = abs(fiyat - ema20) / ema20
                stop_loss = fiyat - (2 * atr)
                risk_orani = (fiyat - stop_loss) / fiyat * 100
                
                text = (
                    f"🔹 **{symbol}** (${fiyat:.2f})\n"
                    f"   📊 **EMA20 Fark:** %{fark_yuzde*100:.2f} | **RSI:** {rsi:.1f}\n"
                    f"   🛡️ **Stop:** {stop_loss:.2f} (Risk: %{risk_orani:.1f})"
                )
                
                aday_listesi.append({
                    'symbol': symbol,
                    'text': text,
                    'score': fark_yuzde 
                })
                
        except Exception:
            continue

    if not aday_listesi:
        return []

    aday_listesi.sort(key=lambda x: x['score'])
    top_5 = aday_listesi[:5]
    print(f"✅ Filtreden geçen: {len(aday_listesi)} | Seçilen Top 5: {[x['symbol'] for x in top_5]}")
    return [x['text'] for x in top_5]

def gemini_analizi(piyasa_raporu, adaylar):
    """Gemini 3 Pro Preview kullanarak analiz yapar."""
    
    if not adaylar:
        return f"{piyasa_raporu}\n\n📉 **SONUÇ:** Stratejiye uygun hisse bulunamadı. Nakitte bekle."

    hisseler_str = "\n".join(adaylar)
    tarih = datetime.datetime.now(pytz.timezone('Europe/Istanbul')).strftime("%d %B %Y")
    
    prompt = f"""
    Sen uzman bir borsa asistanısın. Tarih: {tarih}

    PİYASA ÖZETİ:
    {piyasa_raporu}

    TEKNİK OLARAK GİRİŞ VEREN HİSSELER (SafeBlade Stratejisi):
    {hisseler_str}

    GÖREVİN:
    Bu hisseler teknik olarak "Al" veriyor (EMA20 desteğinde).
    Google Search Tool kullanarak her bir şirket için şu riskleri kontrol et:
    1. **Bilanço (Earnings):** Önümüzdeki 5 gün içinde bilanço açıklayacak mı? (Varsa UYAR).
    2. **Haber Akışı:** Son 48 saatte hisseyi düşürecek çok kötü bir haber var mı?

    ÇIKTI FORMATI (Telegram için):
    🌍 **SAFEBLADE NASDAQ RAPORU** ({tarih})
    
    (Piyasa hakkında tek cümlelik yorum)

    🚀 **GÜNÜN FIRSATLARI**
    
    1️⃣ **HİSSE KODU**
       💡 **Teknik:** (Kısaca durumu öv)
       📅 **Bilanço:** [Tarih veya "Yakın Takvim Yok"] 
       ⚠️ **Risk Durumu:** [Varsa haberi yaz yoksa "Negatif akış yok" yaz]
       🎯 **Karar:** "GİRİLEBİLİR" veya "BEKLE"

    (Bunu seçilen her hisse için yap)
    ⚠️ *Yasal Uyarı: Yatırım tavsiyesi değildir.*
    """

    print(f"\n🧠 {MODEL_NAME} Analiz Yapıyor...")
    
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(
            model=MODEL_NAME,  # <-- BURASI GÜNCELLENDİ
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
                response_mime_type="text/plain"
            )
        )
        return response.text
    except Exception as e:
        return f"{piyasa_raporu}\n\n⚠️ AI Analizi Hatası: {e}\n\n{hisseler_str}"

if __name__ == "__main__":
    start_time = time.time()
    
    piyasa_metni, puan = piyasa_genel_durumu()
    hisse_listesi = get_nasdaq100_tickers()
    en_iyi_adaylar = teknik_tarama(hisse_listesi)
    final_rapor = gemini_analizi(piyasa_metni, en_iyi_adaylar)
    telegrama_gonder(final_rapor)
    
    print(f"\n⏱️ Toplam Süre: {time.time() - start_time:.2f} saniye.")
