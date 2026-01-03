# 🤖 SafeBlade AI - Gemini 3.0 Pro Swing Trade Botu

Bu proje, Google'ın en gelişmiş yapay zeka modeli **Gemini 3.0 Pro** ve **Thinking Mode** (Derin Düşünme) özelliğini kullanarak finansal piyasaları tarayan, **SafeBlade** stratejisine göre fırsatları belirleyen ve sonuçları **Telegram** üzerinden raporlayan tam otomatik bir bottur.

> **Not:** Bu bot **GitHub Actions** üzerinde çalıştığı için sunucu maliyeti yoktur ve bilgisayarınız kapalıyken bile her sabah otomatik çalışır.

## 🚀 Özellikler

* **Yapay Zeka Destekli Analiz:** Gemini 3.0 Pro modeli, sadece veriyi okumaz; "Thinking Mode" sayesinde bir analist gibi mantık yürütür.
* **Canlı Veri (Google Search):** Model, Google Arama motorunu kullanarak anlık fiyatları, indikatörleri (RSI, EMA) ve haber akışını tarar.
* **Özel Strateji (SafeBlade):** Rastgele hisse önermez. Sadece yükseliş trendindeki düzeltmeleri (Pullback) avlar.
* **Otomatik Zamanlama:** Her sabah (Borsa açılış öncesi) otomatik çalışır.
* **Telegram Entegrasyonu:** Analiz raporunu doğrudan cebinize gönderir.

## 🧠 Algoritma Nasıl Çalışır? (SafeBlade Stratejisi)

Bot, interneti tararken aşağıdaki katı kuralları uygular:

1.  📈 **Ana Trend:** Fiyat kesinlikle **50 Günlük Hareketli Ortalamanın (EMA 50)** üzerinde olmalıdır.
2.  🧲 **Düzeltme (Pullback):** Fiyat kısa vadeli ortalamasına **(EMA 20)** geri çekilmiş veya temas etmiş olmalıdır.
3.  📊 **Momentum (RSI):** RSI değeri **35 ile 65** arasında olmalıdır (Aşırı şişmiş veya ölü hisseler elenir).
4.  ⚠️ **Hacim Analizi:** Düşüşler hacimsiz, yükselişler hacimli olmalıdır.

## 🛠️ Kurulum

Bu botu kendi hesabınızda çalıştırmak için şu adımları izleyin:

### 1. Projeyi Forklayın
Sağ üstteki **Fork** butonuna tıklayarak projeyi kendi GitHub hesabınıza kopyalayın.

### 2. API Anahtarlarını Alın
* **Gemini API Key:** [Google AI Studio](https://aistudio.google.com/app/apikey) adresinden ücretsiz bir anahtar alın.
* **Telegram Bot Token:** Telegram'da `@BotFather` ile konuşarak yeni bir bot oluşturun ve token alın.
* **Telegram Chat ID:** Telegram'da `@userinfobot` ile konuşarak kendi ID'nizi öğrenin.

### 3. GitHub Secrets Ayarları
Projenizin **Settings** -> **Secrets and variables** -> **Actions** kısmına gidin ve şu 3 anahtarı ekleyin:

| Secret İsmi | Değer |
| :--- | :--- |
| `GEMINI_API_KEY` | Google AI Studio'dan aldığınız anahtar |
| `TELEGRAM_BOT_TOKEN` | BotFather'dan gelen token (Örn: `12345:ABC...`) |
| `TELEGRAM_CHAT_ID` | Mesajın geleceği ID (Örn: `12345678`) |

### 4. Çalıştırın!
Kurulum bitti! Bot her sabah 09:00'da (TSİ) otomatik çalışacaktır. Test etmek için **Actions** sekmesinden manuel tetikleyebilirsiniz.

## 📂 Dosya Yapısı

* `main.py`: Botun beyni. Gemini API ile konuşan ve analizi yapan Python kodu.
* `.github/workflows/bot.yml`: Zamanlayıcı ayarı. Botun ne zaman çalışacağını belirler.
* `requirements.txt`: Gerekli kütüphaneler (`google-genai`, `requests`).

## ⚠️ Yasal Uyarı

Bu yazılım sadece eğitim ve bilgilendirme amaçlıdır. Üretilen içerik **Yatırım Tavsiyesi Değildir (YTD)**. Finansal piyasalar risk içerir; yapay zeka hata yapabilir (halüsinasyon görebilir). İşlem yapmadan önce kendi araştırmanızı yapmalısınız.

---
*Powered by Google Gemini 3.0 Pro & GitHub Actions*
