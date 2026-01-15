## 📚 sEkitap Bot v9.3

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Telethon](https://img.shields.io/badge/Telethon-1.34+-green.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)
![Version](https://img.shields.io/badge/version-v9.0-red.svg)
![Database](https://img.shields.io/badge/database-SQLite-blue.svg)
![Platform](https://img.shields.io/badge/platform-Telegram-blue.svg)

> 🤖 **Akıllı Telegram Kitap Botu** - PDF/EPUB dosyalarını otomatik tanıyıp detaylı bilgilerle zenginleştirir

## 🌟 Öne Çıkan Özellikler

<div align="left">

### 🎯 **Akıllı Kitap Tanıma**
- ✅ Otomatik PDF/EPUB dosya analizi
- ✅ ISBN tabanlı doğrulama
- ✅ Benzerlik algoritması ile başlık eşleştirme

### 🔍 **3 Farklı Kaynak Desteği**
- 📚 **1000Kitap** - Türkçe kitap arşivi
- 🛒 **Kitapyurdu** - En büyük online kitapçı
- 🌟 **Goodreads** - Dünyanın en büyük kitap platformu


### 💡 **Gelişmiş Teknolojiler**
- 🧠 **Yapay Zeka Benzerlik Algoritması**
- 💾 **TTL Destekli Akıllı Önbellekleme**
- ⚡ **Asenkron İşleme**
- 🔧 **Modüler Mimari**

</div>

## 🚀 Kurulum Rehberi

### 📋 Gereksinimler
- Python 3.10 veya üzeri
- Telegram hesabı
- Telegram API erişimi

### 🔧 Kurulum Adımları

#### 1. Projeyi Klonlayın
```bash
git clone https://github.com/trepcan/sekitap-bot.git
cd sekitap-bot
```

#### 2. Sanal Ortam Oluşturun (Önerilen)
```bash
# Linux/Mac
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

#### 3. Bağımlılıkları Yükleyin
```bash
pip install -r requirements.txt
```

#### 4. Ortam Dosyasını Oluşturun
```bash
cp .env.example .env
```

#### 5. Telegram API Bilgilerini Alın

<details>
<summary>🔍 Detaylı Telegram API Kurulumu</summary>

1. [my.telegram.org/apps](https://my.telegram.org/apps) adresine gidin
2. Telefon numaranızla giriş yapın
3. "Create Application" butonuna tıklayın
4. Aşağıdaki bilgileri doldurun:
   - App title: `sEkitap Bot`
   - Short name: `sekitap`
   - Platform: Desktop
5. API ID ve API Hash değerlerini `.env` dosyasına yapıştırın

</details>

#### 6. Gerekli ID'leri Bulun

<details>
<summary>🔍 Admin ID ve Kanal ID Bulma</summary>

**Admin ID Bulma:**
1. Telegram'da [@userinfobot](https://t.me/userinfobot) botuna `/start` gönderin
2. Gelen mesajdaki "id" değerini kullanın

**Kanal ID Bulma:**
1. Hedef kanaldan herhangi bir mesajı kendinize forward edin
2. Forward ettiğiniz mesaja [@userinfobot](https://t.me/userinfobot) ile reply yapın
3. Gelen ID değerini kullanın (örn: `-1003184032013`)

</details>

#### 7. Botu Başlatın
```bash
python main.py
```

## ⚙️ Yapılandırma

### 🔐 Temel Ayarlar
```env
# Telegram API
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=abcdef1234567890abcdef1234567890

# Bot Yönetimi
BOT_ADMIN_ID=987654321
HEDEF_KANALLAR=-1003184032013,-1002345678901

# Özellikler
GECMIS_TARAMA_AKTIF=false
ZORLA_GUNCELLEME_MODU=false
```

### 🎯 Gelişmiş Ayarlar
```env
# Performans
BENZERLIK_ORANI=0.35          # Benzerlik eşiği (0-1)
KELIME_ESLESME_ORANI=0.65     # Kelime eşleşme oranı
CACHE_TTL=168                 # Önbellek süresi (saat)
MAX_LOG_BOYUTU_MB=5          # Maksimum log dosya boyutu
REQUEST_TIMEOUT=15           # HTTP istek zaman aşımı
RATE_LIMIT_DELAY=0.5         # Rate limiting gecikmesi
```

## 🎮 Kullanım Kılavuzu

### 👑 Admin Komutları

| Komut | Açıklama | Örnek |
|-------|----------|-------|
| `/admin` | Tüm komutları listeler | `/admin` |
| `/durum` | Detaylı bot istatistikleri | `/durum` |
| `/ping` | Bağlantı testi | `/ping` |
| `/dbbilgi` | Veritabanı bilgileri | `/dbbilgi` |
| `/sonkayitlar` | Son 5 kitap kaydı | `/sonkayitlar` |
| `/logtemizle` | Log dosyasını temizler | `/logtemizle` |

### 📚 Otomatik İşlemler

Bot aşağıdaki durumlarda otomatik olarak çalışır:

1. **📁 Yeni Dosya Yüklendiğinde**
   - PDF/EPUB dosyalarını otomatik tanır
   - Dosya adını analiz eder
   - Uygun kitap bilgilerini arar

2. **📝 Mesaj Düzenlendiğinde**
   - Mevcut açıklamaları korur
   - Yeni linkleri algılar
   - Eksik bilgileri tamamlar

3. **🔗 Direkt Link Paylaşıldığında**
   - 1000Kitap, Kitapyurdu, Goodreads linklerini destekler
   - Direkt olarak ilgili sayfadan bilgi çeker

## 📁 Proje Yapısı

```
sekitap_bot/
├── 📄 main.py                # Ana uygulama ve event handler'lar
├── 📁 config/                # Konfigürasyon dosyaları
│   ├── 🔧 settings.py        # Bot ayarları ve ortam değişkenleri
│   └── 📋 constants.py       # Sabitler ve veri kalıpları
├── 📁 database/              # Veritabanı yönetimi
│   └── 🗄️ db_manager.py      # SQLite önbellek sistemi
├── 📁 scrapers/              # Web scraping modülleri
│   ├── 🔍 base_scraper.py    # Temel scraper sınıfı
│   ├── 📚 binkitap.py        # 1000Kitap scraper
│   ├── 🛒 kitapyurdu.py      # Kitapyurdu scraper
│   ├── 🌟 goodreads.py       # Goodreads scraper
├── 📁 services/              # İş mantığı katmanı
│   └── 📋 book_service.py    # Kitap arama ve veri işleme
├── 📁 handlers/              # Telegram event handler'ları
│   ├── 💬 message_handler.py # Mesaj işleme mantığı
│   └── 👑 admin_handler.py   # Admin komutları
├── 📁 parsers/               # Veri ayrıştırıcılar
│   └── 🔍 data_parser.py     # HTML/JSON parsing
├── 📁 utils/                 # Yardımcı araçlar
│   ├── 📝 text_utils.py      # Metin işleme fonksiyonları
│   └── 🔧 helpers.py         # Genel yardımcı fonksiyonlar
└── 📁 tests/                 # Test dosyaları
    └── 🧪 test_scrapers.py   # Scraper testleri
```

## 🔧 Geliştirici Rehberi

### 🚀 Yeni Scraper Ekleme

```python
from scrapers.base_scraper import BaseScraper

class YeniScraper(BaseScraper):
    def get_name(self) -> str:
        return "YeniKaynak"
    
    def search(self, query: str, direct_url: str = None) -> Optional[Dict[str, Any]]:
        # Arama mantığınızı buraya yazın
        # Detay sayfasını parse edin
        # Standart veri formatında döndürün
        return self._parse_detail_page(soup, link)
```

### 🧪 Test Etme

```bash
# Manuel scraper testi
python -c "from scrapers.kitapyurdu import KitapyurduScraper; s = KitapyurduScraper(); print(s.search('Suç ve Ceza'))"

# Tüm testleri çalıştırma
python -m pytest tests/
```

## 📊 Performans Metrikleri

| Metrik | Değer |
|--------|--------|
| **Arama Hızı** | ~2-5 saniye/kitap |
| **Önbellek Hit Rate** | %70-80 |
| **Veritabanı Boyutu** | 1000 kitap = ~2-3 MB |
| **Bellek Kullanımı** | < 100 MB |
| **CPU Kullanımı** | < 10% |

## 🔍 Algoritma Detayları

### 🧠 Benzerlik Algoritması

```python
# Çok aşamalı doğrulama sistemi
1. ISBN kontrolü (en güvenilir)
2. Direkt substring eşleşmesi
3. Levenshtein mesafesi benzerliği
4. Kelime kümesi eşleşme oranı
5. Türkçe karakter normalizasyonu
```

### 💾 Akıllı Önbellekleme

- **TTL Destekli**: 7 güne kadar önbellekleme
- **Anahtar Tabanlı**: Temizlenmiş kitap adı ile indeksleme
- **Otomatik Temizlik**: Süresi dolan kayıtların otomatik silinmesi

## 🐛 Sorun Giderme

<details>
<summary>❌ Sık Karşılaşılan Hatalar</summary>

### ModuleNotFoundError
```bash
# Çözüm: Bağımlılıkları yeniden yükleyin
pip install -r requirements.txt --force-reinstall
```

### API ID/Hash Hatası
- `.env` dosyasında tırnak işareti kullanmayın
- API değerlerinin doğruluğunu kontrol edin

### Kanal Erişim Hatası
- Bot hesabının kanala üye olduğundan emin olun
- Kanalda mesaj yazma izni olduğunu kontrol edin

### Rate Limiting
- `RATE_LIMIT_DELAY` değerini artırın
- Aynı anda çok fazla kanal taramayın

</details>

## 🔐 Güvenlik

- **API Anahtarları**: `.env` dosyasında saklanır, GitHub'a yüklenmez
- **Rate Limiting**: Web sitelerini korumak için otomatik gecikme
- **Hata Yönetimi**: Tüm hatalar loglanır, bot çökmeleri önlenir
- **Veri Doğrulama**: Tüm kullanıcı girişleri kontrol edilir

## 🤝 Katkıda Bulunma

1. **Fork** edin ⏳
2. **Feature branch** oluşturun (`git checkout -b feature/harikaOzellik`)
3. **Commit** edin (`git commit -m 'Harika özellik eklendi'`)
4. **Push** edin (`git push origin feature/harikaOzellik`)
5. **Pull Request** açın 🎉

### 📋 Katkı Kuralları
- Kodunuzu PEP 8 standartlarına uygun yazın
- Yeni scraper'lar için test ekleyin
- README.md dosyasını güncelleyin
- Commit mesajlarını açıklayıcı yazın

## 📄 Lisans

Bu proje **MIT Lisansı** altında lisanslanmıştır. Detaylar için [LICENSE](LICENSE) dosyasına bakın.

## 👨‍💻 Geliştirici Bilgileri

**Proje**: sEkitap Bot v9.3  
**Mimari**: Modüler Asenkron Tasarım  
**Versiyon**: 9.3  
**Son Güncelleme**: 2026

📧 **İletişim**: [seyhanyuksel@gmail.com](mailto:seyhanyuksel@gmail.com)  
🔗 **GitHub**: [@trepcan](https://github.com/trepcan)

## 🙏 Teşekkürler

- **[Telethon](https://github.com/LonamiWebs/Telethon)** - Telegram API kütüphanesi
- **[BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/)** - HTML parsing
- **[Cloudscraper](https://github.com/VeNoMouS/cloudscraper)** - CloudFlare bypass
- **[Python-dotenv](https://github.com/theskumar/python-dotenv)** - Ortam değişkenleri yönetimi

---

<div align="center">

### ⭐ Projeyi Beğendiyseniz Yıldız Vermeyi Unutmayın!

**[⭐ GitHub'da Yıldız Ver](https://github.com/trepcan/sekitap-bot)**

</div>

---

=======
**Not**: Bu bot eğitim ve kişisel kullanım amaçlıdır. Web scraping işlemleri sırasında ilgili sitelerin kullanım koşullarına ve robots.txt dosyalarına saygı gösterin.