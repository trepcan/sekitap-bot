
# 📚 Sekitap Bot

Telegram kanallarındaki PDF ve EPUB kitaplarını otomatik olarak tanımlayan, kitap bilgilerini Kitapyurdu, Goodreads ve 1000Kitap'tan çekip mesajlara ekleyen akıllı bot.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)  
![Telethon](https://img.shields.io/badge/Telethon-1.34+-green.svg)  
![License](https://img.shields.io/badge/license-MIT-orange.svg)  

## 🎯 Özellikler


### 📖 Kitap Tanıma ve Zenginleştirme
```
- ✅ **Otomatik Kitap Tespiti**: PDF ve EPUB dosyalarını otomatik algılar
- ✅ **Çoklu Kaynak Desteği**: Kitapyurdu, Goodreads, 1000Kitap
- ✅ **Akıllı Arama**: 5 aşamalı arama algoritması ile yüksek bulma oranı
- ✅ **Zenginleştirme**: ISBN, puan, seri bilgisi, orijinal ad, çevirmen
- ✅ **Fallback Mekanizması**: Bulunamayan kitaplar için dosya adından bilgi çıkarma
```
### 🤖 Otomasyon

- ✅ **Eski Mesajları Tarama**: Kanaldaki tüm eski mesajları geriye dönük işleyebilir
- ✅ **Yeni Mesajları İzleme**: Yeni eklenen kitapları anında işler
- ✅ **Zorla Güncelleme**: Zaten işlenmiş mesajları tekrar güncelleyebilir
- ✅ **İstatistik Takibi**: İşlenen, bulunan, bulunamayan kitap sayıları

```
### 📊 Detaylı Bilgiler
✍️ Yazar: C. S. Lewis  
📖 Kitap: Narnia Günlükleri 3 / At ve Çocuk  
📚 Seri: Narnia Günlükleri #3  
📂 Tür: EPUB  
📊 Durum: Okunmadı  
🏢 Yayınevi: Doğan Çocuk  
📅 Yayın Tarihi: 2016  
📄 Sayfa: 248  
🔢 ISBN: 9789752896468  
🌍 Çevirmen: Altan Çetin  
📝 Orijinal Ad: The Horse and His Boy  
⭐ Puan: 4.16/5 (147234 oy)  

🏷 #Fantasy #Classics #ChildrensLit

ℹ️ Açıklama:
Narnia'nın Altın Çağı'nda geçen bu macera...

🌐 Kitapyurdu
```

---

## 📁 Proje Yapısı

```
sekitap-bot/  
├── main.py                    # Ana uygulama  
├── config/  
│   └── settings.py            # Konfigürasyon yönetimi  
├── database/  
│   └── db_manager.py          # SQLite veritabanı yönetimi  
├── handlers/  
│   └── message_handler.py     # Telegram mesaj işleyici  
├── scrapers/  
│   ├── base_scraper.py        # Temel scraper sınıfı  
│   ├── kitapyurdu.py          # Kitapyurdu scraper  
│   ├── goodreads.py  		   # Goodreads scraper  
│   └── binkitap.py 		   # 1000Kitap scraper  
├── services/  
│   └── book_service.py        # Kitap arama ve zenginleştirme servisi  
├── utils/  
│   └── text_utils.py          # Metin işleme yardımcıları  
├── requirements.txt           # Python bağımlılıkları  
└── README.md                  # Bu dosya  
```

---

## 🚀 Kurulum

### 1. Gereksinimleri Yükleyin

```bash
git clone https://github.com/trepcan/sekitap-bot.git
cd sekitap-bot
pip install -r requirements.txt
```

### 2. Telegram API Bilgilerinizi Alın

1. [my.telegram.org](https://my.telegram.org) adresine gidin
2. **API development tools** bölümünden `api_id` ve `api_hash` alın

### 3. Konfigürasyon Dosyasını Oluşturun

`config/settings.py` dosyasını düzenleyin:

```python
class Settings:
    # Telegram API bilgileri
    API_ID = "12345678"  # Buraya kendi api_id'nizi yazın
    API_HASH = "abcdef1234567890"  # Buraya kendi api_hash'inizi yazın
    PHONE = "+905551234567"  # Telefon numaranız
    
    # Hedef kanal
    CHANNEL_USERNAME = "@kitapkanaliniz"  # Kendi kanalınız
    
    # Veritabanı
    DB_PATH = "data/books.db"
    
    # Scraper ayarları
    SCRAPERS = {
        "kitapyurdu": True,   # Ana kaynak
        "goodreads": True,    # Zenginleştirme
        "1000kitap": True     # Alternatif kaynak
    }
    
    # Arama ayarları
    SEARCH_TIMEOUT = 10  # Saniye
    MAX_RETRIES = 3
```

### 4. İlk Çalıştırma

```bash
python main.py
```

İlk çalıştırmada Telegram'dan gelen doğrulama kodunu girin.

---

## 🎮 Kullanım

### Komutlar

#### `/tara [limit]`
Kanaldaki eski mesajları geriye dönük tarar.

```
/tara              # Tüm mesajları tara
/tara 100          # Son 100 mesajı tara
```

#### `/istatistik`
İşlem istatistiklerini gösterir.

```
📊 İstatistikler:
✅ Toplam Taranan: 456
✅ Bulunan: 389
❌ Bulunamayan: 67
🔄 Başarı Oranı: %85.3
```

#### `/zorla_guncelle [limit]`
Zaten işlenmiş mesajları tekrar günceller.

```
/zorla_guncelle         # Tümünü güncelle
/zorla_guncelle 50      # Son 50 mesajı güncelle
```

---

## 🔍 Akıllı Arama Algoritması

Bot, kitap bilgilerini bulmak için **5 aşamalı arama** kullanır:

### Aşama 1: Tam Sorgu
```
"Tess Gerritsen - Rizzoli & Isles 5 Rehine (Vanish).epub"
```

### Aşama 2: Basitleştirilmiş Sorgu
```
"Tess Gerritsen Rizzoli Isles 5 Rehine (Vanish)"
```

### Aşama 3: Parantez İçi + Yazar
```
"Vanish Tess Gerritsen"  ← En etkili!
```

### Aşama 4: Parantez İçi
```
"Vanish"
```

### Aşama 5: Temiz Sorgu
```
"Tess Gerritsen Rehine"
```

---

## 🎨 Zenginleştirme

### Kitapyurdu (Ana Kaynak)
- ✅ Yazar, Kitap adı, Açıklama
- ✅ Yayınevi, Yayın tarihi
- ✅ ISBN, Sayfa sayısı
- ✅ Link

### Goodreads (Zenginleştirme)
- ✅ Puan ve oy sayısı
- ✅ Seri bilgisi (Örn: "Narnia Günlükleri #3")
- ✅ Türler (Fantasy, Classics, etc.)
- ✅ Orijinal ad

### 1000Kitap (Alternatif)
- ✅ Türkçe açıklamalar
- ✅ Çevirmen bilgisi
- ✅ Orijinal ad

---

## 🛠️ Geliştirme

### Scraper Ekleme

Yeni bir scraper eklemek için `scrapers/base_scraper.py`'dan türetin:

```python
from scrapers.base_scraper import BaseScraper

class YeniScraper(BaseScraper):
    def __init__(self):
        super().__init__("YeniKaynak", "https://yenikaynak.com")
    
    def search(self, query: str):
        # Arama mantığınız
        return {
            "baslik": "...",
            "yazar": "...",
            "aciklama": "..."
        }
```

`book_service.py` içine ekleyin:

```python
self.scrapers['yenikaynak'] = YeniScraper()
```

---

## 📊 Veritabanı

SQLite veritabanı (`data/books.db`) şu tabloları içerir:

### `books` Tablosu
```sql
CREATE TABLE books (
    id INTEGER PRIMARY KEY,
    message_id INTEGER UNIQUE,
    file_name TEXT,
    title TEXT,
    author TEXT,
    isbn TEXT,
    source TEXT,
    found BOOLEAN,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

---

## 🐛 Hata Ayıklama

### Log Seviyeleri

```python
# config/settings.py
LOG_LEVEL = "DEBUG"  # DEBUG, INFO, WARNING, ERROR
```

### Log Dosyası

```bash
tail -f logs/bot.log
```

### Sık Karşılaşılan Sorunlar

#### Kitap Bulunamıyor
```python
# book_service.py içinde log kontrol edin:
logger.info(f"🔍 [1/5] Tam sorgu: {query[:60]}...")
```

#### Scraper Hatası
```bash
# Scraper'ı manuel test edin:
python -c "from scrapers.kitapyurdu_scraper import KitapyurduScraper; s = KitapyurduScraper(); print(s.search('Harry Potter'))"
```

---

## 🤝 Katkıda Bulunma

1. Fork yapın
2. Feature branch oluşturun (`git checkout -b feature/yeni-ozellik`)
3. Commit yapın (`git commit -am 'Yeni özellik eklendi'`)
4. Push edin (`git push origin feature/yeni-ozellik`)
5. Pull Request açın

---

## 📝 Yapılacaklar

- [ ] Google Books API desteği
- [ ] Kapak resmi indirme ve ekleme
- [ ] Çoklu kanal desteği
- [ ] Web dashboard
- [ ] Docker desteği
- [ ] Otomatik backup sistemi

---

## 📄 Lisans

Bu proje MIT lisansı altında lisanslanmıştır. Detaylar için [LICENSE](LICENSE) dosyasına bakın.

---

## 👤 Geliştirici

**Seyhan** - [@trepcan](https://github.com/trepcan)

---

## 🙏 Teşekkürler

- [Telethon](https://github.com/LonamiWebs/Telethon) - Telegram API
- [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/) - HTML parsing
- [Kitapyurdu](https://www.kitapyurdu.com) - Kitap veritabanı
- [Goodreads](https://www.goodreads.com) - Kitap puanları ve seriler
- [1000Kitap](https://1000kitap.com) - Türkçe kitap bilgileri

---


```

---

## 🎯 Ek: Badges ve Görsel

README'ye ekleyebileceğiniz ek badge'ler:

```markdown
![GitHub stars](https://img.shields.io/github/stars/trepcan/sekitap-bot)
![GitHub forks](https://img.shields.io/github/forks/trepcan/sekitap-bot)
![GitHub issues](https://img.shields.io/github/issues/trepcan/sekitap-bot)
![GitHub last commit](https://img.shields.io/github/last-commit/trepcan/sekitap-bot)
```
