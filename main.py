import os
import requests
import datetime
import pytz
import time
import yfinance as yf
import pandas as pd
import ta
import mplfinance as mpf
from io import BytesIO
from google import genai
from google.genai import types

# --- ⚙️ AYARLAR ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
MODEL_NAME = "gemini-3-pro-preview"

# --- 🛠️ YARDIMCI FONKSİYONLAR ---

def telegram_foto_gonder(caption, image_buffer):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print(caption)
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    files = {'photo': ('chart.png', image_buffer, 'image/png')}
    data = {'chat_id': TELEGRAM_CHAT_ID, 'caption': caption, 'parse_mode': 'Markdown'}
    try: requests.post(url, files=files, data=data)
    except Exception as e: print(f"Hata: {e}")

def telegram_mesaj_gonder(mesaj):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print(mesaj)
        return
    requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", 
                  data={'chat_id': TELEGRAM_CHAT_ID, 'text': mesaj, 'parse_mode': 'Markdown'})

def grafik_ciz(df, symbol):
    try:
        # Türkiye saatini al
        tr_time = datetime.datetime.now(pytz.timezone('Europe/Istanbul')).strftime("%H:%M")
        
        # Grafik Stili
        s = mpf.make_mpf_style(base_mpf_style='yahoo', rc={'font.size': 10})
        apds = [
            mpf.make_addplot(df['EMA_20'], color='orange', width=1.5),
            mpf.make_addplot(df['EMA_50'], color='blue', width=1.5),
        ]
        
        buf = BytesIO()
        # Son 60 mum (Günlük)
        mpf.plot(
            df.iloc[-60:], 
            type='candle', 
            style=s, 
            addplot=apds[-60:], 
            title=f"\n{symbol} - SafeBlade Analiz ({tr_time})",
            volume=True, 
            savefig=dict(fname=buf, dpi=100, bbox_inches='tight')
        )
        buf.seek(0)
        return buf
    except: return None

def get_nasdaq100_tickers():
    print("🌍 NASDAQ 100 Listesi çekiliyor...")
    fallback = ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "AMD", "QCOM", "INTC"]
    try:
        url = "https://en.wikipedia.org/wiki/Nasdaq-100"
        tables = pd.read_html(url)
        nasdaq_table = next((t for t in tables if 'Ticker' in t.columns or 'Symbol' in t.columns), None)
        if nasdaq_table:
            col = 'Ticker' if 'Ticker' in nasdaq_table.columns else 'Symbol'
            return [t.replace('.', '-') for t in nasdaq_table[col].tolist()]
    except: pass
    return fallback

# --- 📊 ANALİZ MOTORU ---

def piyasa_genel_durumu():
    try:
        # Piyasayı en güncel haliyle çek
        data = yf.download(["QQQ", "^VIX"], period="6mo", interval="1d", progress=False)
        close = data['Close'] if 'Close' in data else data
        
        qqq_series = close["QQQ"].dropna()
        qqq_now = qqq_series.iloc[-1]
        vix_now = close["^VIX"].dropna().iloc[-1]
        
        qqq_ema50 = ta.trend.ema_indicator(qqq_series, window=50).iloc[-1]
        
        durum = "POZİTİF (Boğa)" if qqq_now > qqq_ema50 else "NEGATİF (Ayı)"
        ikon = "🟢" if durum.startswith("POZİTİF") and vix_now < 22 else "🔴"
        
        return f"🌍 **PİYASA:** {durum} {ikon}\n📉 **VIX:** {vix_now:.2f} (Risk Seviyesi)", durum
    except: return "⚠️ Piyasa verisi alınamadı.", "NÖTR"

def teknik_tarama(tickers_list):
    print(f"\n🚀 {len(tickers_list)} Hisse taranıyor (Canlı Veri)...")
    aday_listesi = []
    
    try:
        # Veriyi çekerken threads kullanıyoruz, en son veriyi alıyoruz
        data = yf.download(" ".join(tickers_list), period="6mo", interval="1d", group_by='ticker', threads=True)
    except: return []

    for symbol in tickers_list:
        try:
            if symbol not in data: continue
            # dropna() ile eksik verileri at ama son satırın (bugünün) durduğundan emin ol
            df = data[symbol].copy()
            if len(df) < 50: continue
            
            # Eğer son mumun verisi tam değilse (NaN varsa) onu atma, hesaplamaya dahil et
            # yfinance bazen son günü NaN getirebilir, onu temizle:
            if pd.isna(df['Close'].iloc[-1]):
                df = df.iloc[:-1]

            # İndikatörler
            df['EMA_50'] = ta.trend.ema_indicator(df['Close'], window=50)
            df['EMA_20'] = ta.trend.ema_indicator(df['Close'], window=20)
            df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
            df['ATR'] = ta.volatility.average_true_range(df['High'], df['Low'], df['Close'], window=14)
            
            # MACD
            macd = ta.trend.MACD(df['Close'])
            df['MACD_Diff'] = macd.macd_diff()

            son = df.iloc[-1]
            
            fiyat = float(son['Close'])
            ema20 = float(son['EMA_20'])
            ema50 = float(son['EMA_50'])

            # --- 1. KATMAN: STRICT SAFEBLADE ---
            k_trend = fiyat > ema50
            # Destek: EMA20'nin %0.5 altı ile %4 üstü arası (Sarkmalara az tolerans)
            k_destek = (ema20 * 0.995) <= fiyat <= (ema20 * 1.04)
            k_rsi = 40 < son['RSI'] < 65

            if k_trend and k_destek and k_rsi:
                puan = 0
                sinyaller = []

                # --- 2. KATMAN: TEYİTLER ---
                # A) MACD Dönüşü (Histogram yükseliyor mu?)
                if df['MACD_Diff'].iloc[-1] > df['MACD_Diff'].iloc[-2]:
                    puan += 2
                    sinyaller.append("MACD Al")
                
                # B) Hammer Mumu
                govde = abs(son['Close'] - son['Open'])
                alt_fitil = min(son['Open'], son['Close']) - son['Low']
                ust_fitil = son['High'] - max(son['Open'], son['Close'])
                if (alt_fitil > 2 * govde) and (ust_fitil < govde):
                    puan += 3
                    sinyaller.append("🔥 HAMMER")

                # C) Hacim Patlaması Yok (Sakin düşüş)
                vol_avg = df['Volume'].rolling(20).mean().iloc[-1]
                if son['Volume'] < (vol_avg * 2.5):
                    puan += 1

                fark_yuzde = abs(fiyat - ema20) / ema20
                
                aday_listesi.append({
                    'symbol': symbol,
                    'fiyat': fiyat,
                    'stop': fiyat - (2 * son['ATR']),
                    'score': fark_yuzde,
                    'extra_puan': puan,
                    'sinyaller': ", ".join(sinyaller) if sinyaller else "Destek Testi",
                    'df': df
                })
        except: continue

    # Puanı yüksek olan en üstte
    aday_listesi.sort(key=lambda x: (-x['extra_puan'], x['score']))
    return aday_listesi[:3]

def gemini_ve_gonder(piyasa_raporu, adaylar):
    if not adaylar:
        telegram_mesaj_gonder(f"{piyasa_raporu}\n\n📉 Kriterlere uyan hisse yok.")
        return

    print("🧠 Gemini Haberleri Tarıyor (Canlı)...")
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    # Zaman Bilgisi (New York ve İstanbul)
    ist_time = datetime.datetime.now(pytz.timezone('Europe/Istanbul')).strftime("%d %B %Y %H:%M")
    ny_time = datetime.datetime.now(pytz.timezone('America/New_York')).strftime("%H:%M")

    # Başlık
    telegram_mesaj_gonder(f"🌍 **SAFEBLADE CANLI RAPOR**\n⏰ IST: {ist_time} | NY: {ny_time}\n{piyasa_raporu}")

    for hisse in adaylar:
        symbol = hisse['symbol']
        grafik = grafik_ciz(hisse['df'], symbol)
        
        # --- GÜNCELLENMİŞ PROMPT (SON DAKİKA ODAKLI) ---
        prompt = f"""
        Hisse: {symbol}
        Fiyat: {hisse['fiyat']}
        Teknik Durum: {hisse['sinyaller']}
        
        GÖREV:
        1. Bu hisse için Google'da "SON 24 SAAT" içindeki haberleri ara.
        2. Özellikle "Earnings" (Bilanço) ve "Breaking News" (Son Dakika) var mı bak.
        3. Eski haberleri görmezden gel, sadece bugünün gündemine odaklan.
        
        TELEGRAM MESAJI FORMATI:
        📊 **{symbol}** (${hisse['fiyat']:.2f})
        
        💡 **Teknik:** {hisse['sinyaller']} (EMA20 Desteğinde)
        📅 **Bilanço:** [Tarih ve Durum]
        📰 **Haber (Canlı):** [Son 24 saatte kritik bir haber var mı? Yoksa "Akış Sakin" yaz.]
        🛡️ **Stop-Loss:** {hisse['stop']:.2f}
        """
        
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config=types.GenerateContentConfig(
                    tools=[types.Tool(google_search=types.GoogleSearch())],
                    response_mime_type="text/plain"
                )
            )
            yorum = response.text
        except Exception as e:
            yorum = f"📊 **{symbol}**\n⚠️ AI Bağlantı Hatası: {e}"

        if grafik: telegram_foto_gonder(yorum, grafik)
        else: telegram_mesaj_gonder(yorum)
        time.sleep(1)

if __name__ == "__main__":
    start = time.time()
    piyasa_metni, durum = piyasa_genel_durumu()
    tickers = get_nasdaq100_tickers()
    en_iyiler = teknik_tarama(tickers)
    gemini_ve_gonder(piyasa_metni, en_iyiler)
    print(f"\n✅ Tamamlandı. Süre: {time.time() - start:.2f} sn.")
