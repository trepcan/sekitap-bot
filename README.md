# 📚 sEkitap Bot v9.0

🤖 Telegram kanallarındaki PDF/EPUB kitap dosyalarını otomatik olarak tarayan ve detaylı bilgilerini ekleyen gelişmiş bot.

## ✨ Özellikler

- ✅ **Çoklu Kaynak Desteği**: 1000Kitap, Kitapyurdu, Amazon TR, Goodreads, İdefix, BKM Kitap, Storytel
- ✅ **Akıllı Arama**: Benzerlik algoritması ile doğru eşleştirme
- ✅ **Goodreads Zenginleştirme**: Puan, tür, seri bilgileri
- ✅ **Veritabanı Önbellekleme**: TTL destekli SQLite cache
- ✅ **Canlı Mod**: Yeni mesajları otomatik işle
- ✅ **Geçmiş Tarama**: Eski mesajları toplu işle
- ✅ **Admin Panel**: Detaylı istatistik ve yönetim komutları
- ✅ **Modüler Mimari**: Kolay genişletilebilir yapı

## 🚀 Hızlı Başlangıç

### 1. Projeyi Klonlayın
\`\`\`bash
git clone https://github.com/KULLANICI_ADINIZ/sekitap-bot.git
cd sekitap-bot
\`\`\`

### 2. Sanal Ortam Oluşturun (Önerilen)
\`\`\`bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# veya
venv\Scripts\activate  # Windows
\`\`\`

### 3. Bağımlılıkları Yükleyin
\`\`\`bash
pip install -r requirements.txt
\`\`\`

### 4. Konfigürasyon
\`\`\`bash
cp .env.example .env
\`\`\`

`.env` dosyasını düzenleyin:
\`\`\`env
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=abcdef1234567890abcdef1234567890
BOT_ADMIN_ID=987654321
HEDEF_KANALLAR=-1003184032013,-1002345678901
\`\`\`

### 5. Telegram API Bilgileri

1. https://my.telegram.org/apps adresine gidin
2. Giriş yapın
3. "Create Application" ile yeni uygulama oluşturun
4. **API ID** ve **API Hash** değerlerini `.env` dosyasına kaydedin

### 6. Admin ID Bulma

Telegram'da [@userinfobot](https://t.me/userinfobot) botuna `/start` gönderin.

### 7. Kanal ID Bulma

- Kanaldan herhangi bir mesajı kendinize forward edin
- [@userinfobot](https://t.me/userinfobot) ile forward ettiğiniz mesaja reply yapın
- Kanal ID'sini alın (örn: `-1003184032013`)

### 8. Botu Çalıştırın
\`\`\`bash
python main.py
\`\`\`

## 🎮 Kullanım

### Admin Komutları

| Komut | Açıklama |
|-------|----------|
| `/admin` | Yardım menüsü |
| `/durum` | Detaylı bot istatistikleri |
| `/ping` | Bağlantı testi |
| `/dbbilgi` | Veritabanı bilgileri |
| `/sonkayitlar` | Son eklenen 5 kitap |
| `/logtemizle` | Log dosyasını temizle |

### Otomatik İşlemler

Bot şu durumlarda çalışır:
- ✅ Yeni kitap dosyası yüklendiğinde
- ✅ Mesaj düzenlendiğinde
- ✅ Direkt kitap linki gönderildiğinde

## ⚙️ Konfigürasyon

### .env Ayarları

\`\`\`env
# Geçmiş mesajları tara
GECMIS_TARAMA_AKTIF=true

# Zaten işlenmiş mesajları güncelle
ZORLA_GUNCELLEME_MODU=false

# Önbellek geçerlilik süresi (saat)
CACHE_TTL=168

# Benzerlik eşiği (0-1)
BENZERLIK_ORANI=0.35
KELIME_ESLESME_ORANI=0.65
\`\`\`

## 📁 Proje Yapısı

\`\`\`
sekitap_bot/
├── main.py                  # Ana uygulama
├── config/                  # Konfigürasyon
│   ├── settings.py          # Bot ayarları
│   └── constants.py         # Sabitler
├── database/                # Veritabanı
│   └── db_manager.py        # SQLite yöneticisi
├── scrapers/                # Web scraper'lar
│   ├── base_scraper.py      # Temel sınıf
│   ├── binkitap.py          # 1000Kitap
│   ├── kitapyurdu.py        # Kitapyurdu
│   ├── amazon.py            # Amazon TR
│   ├── goodreads.py         # Goodreads
│   ├── idefix.py            # İdefix
│   ├── bkm.py               # BKM Kitap
│   └── storytel.py          # Storytel
├── parsers/                 # Veri işleme
│   └── data_parser.py       # HTML/JSON parser
├── services/                # İş mantığı
│   └── book_service.py      # Kitap arama servisi
├── handlers/                # Telegram handler'lar
│   ├── message_handler.py   # Mesaj işleyici
│   └── admin_handler.py     # Admin komutları
└── utils/                   # Yardımcılar
    ├── text_utils.py        # Metin işleme
    └── helpers.py           # Genel fonksiyonlar
\`\`\`

## 🔧 Geliştirme

### Yeni Scraper Ekleme

\`\`\`python
from scrapers.base_scraper import BaseScraper

class YeniScraper(BaseScraper):
    def get_name(self):
        return "YeniKaynak"
    
    def search(self, query, direct_url=None):
        # Arama mantığı
        pass
\`\`\`

### Test

\`\`\`bash
# Manuel test
python -c "from scrapers.binkitap import BinKitapScraper;            s = BinKitapScraper();            print(s.search('Suç ve Ceza'))"
\`\`\`

## 🐛 Sorun Giderme

### "ModuleNotFoundError"
\`\`\`bash
pip install -r requirements.txt
\`\`\`

### "API ID/Hash hatası"
`.env` dosyasını kontrol edin, tırnak işareti kullanmayın.

### "Kanal erişim hatası"
Botun hesabının kanala üye olması gerekir.

## 📊 Performans

- **Arama Hızı**: ~2-5 saniye/kitap
- **Önbellek Hit Rate**: %70-80
- **Veritabanı**: 1000 kitap = ~2-3 MB

## 🤝 Katkıda Bulunma

1. Fork edin
2. Feature branch oluşturun (`git checkout -b feature/yeniOzellik`)
3. Commit edin (`git commit -m 'Yeni özellik eklendi'`)
4. Push edin (`git push origin feature/yeniOzellik`)
5. Pull Request açın

## 📝 Lisans

MIT License

## 👨‍💻 Geliştirici

**sEkitap Bot v9.0** - Modüler Mimari  
📧 İletişim: seyhanyuksel@gmail.com

## 🙏 Teşekkürler

- Telethon kütüphanesi
- BeautifulSoup4
- Cloudscraper
