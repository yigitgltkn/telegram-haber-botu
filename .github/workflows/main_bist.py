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
# (Telegram ve Grafik fonksiyonları orjinalindeki ile aynı kalabilir)
def telegram_foto_gonder(caption, image_buffer):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID: return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    files = {'photo': ('chart.png', image_buffer, 'image/png')}
    data = {'chat_id': TELEGRAM_CHAT_ID, 'caption': caption, 'parse_mode': 'Markdown'}
    try: requests.post(url, files=files, data=data)
    except Exception as e: print(f"Hata: {e}")

def telegram_mesaj_gonder(mesaj):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID: return
    requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", 
                  data={'chat_id': TELEGRAM_CHAT_ID, 'text': mesaj, 'parse_mode': 'Markdown'})

def grafik_ciz(df, symbol):
    try:
        tr_time = datetime.datetime.now(pytz.timezone('Europe/Istanbul')).strftime("%H:%M")
        s = mpf.make_mpf_style(base_mpf_style='yahoo', rc={'font.size': 10})
        apds = [
            mpf.make_addplot(df['EMA_20'], color='orange', width=1.5),
            mpf.make_addplot(df['EMA_50'], color='blue', width=1.5),
        ]
        buf = BytesIO()
        mpf.plot(df.iloc[-60:], type='candle', style=s, addplot=apds[-60:], 
                 title=f"\n{symbol} - BIST SafeBlade ({tr_time})", volume=True, 
                 savefig=dict(fname=buf, dpi=100, bbox_inches='tight'))
        buf.seek(0)
        return buf
    except: return None

def get_bist_tickers():
    # BİST30 ve sağlam temelli BİST50 hisseleri (yfinance .IS takısı ister)
    return ["AKBNK.IS", "BIMAS.IS", "EREGL.IS", "FROTO.IS", "GARAN.IS", "KCHOL.IS", 
            "SAHOL.IS", "SISE.IS", "TCELL.IS", "THYAO.IS", "TOASO.IS", "TUPRS.IS", 
            "YKBNK.IS", "ASELS.IS", "ENKAI.IS", "PGSUS.IS", "TTKOM.IS", "MGROS.IS"]

# --- 📊 BİST ANALİZ MOTORU ---

def piyasa_genel_durumu():
    try:
        # BİST100 (XU100.IS) endeksini çekiyoruz
        data = yf.download("XU100.IS", period="6mo", interval="1d", progress=False)
        close = data['Close'] if 'Close' in data else data
        
        xu100_now = close.dropna().iloc[-1]
        xu100_ema50 = ta.trend.ema_indicator(close.dropna(), window=50).iloc[-1]
        
        durum = "POZİTİF (Boğa)" if float(xu100_now) > float(xu100_ema50) else "NEGATİF (Ayı)"
        ikon = "🟢" if durum.startswith("POZİTİF") else "🔴"
        
        return f"🇹🇷 **BİST PİYASA:** {durum} {ikon}\n📉 **BİST100:** {float(xu100_now):.2f}", durum
    except: return "⚠️ Piyasa verisi alınamadı.", "NÖTR"

def bist_temel_tarama(tickers_list):
    print("🔍 Temel Analiz Taraması Başlıyor (Ucuzluk Filtresi)...")
    saglam_hisseler = []
    
    for symbol in tickers_list:
        try:
            hisse = yf.Ticker(symbol)
            bilgiler = hisse.info
            fk_orani = bilgiler.get('trailingPE', 999) # Veri yoksa yüksek ver ki elensin
            pddd_orani = bilgiler.get('priceToBook', 999)
            
            # Kriter: F/K 15'ten küçük, PD/DD 4'ten küçük olanlar
            if fk_orani and pddd_orani and (0 < fk_orani < 15) and (0 < pddd_orani < 4):
                saglam_hisseler.append(symbol)
        except: continue
    
    print(f"✅ Temel analizi geçen hisse sayısı: {len(saglam_hisseler)}")
    return saglam_hisseler

def teknik_tarama(tickers_list):
    print("🚀 Teknik Tarama Başlıyor...")
    aday_listesi = []
    if not tickers_list: return aday_listesi
    
    try:
        data = yf.download(" ".join(tickers_list), period="6mo", interval="1d", group_by='ticker', threads=True)
    except: return []

    # Eğer sadece 1 hisse geldiyse, yf.download yapısı farklı olur, onu handle edelim
    is_multi = len(tickers_list) > 1

    for symbol in tickers_list:
        try:
            df = data[symbol].copy() if is_multi else data.copy()
            if len(df) < 50: continue
            if pd.isna(df['Close'].iloc[-1]): df = df.iloc[:-1]

            df['EMA_50'] = ta.trend.ema_indicator(df['Close'], window=50)
            df['EMA_20'] = ta.trend.ema_indicator(df['Close'], window=20)
            df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
            df['ATR'] = ta.volatility.average_true_range(df['High'], df['Low'], df['Close'], window=14)

            son = df.iloc[-1]
            fiyat = float(son['Close'])
            ema20 = float(son['EMA_20'])
            ema50 = float(son['EMA_50'])

            # BİST Volatilitesi için toleransları biraz daha geniş tutuyoruz (%1.5 altı, %5 üstü)
            k_trend = fiyat > ema50
            k_destek = (ema20 * 0.985) <= fiyat <= (ema20 * 1.05)
            k_rsi = 30 < son['RSI'] < 60

            if k_trend and k_destek and k_rsi:
                fark_yuzde = abs(fiyat - ema20) / ema20
                aday_listesi.append({
                    'symbol': symbol,
                    'fiyat': fiyat,
                    'stop': fiyat - (2 * float(son['ATR'])),
                    'score': fark_yuzde,
                    'sinyaller': f"RSI: {float(son['RSI']):.2f} - Destek Testi",
                    'df': df
                })
        except: continue

    aday_listesi.sort(key=lambda x: x['score'])
    return aday_listesi[:3]

def gemini_ve_gonder(piyasa_raporu, adaylar):
    if not adaylar:
        telegram_mesaj_gonder(f"{piyasa_raporu}\n\n📉 Kriterlere uyan BİST hissesi yok.")
        return

    client = genai.Client(api_key=GEMINI_API_KEY)
    ist_time = datetime.datetime.now(pytz.timezone('Europe/Istanbul')).strftime("%d %B %Y %H:%M")

    telegram_mesaj_gonder(f"🇹🇷 **BİST SAFEBLADE RAPORU**\n⏰ IST: {ist_time}\n{piyasa_raporu}")

    for hisse in adaylar:
        symbol = hisse['symbol']
        grafik = grafik_ciz(hisse['df'], symbol)
        
        # BİST için Özel KAP ve Haber Promptu
        prompt = f"""
        Hisse: {symbol.replace('.IS', '')} (Borsa İstanbul)
        Fiyat: {hisse['fiyat']} TL
        Teknik Durum: Temel analizi sağlam, ucuz kalmış ve EMA20 desteğine çekilmiş.
        
        GÖREV:
        1. Bu hisse için Google'da son 48 saat içindeki Türkiye menşeli haberleri ara.
        2. Özellikle "KAP bildirimi", "Bilanço", "İş ilişkisi" veya "Pay geri alım" haberleri var mı kontrol et.
        3. Eski haberleri görmezden gel.
        
        TELEGRAM MESAJI FORMATI:
        📊 **{symbol.replace('.IS', '')}** ({hisse['fiyat']:.2f} TL)
        
        💡 **Teknik:** {hisse['sinyaller']}
        📰 **KAP / Haber (Canlı):** [Son 48 saatte kritik bir haber veya KAP varsa özetle. Yoksa "Önemli bir haber akışı yok" yaz.]
        🛡️ **Stop-Loss:** {hisse['stop']:.2f} TL
        """
        
        try:
            response = client.models.generate_content(
                model=MODEL_NAME, contents=prompt,
                config=types.GenerateContentConfig(tools=[types.Tool(google_search=types.GoogleSearch())], response_mime_type="text/plain")
            )
            yorum = response.text
        except Exception as e:
            yorum = f"📊 **{symbol.replace('.IS', '')}**\n⚠️ AI Hatası: {e}"

        if grafik: telegram_foto_gonder(yorum, grafik)
        else: telegram_mesaj_gonder(yorum)
        time.sleep(2)

if __name__ == "__main__":
    start = time.time()
    piyasa_metni, durum = piyasa_genel_durumu()
    
    tum_hisseler = get_bist_tickers()
    # 1. Aşama: Temel Analiz Eleği
    saglam_hisseler = bist_temel_tarama(tum_hisseler)
    # 2. Aşama: Teknik Analiz Eleği
    en_iyiler = teknik_tarama(saglam_hisseler)
    # 3. Aşama: Yapay Zeka Haber Yorumu
    gemini_ve_gonder(piyasa_metni, en_iyiler)
    
    print(f"\n✅ BİST Analizi Tamamlandı. Süre: {time.time() - start:.2f} sn.")
