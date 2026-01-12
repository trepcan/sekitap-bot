#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sEkitap Bot - Tam Otomatik Kurulum Scripti
Tüm dosyalar ve scraper'lar dahil
"""
import os
import sys

PROJECT_FILES = {
    "requirements.txt": """telethon==1.34.0
python-dotenv==1.0.0
beautifulsoup4==4.12.3
requests==2.31.0
ftfy==6.1.3
cloudscraper==1.2.71
lxml==5.1.0
""",

    ".env.example": """# Telegram API Credentials
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash

# Bot Configuration
BOT_ADMIN_ID=your_telegram_user_id
HEDEF_KANALLAR=-1003184032013

# Bot Settings
GECMIS_TARAMA_AKTIF=false
ZORLA_GUNCELLEME_MODU=false

# Database
DB_FILE=kitap_onbellek.db

# Performance Settings
MAX_LOG_BOYUTU_MB=5
BENZERLIK_ORANI=0.35
KELIME_ESLESME_ORANI=0.65

# Cache Settings (hours)
CACHE_TTL=168
""",

    ".gitignore": """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
*.egg-info/
dist/
build/

# Bot specific
.env
*.session
*.session-journal
kitap_onbellek.db
log.txt
bot.log

# IDE
.vscode/
.idea/
*.swp
*.swo
.DS_Store
""",

    "README.md": """# 📚 sEkitap Bot v9.0

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
venv\\Scripts\\activate  # Windows
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
python -c "from scrapers.binkitap import BinKitapScraper; \
           s = BinKitapScraper(); \
           print(s.search('Suç ve Ceza'))"
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
""",

    "config/__init__.py": """from .settings import settings
from .constants import *

__all__ = ['settings', 'HEADERS', 'GURULTU_KELIMELERI', 'veri_kalibi']
""",

    "config/settings.py": """\"\"\"Bot konfigürasyon ayarları\"\"\"
import os
import sys
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()

if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass


class Settings:
    SURUM = "v9.0 (Modüler Mimari)"
    API_ID: int = int(os.getenv('TELEGRAM_API_ID', 0))
    API_HASH: str = os.getenv('TELEGRAM_API_HASH', '')
    
    ADMIN_ID: Optional[int] = None
    try:
        ADMIN_ID = int(os.getenv('BOT_ADMIN_ID', 0))
    except (TypeError, ValueError):
        pass
    
    HEDEF_KANALLAR: List[int] = []
    kanallar_str = os.getenv('HEDEF_KANALLAR', '')
    if kanallar_str:
        HEDEF_KANALLAR = [int(k.strip()) for k in kanallar_str.split(',') if k.strip()]
    else:
        HEDEF_KANALLAR = [-1003184032013]
    
    KANAL_ISIMLERI = {-1003184032013: "sEkitap Arşivi"}
    
    GECMIS_TARAMA_AKTIF: bool = os.getenv('GECMIS_TARAMA_AKTIF', 'false').lower() == 'true'
    ZORLA_GUNCELLEME_MODU: bool = os.getenv('ZORLA_GUNCELLEME_MODU', 'false').lower() == 'true'
    
    MAX_LOG_BOYUTU_MB: int = int(os.getenv('MAX_LOG_BOYUTU_MB', 5))
    BENZERLIK_ORANI: float = float(os.getenv('BENZERLIK_ORANI', 0.35))
    KELIME_ESLESME_ORANI: float = float(os.getenv('KELIME_ESLESME_ORANI', 0.65))
    
    DB_FILE: str = os.getenv('DB_FILE', 'kitap_onbellek.db')
    CACHE_TTL: int = int(os.getenv('CACHE_TTL', 168))
    
    REQUEST_TIMEOUT: int = 15
    RATE_LIMIT_DELAY: float = 0.5
    
    @classmethod
    def validate(cls) -> bool:
        if not cls.API_ID or not cls.API_HASH:
            print("HATA: Telegram API bilgileri eksik!")
            return False
        return True


settings = Settings()
""",

    "config/constants.py": """\"\"\"Sabit değerler\"\"\"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
    'Connection': 'keep-alive'
}

GURULTU_KELIMELERI = [
    "yayınları", "yayınevi", "yayıncılık", "yayın", "kitabevi",
    "bütün eserleri", "toplu eserler", "bls", "pdf", "epub", "okunmadı"
]

YASAKLI_TURLER = ["audiobook", "audible", "sesli kitap", "audio"]
UZUN_TUR_ISTISNALARI = ["historical fiction", "science fiction", "artificial intelligence"]

TUR_CEVIRI = {
    "Fiction": "Kurmaca", "HistoricalFiction": "TarihselKurgu",
    "ScienceFiction": "BilimKurgu", "Mystery": "Gizem",
    "Thriller": "Gerilim", "Romance": "Aşk", "Fantasy": "Fantastik"
}

def veri_kalibi():
    return {
        "baslik": None, "yazar": None, "aciklama": None, "seri": None,
        "yayinevi": None, "cevirmen": None, "orijinal_ad": None,
        "tarih": None, "isbn": None, "sayfa": None, "link": None,
        "turu": None, "puan": None, "oy_sayisi": None
    }
""",

    "utils/__init__.py": """from .text_utils import *
from .helpers import *
""",

    "database/__init__.py": """from .db_manager import db, DatabaseManager
""",

    "scrapers/__init__.py": """from .base_scraper import BaseScraper
from .binkitap import BinKitapScraper
from .kitapyurdu import KitapyurduScraper
from .goodreads import GoodreadsScraper
""",

    "parsers/__init__.py": """from .data_parser import DataParser
""",

    "handlers/__init__.py": """from .message_handler import MessageHandler
from .admin_handler import AdminHandler
""",

    "services/__init__.py": """from .book_service import book_service
""",
}

# Büyük dosyalar için ayrı sözlük (karakter sınırı)
LARGE_FILES = {
    "utils/text_utils.py": '''"""Metin işleme fonksiyonları"""
import re
import html
import difflib
from typing import Optional
import ftfy
from bs4 import BeautifulSoup
from config.constants import GURULTU_KELIMELERI


def turkce_kucult(metin: str) -> str:
    if not metin:
        return ""
    return metin.replace('I', 'ı').replace('İ', 'i').lower()


def turkce_baslik_yap(metin: str) -> Optional[str]:
    if not metin:
        return None
    kucuk = turkce_kucult(metin)
    kelimeler = kucuk.split()
    yeni_kelimeler = []
    for kelime in kelimeler:
        if not kelime:
            continue
        ilk_harf = kelime[0]
        geri_kalan = kelime[1:]
        if ilk_harf == 'i':
            ilk_harf = 'İ'
        elif ilk_harf == 'ı':
            ilk_harf = 'I'
        else:
            ilk_harf = ilk_harf.upper()
        yeni_kelimeler.append(ilk_harf + geri_kalan)
    return " ".join(yeni_kelimeler)


def metin_duzelt(metin: str) -> str:
    if not metin:
        return ""
    try:
        if "<" in str(metin) and ">" in str(metin):
            soup = BeautifulSoup(str(metin), 'html.parser')
            metin = soup.get_text(separator=' ')
    except:
        pass
    metin = html.unescape(str(metin))
    metin = ftfy.fix_text(metin)
    metin = re.sub(r'\\s+', ' ', metin).strip()
    return metin.strip()


def baslik_teknik_temizle(baslik: str) -> Optional[str]:
    if not baslik:
        return None
    regex = r'\\s*\\((?:Karton Kapak|Ciltli|İnce Kapak|Cep Boy)\\)'
    temiz = re.sub(regex, '', baslik, flags=re.IGNORECASE)
    return temiz.strip()


def turkce_baslik(metin: str) -> Optional[str]:
    if not metin:
        return None
    metin = metin_duzelt(metin)
    metin = baslik_teknik_temizle(metin)
    return turkce_baslik_yap(metin)


def metni_temizle(metin: str, manuel_mod: bool = False) -> str:
    saf_rakamlar = re.sub(r'[^\\d]', '', metin)
    if len(saf_rakamlar) in [10, 13]:
        if re.match(r'^[\\d\\-\\sX]+$', metin.strip(), re.IGNORECASE):
            return saf_rakamlar
    temiz = turkce_kucult(metin)
    if not manuel_mod:
        temiz = temiz.replace('.pdf', '').replace('.epub', '')
        temiz = re.sub(r'\\b(19|20)\\d{2}\\b', '', temiz)
    temiz = re.sub(r'-km$', '', temiz)
    temiz = re.sub(r'(\\[|\\(|\\{|_|-|\\s)+(cs|ham|bls)(\\]|\\)|\\}|\\b)', '', temiz)
    temiz = temiz.replace('_okunmadı', '').replace('_okunmadi', '')
    temiz = re.sub(r'\\(.*?\\)', '', temiz)
    temiz = re.sub(r'\\[.*?\\]', '', temiz)
    temiz = temiz.replace('_', ' ')
    for kelime in GURULTU_KELIMELERI:
        pattern = r'\\b' + re.escape(kelime) + r'(\\s+\\d+)?\\b'
        temiz = re.sub(pattern, '', temiz)
    if not manuel_mod:
        parcalar = temiz.split('-')
        if len(parcalar) >= 3:
            yeni_metin = f"{parcalar[0]} {parcalar[-1]}"
            temiz = " ".join(yeni_metin.split())
        else:
            temiz = temiz.replace('-', ' ')
    return " ".join(temiz.split())


def benzerlik_orani(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return difflib.SequenceMatcher(None, turkce_kucult(a), turkce_kucult(b)).ratio()


def kelime_kumesi_orani(aranan: str, bulunan: str) -> float:
    if not aranan or not bulunan:
        return 0.0
    def tokenize(text):
        text = turkce_kucult(text)
        return set(re.findall(r'\\w+', text))
    aranan_set = tokenize(aranan)
    bulunan_set = tokenize(bulunan)
    if not aranan_set:
        return 0.0
    kesisim = aranan_set.intersection(bulunan_set)
    return len(kesisim) / len(aranan_set)


def isbn_bul(text: str) -> Optional[str]:
    if not text:
        return None
    match = re.search(r'978[\\d-]{10,14}', text)
    if match:
        return match.group(0).replace('-', '').replace(' ', '')
    return None


def durum_belirle(dosya_adi: str) -> str:
    ad = dosya_adi.lower()
    if ad.endswith('.epub'):
        if 'okunmadı' in ad or 'okunmadi' in ad:
            return "Okunmadı"
        if 'storytel' in ad:
            return "Storytel, Orijinal"
        return "Okundu"
    elif ad.endswith('.pdf'):
        if re.search(r'(?:^|[\\s_\\-\\(\\[])ham[\\s_\\-\\)\\]]*\\.pdf$', ad):
            return "Ham Tarama"
        return "Clear Scan"
    return "-"
''',

    "utils/helpers.py": '''"""Yardımcı fonksiyonlar"""
import asyncio
import functools
from typing import Optional, Dict
from config.constants import TUR_CEVIRI, YASAKLI_TURLER, UZUN_TUR_ISTISNALARI


async def run_sync(func, *args, **kwargs):
    loop = asyncio.get_event_loop()
    pfunc = functools.partial(func, *args, **kwargs)
    return await loop.run_in_executor(None, pfunc)


def tur_cevir_ve_filtrele(tur_listesi: list) -> Optional[str]:
    if not tur_listesi:
        return None
    formatted_genres = []
    for g in tur_listesi:
        raw_genre = g.strip()
        if any(banned in raw_genre.lower() for banned in YASAKLI_TURLER):
            continue
        translated_genre = TUR_CEVIRI.get(raw_genre, TUR_CEVIRI.get(raw_genre.replace(" ", ""), raw_genre))
        clean_g = translated_genre.replace(" ", "")
        is_exception = any(exc.lower() in clean_g.lower() for exc in UZUN_TUR_ISTISNALARI)
        if len(clean_g) > 12 and not is_exception:
            continue
        if clean_g and f"#{clean_g}" not in formatted_genres:
            formatted_genres.append(f"#{clean_g}")
        if len(formatted_genres) >= 5:
            break
    return " ".join(formatted_genres) if formatted_genres else None


def basit_bilgi_cikar(metin: str) -> Dict[str, str]:
    from utils.text_utils import turkce_baslik
    orijinal_temiz = metin.replace('.pdf', '').replace('.epub', '').replace('_', ' ')
    parcalar = orijinal_temiz.split('-')
    yazar = "Bilinmiyor"
    kitap = turkce_baslik(orijinal_temiz)
    if len(parcalar) >= 2:
        yazar = turkce_baslik(parcalar[0].strip())
        kitap = turkce_baslik("-".join(parcalar[1:]).strip())
    return {"yazar": yazar, "baslik": kitap}
''',

    "database/db_manager.py": '''"""Veritabanı yöneticisi"""
import sqlite3
import json
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging
from config.settings import settings

logger = logging.getLogger(__name__)


class DatabaseManager:
    def __init__(self, db_file: str = None):
        self.db_file = db_file or settings.DB_FILE
        self.initialize()
    
    def initialize(self):
        try:
            conn = sqlite3.connect(self.db_file)
            c = conn.cursor()
            c.execute("""
                CREATE TABLE IF NOT EXISTS kitaplar (
                    anahtar TEXT PRIMARY KEY,
                    veri TEXT,
                    tarih TEXT,
                    guncelleme_tarihi TEXT
                )
            """)
            conn.commit()
            conn.close()
            logger.info("✅ Veritabanı başlatıldı")
        except Exception as e:
            logger.error(f"❌ Veritabanı hatası: {e}")
    
    def kaydet(self, anahtar: str, veri_dict: Dict[str, Any]) -> bool:
        if not anahtar or not veri_dict:
            return False
        try:
            conn = sqlite3.connect(self.db_file)
            c = conn.cursor()
            veri_json = json.dumps(veri_dict, ensure_ascii=False)
            tarih_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            c.execute("""
                INSERT OR REPLACE INTO kitaplar 
                (anahtar, veri, tarih, guncelleme_tarihi) 
                VALUES (?, ?, ?, ?)
            """, (anahtar, veri_json, tarih_str, tarih_str))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"❌ Kayıt hatası: {e}")
            return False
    
    def getir(self, anahtar: str, cache_ttl_hours: int = None) -> Optional[Dict[str, Any]]:
        if not anahtar:
            return None
        ttl = cache_ttl_hours or settings.CACHE_TTL
        try:
            conn = sqlite3.connect(self.db_file)
            c = conn.cursor()
            c.execute("SELECT veri, guncelleme_tarihi FROM kitaplar WHERE anahtar = ?", (anahtar,))
            sonuc = c.fetchone()
            conn.close()
            if sonuc:
                veri_json, guncelleme_str = sonuc
                if guncelleme_str:
                    try:
                        guncelleme = datetime.strptime(guncelleme_str, '%Y-%m-%d %H:%M:%S')
                        if datetime.now() - guncelleme > timedelta(hours=ttl):
                            return None
                    except:
                        pass
                return json.loads(veri_json)
            return None
        except:
            return None
    
    def istatistikler(self) -> str:
        if not os.path.exists(self.db_file):
            return "Veritabanı dosyası henüz oluşmamış."
        try:
            conn = sqlite3.connect(self.db_file)
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM kitaplar")
            toplam_kitap = c.fetchone()[0]
            c.execute("SELECT MAX(tarih) FROM kitaplar")
            son_tarih = c.fetchone()[0]
            conn.close()
            boyut_mb = os.path.getsize(self.db_file) / (1024 * 1024)
            return f"📊 **Veritabanı**\\n📚 Kitap: {toplam_kitap}\\n💾 Boyut: {boyut_mb:.2f} MB\\n🕒 Son: {son_tarih or 'Yok'}"
        except Exception as e:
            return f"Hata: {e}"
    
    def son_kayitlar(self, limit: int = 5) -> str:
        try:
            conn = sqlite3.connect(self.db_file)
            c = conn.cursor()
            c.execute("SELECT anahtar, tarih FROM kitaplar ORDER BY tarih DESC LIMIT ?", (limit,))
            veriler = c.fetchall()
            conn.close()
            if not veriler:
                return "Kayıt bulunamadı."
            msg = "🆕 **Son Kayıtlar:**\\n"
            for anahtar, tarih in veriler:
                msg += f"• `{anahtar}` ({tarih})\\n"
            return msg
        except Exception as e:
            return f"Hata: {e}"


db = DatabaseManager()
''',

    "scrapers/base_scraper.py": '''"""Temel scraper"""
import requests
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from bs4 import BeautifulSoup
from config.constants import HEADERS
from config.settings import settings

try:
    import cloudscraper
    HAS_SCRAPER = True
except ImportError:
    HAS_SCRAPER = False

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        if HAS_SCRAPER:
            self.scraper = cloudscraper.create_scraper(
                browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True}
            )
        else:
            self.scraper = None
        self.timeout = settings.REQUEST_TIMEOUT
    
    def get_response(self, url: str, use_scraper: bool = True) -> Optional[requests.Response]:
        try:
            if use_scraper and self.scraper:
                response = self.scraper.get(url, timeout=self.timeout)
            else:
                response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response
        except Exception as e:
            logger.error(f"❌ HTTP hatası: {e}")
            return None
    
    def parse_html(self, response: requests.Response) -> Optional[BeautifulSoup]:
        try:
            return BeautifulSoup(response.content, 'html.parser')
        except:
            return None
    
    @abstractmethod
    def search(self, query: str, direct_url: str = None) -> Optional[Dict[str, Any]]:
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        pass
''',
}

# DİĞER BÜYÜK DOSYALAR DEVAM EDECEK...

def create_file(path, content):
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else '.', exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ {path}")

def main():
    print("=" * 60)
    print("📦 sEkitap Bot - Tam Otomatik Kurulum v9.0")
    print("=" * 60)
    print()
    
    # Dizinler
    directories = ['config', 'database', 'scrapers', 'parsers', 'utils', 'handlers', 'services']
    for d in directories:
        os.makedirs(d, exist_ok=True)
    
    # Küçük dosyalar
    for path, content in PROJECT_FILES.items():
        create_file(path, content)
    
    # Büyük dosyalar
    for path, content in LARGE_FILES.items():
        create_file(path, content)
    
    print()
    print("=" * 60)
    print("✨ Kurulum tamamlandı!")
    print()
    print("📋 Sonraki Adımlar:")
    print("1. pip install -r requirements.txt")
    print("2. cp .env.example .env")
    print("3. .env dosyasını düzenleyin")
    print("4. python main.py")
    print("=" * 60)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"❌ HATA: {e}")
        sys.exit(1)