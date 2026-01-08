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

# Genişletilmiş Profesyonel Liste
HISSE_LISTESI = [
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA",
    "AMD", "AVGO", "QCOM", "INTC", "TXN", "MU", "LRCX", "KLAC", "MRVL", "ARM", "TSM", "SMCI",
    "ADBE", "CRM", "ORCL", "NOW", "SNOW", "DDOG", "PLTR", "MDB", "TEAM", "HUBS",
    "PANW", "CRWD", "FTNT", "ZS", "NET", "CYBR",
    "PYPL", "SQ", "COIN", "HOOD", "MSTR", "AFRM", "V", "MA",
    "NFLX", "ABNB", "UBER", "DASH", "BKNG", "SBUX", "CMG", "LULU", "NKE",
    "MRNA", "GILD", "VRTX", "REGN", "ISRG", "AMGN",
    "CSCO", "IBM", "DELL", "HPQ", "ANET",
    "PEP", "COST", "WMT", "TGT", "MDLZ"
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

def piyasa_genel_durumu():
    """
    QQQ, VIX ve TNX verilerini analiz ederek piyasanın 'Hava Durumunu' belirler.
    """
    print("\n🌍 KÜRESEL PİYASA ANALİZİ YAPILIYOR...")
    try:
        # Verileri çek (QQQ, VIX, TNX)
        tickers = ["QQQ", "^VIX", "^TNX"]
        data = yf.download(tickers, period="6mo", interval="1d", progress=False)
        
        # Multi-index düzeltmesi
        if isinstance(data.columns, pd.MultiIndex):
            close_prices = data['Close']
        else:
            close_prices = data
            
        # --- QQQ ANALİZİ (Ana Gemi) ---
        qqq_series = close_prices["QQQ"].dropna()
        qqq_ema50 = ta.trend.ema_indicator(close=qqq_series, window=50).iloc[-1]
        qqq_price = qqq_series.iloc[-1]
        qqq_durum = "POZİTİF (Trend Yukarı)" if qqq_price > qqq_ema50 else "NEGATİF (Trend Altında)"
        qqq_icon = "🟢" if qqq_price > qqq_ema50 else "🔴"

        # --- VIX ANALİZİ (Korku) ---
        vix_price = close_prices["^VIX"].dropna().iloc[-1]
        if vix_price < 20:
            vix_durum = "GÜVENLİ (Düşük Korku)"
            vix_icon = "🟢"
        elif vix_price < 30:
            vix_durum = "DİKKATLİ OL (Volatilite Var)"
            vix_icon = "🟡"
        else:
            vix_durum = "TEHLİKE (Panik Satışı)"
            vix_icon = "🔴"

        # --- TNX ANALİZİ (Faiz Baskısı) ---
        tnx_price = close_prices["^TNX"].dropna().iloc[-1]
        tnx_icon = "🟢" if tnx_price < 4.2 else "🔴" # 4.2 kritik eşik kabul edelim

        # GENEL KARAR
        piyasa_puani = 0
        if qqq_price > qqq_ema50: piyasa_puani += 1
        if vix_price < 25: piyasa_puani += 1
        
        genel_karar = ""
        if piyasa_puani == 2:
            genel_karar = "✅ PİYASA IŞIKLARI YEŞİL: Swing Trade İçin Uygun."
        elif piyasa_puani == 1:
            genel_karar = "⚠️ PİYASA KARIŞIK: Pozisyon büyüklüğünü azalt."
        else:
            genel_karar = "⛔ PİYASA KIRMIZI: Nakitte kalmak en iyisi."

        rapor = (
            f"🌍 **KÜRESEL PİYASA KOKPİTİ**\n"
            f"{qqq_icon} **QQQ (Nasdaq):** {qqq_price:.2f} (EMA50: {qqq_ema50:.2f}) -> {qqq_durum}\n"
            f"{vix_icon} **VIX (Korku):** {vix_price:.2f} -> {vix_durum}\n"
            f"{tnx_icon} **TNX (Faiz):** %{tnx_price:.2f}\n"
            f"---------------------------------\n"
            f"🧠 **HOCA'NIN KARARI:** {genel_karar}\n"
        )
        print(rapor)
        return rapor, piyasa_puani

    except Exception as e:
        print(f"Piyasa analizi hatası: {e}")
        return "⚠️ Piyasa verisi çekilemedi.\n", 1 # Hata olursa nötr kabul et

def teknik_tarama(piyasa_puani):
    print("\n" + "="*50)
    print("🔍 HİSSE TARAMASI BAŞLIYOR...")
    
    # Eğer piyasa çok kötüyse (Puan 0), tarama yapma veya uyar.
    # Biz yine de yapalım ama kullanıcı bilsin.
    
    adaylar = []
    
    for symbol in HISSE_LISTESI:
        try:
            df = yf.download(symbol, period="6mo", interval="1d", progress=False)
            if len(df) < 50: continue
            
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            df['EMA_50'] = ta.trend.ema_indicator(close=df['Close'], window=50)
            df['EMA_20'] = ta.trend.ema_indicator(close=df['Close'], window=20)
            df['RSI'] = ta.momentum.rsi(close=df['Close'], window=14)

            son = df.iloc[-1]
            fiyat = float(son['Close'])
            ema50 = float(son['EMA_50'])
            ema20 = float(son['EMA_20'])
            rsi = float(son['RSI'])

            # STRATEJİ: SafeBlade
            if (fiyat > ema50) and (ema20 * 0.97 <= fiyat <= ema20 * 1.03) and (35 < rsi < 65):
                bilgi = f"🔹 {symbol} | Fiyat: {fiyat:.2f} | RSI: {rsi:.1f}"
                adaylar.append(bilgi)
                print(f"✅ BULUNDU: {symbol}")
        except Exception:
            continue
            
    return adaylar

def gemini_analizi(piyasa_raporu, adaylar):
    if not adaylar:
        return f"{piyasa_raporu}\n📉 **SONUÇ:** Piyasa analizinden sonra hisse taraması yapıldı ancak stratejiye uyan (EMA 20 Pullback) hisse bulunamadı."
    
    hisseler_str = "\n".join(adaylar)
    tarih = datetime.datetime.now(pytz.timezone('Europe/Istanbul')).strftime("%d %B %Y")
    
    prompt = f"""
    TARİH: {tarih}
    GÖREV: Borsa Yatırım Danışmanı olarak rapor yaz.
    
    1. KISIM: AŞAĞIDAKİ PİYASA ANALİZİNİ ÖZETLE:
    {piyasa_raporu}
    
    2. KISIM: AŞAĞIDAKİ HİSSELERİ ANALİZ ET:
    {hisseler_str}
    
    Bu hisseler teknik olarak EMA20 desteğinde. 
    Google Aramayı kullanarak bu hisseler için: "Kötü haber" ve "Bilanço tarihi" kontrolü yap.
    
    ÇIKTI FORMATI (Telegram İçin):
    🌍 **SAFEBLADE GÜNLÜK BÜLTEN**
    
    (Buraya Piyasa Yorumunu Kısaca Yaz)
    
    🚀 **FIRSAT ADAYLARI**
    (Her hisse için):
    ✅ **Hisse Kodu**
    * 📊 Teknik: EMA20 Teması.
    * 📰 Haber/Risk: ...
    * 🎯 Karar: "GİR" veya "BEKLE"
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
    # 1. Piyasaya Bak
    piyasa_metni, puan = piyasa_genel_durumu()
    
    # 2. Hisseleri Tara
    adaylar = teknik_tarama(puan)
    
    # 3. Raporu Oluştur ve Gönder
    final_rapor = gemini_analizi(piyasa_metni, adaylar)
    telegrama_gonder(final_rapor)
