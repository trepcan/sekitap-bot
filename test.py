from typing import Optional, Dict, Any
from urllib.parse import quote_plus
import logging
import re

from scrapers.base_scraper import BaseScraper
from parsers.data_parser import DataParser
from utils.text_utils import metin_duzelt, turkce_baslik, baslik_teknik_temizle, isbn_bul, benzerlik_orani
from config.constants import veri_kalibi
import logging
from typing import Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor
import asyncio
import re

from scrapers.kitapyurdu import KitapyurduScraper
from scrapers.goodreads import GoodreadsScraper
from scrapers.binkitap import BinKitapScraper
from utils.async_utils import run_sync
from utils.text_utils import metin_duzelt, benzerlik_orani
from utils.series_utils import translate_series_name, prefer_turkish_series
from config.constants import GURULTU_KELIMELERI


logger = logging.getLogger(__name__)


def test_search(self, query: str):
    """Debug arama testi"""
    print(f"\n🧪 TEST: {query}")
    
    from urllib.parse import quote_plus
    encoded_query = quote_plus(query)
    url = f"{self.BASE_URL}/index.php?route=product/search&filter_name={encoded_query}"
    
    print(f"URL: {url}\n")
    
    try:
        response = self.session.get(url, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Content Length: {len(response.content)}")
        
        # Dosyaya kaydet
        with open('debug_search.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        print("✅ debug_search.html kaydedildi\n")
        
        # Selektörleri test et
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')
        
        print("🔍 Selektör Testleri:")
        selektorler = [
            '.product-cr',
            '.product-item',
            '.book-item',
            '[data-product-id]',
            'div.product',
            'article.product',
            '.product-card',
            'li[data-product]',
            'a[href*="/kitap/"]'
        ]
        
        for sel in selektorler:
            sonuclar = soup.select(sel)
            if sonuclar:
                print(f"✅ {sel}: {len(sonuclar)} sonuç")
                # İlk sonucun HTML'ini göster
                print(f"   HTML: {str(sonuclar[0])[:200]}\n")
            else:
                print(f"❌ {sel}: 0 sonuç")
        
    except Exception as e:
        print(f"❌ Hata: {e}")

# test.py'de çalıştır:
scraper = KitapyurduScraper()
scraper.test_search("Neksus")