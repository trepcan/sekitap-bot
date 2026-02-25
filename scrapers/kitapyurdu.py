from typing import Optional, Dict, Any
from urllib.parse import quote_plus
import logging
import re
import time

from scrapers.base_scraper import BaseScraper
from parsers.data_parser import DataParser
from utils.text_utils import metin_duzelt, turkce_baslik, baslik_teknik_temizle, isbn_bul, benzerlik_orani
from config.constants import veri_kalibi
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# BaseScraper'dan HAS_SCRAPER'ı al
try:
    import cloudscraper
    HAS_SCRAPER = True
except ImportError:
    HAS_SCRAPER = False


class KitapyurduScraper(BaseScraper):
    """Kitapyurdu.com scraper"""
    
    BASE_URL = "https://www.kitapyurdu.com"
    
    def get_name(self) -> str:
        return "Kitapyurdu"
    
    def fetch_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Verilen URL'den direkt kitap bilgilerini çek (arama yapmadan)
        
        Args:
            url: Kitap detay sayfası URL'si
            
        Returns:
            Dict veya None
        """
        try:
            logger.info(f"🔗 Direkt URL'den çekiliyor: {url[:80]}...")
            
            response = self.get_response(url, use_scraper=False)
            if not response:
                logger.error("❌ URL'den yanıt alınamadı")
                return None
            
            # Encoding ayarla
            try:
                html_content = response.content.decode('utf-8')
            except:
                html_content = response.content.decode('iso-8859-9', errors='replace')
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Direkt parse et
            return self._parse_detail_page(soup, url)
            
        except Exception as e:
            logger.error(f"❌ Kitapyurdu fetch_by_url hatası: {e}")
            return None
    
    def fetch_by_id(self, book_id: str) -> Optional[Dict[str, Any]]:
        """
        Kitap ID'si ile direkt kitap bilgilerini çek
        
        Args:
            book_id: Kitapyurdu kitap ID'si (örn: "82977")
            
        Returns:
            Dict veya None
        """
        # ID'den URL oluştur - Yeni yapı: /kitap/slug/id.html
        url = f"{self.BASE_URL}/kitap/-/{book_id}.html"
        return self.fetch_by_url(url)
    
    @staticmethod
    def extract_id_from_url(url: str) -> Optional[str]:
        """
        URL'den kitap ID'sini çıkar
        
        Yeni URL Yapısı: 
            https://www.kitapyurdu.com/kitap/kisot/743578.html -> "743578"
            https://www.kitapyurdu.com/kitap/-/<id>.html -> "<id>"
        """
        if not url:
            return None
        
        # Yeni Pattern: /kitap/herhangi-bir-slug/12345.html
        match = re.search(r'/kitap/[a-zA-Z0-9\-_]+/(\d+)\.html', url)
        if match:
            return match.group(1)
        
        # Alternatif: sadece sayı.html (eski yapı için geriye dönük uyumluluk)
        match = re.search(r'/(\d+)\.html$', url)
        if match:
            return match.group(1)
        
        # Query string'de id parametresi var mı?
        match = re.search(r'[?&]id=(\d+)', url)
        if match:
            return match.group(1)
        
        return None
    
    def search_by_isbn(self, isbn: str) -> Optional[Dict[str, Any]]:
        """
        ISBN ile direkt arama yap
        """
        if not isbn:
            return None
        
        try:
            isbn_clean = isbn.replace('-', '').strip()
            
            if len(isbn_clean) < 10:
                logger.warning(f"⚠️ Geçersiz ISBN: {isbn}")
                return None
            
            logger.info(f"🔢 ISBN ile aranıyor: {isbn_clean}")
            
            # Kitapyurdu ISBN arama URL'si
            url = f"{self.BASE_URL}/index.php?route=product/search&filter_isbn={isbn_clean}"
            
            response = self.get_response(url, use_scraper=False)
            if not response:
                logger.warning("⚠️ ISBN araması başarısız (yanıt yok)")
                return None
            
            # Encoding ayarla
            try:
                html_content = response.content.decode('utf-8')
            except:
                html_content = response.content.decode('iso-8859-9', errors='replace')
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Çoklu selektör deneme
            kitap = self._find_first_product(soup)
            if not kitap:
                logger.warning("⚠️ ISBN araması sonucu boş")
                return None
            
            link_elem = kitap.select_one('a')
            if not link_elem or 'href' not in link_elem.attrs:
                logger.warning("⚠️ Arama sonucunda link bulunamadı")
                return None
            
            link = link_elem['href']
            # Göreceli URL'yi tam URL'ye çevir
            link = self._normalize_url(link)
            
            logger.info(f"✅ ISBN sonucu bulundu: {link}")
            
            # Detay sayfasını çek
            return self.fetch_by_url(link)
            
        except Exception as e:
            logger.error(f"❌ ISBN araması hatası: {e}")
            return None
    
    def _normalize_url(self, url: str) -> str:
        """Göreceli URL'yi tam URL'ye çevir"""
        if url.startswith('http'):
            return url
        elif url.startswith('/'):
            return self.BASE_URL + url
        else:
            return self.BASE_URL + '/' + url
    
    def _find_first_product(self, soup) -> Optional[Any]:
        """Arama sonuçlarından ilk ürünü bul - çoklu selektör desteği"""
        selektorler = [
            '.product-cr',           # Eski klasik selektör
            '.product-item',         # Yeni olası yapı
            'div[data-product-id]',  # data-attribute ile
            '.product-grid > div',   # Grid içindeki div
            '.search-results .product',  # Search results container
            '.product-card',         # Card yapısı
            '.item.product',         # Item class
            '.products .item',       # Products container
            '.product-list .product', # List görünümü
            '.catalog-products .product', # Katalog yapısı
        ]
        
        for sel in selektorler:
            try:
                sonuclar = soup.select(sel)
                if sonuclar and len(sonuclar) > 0:
                    logger.debug(f"✅ Selektör '{sel}' ile {len(sonuclar)} sonuç bulundu")
                    return sonuclar[0]
            except Exception as e:
                logger.debug(f"Selektör '{sel}' hatası: {e}")
                continue
        
        return None
    
    def _find_all_products(self, soup) -> list:
        """Arama sonuçlarından tüm ürünleri bul - çoklu selektör desteği"""
        selektorler = [
            '.product-cr',           # Eski klasik selektör
            '.product-item',         # Yeni olası yapı
            'div[data-product-id]',  # data-attribute ile
            '.product-grid > div',   # Grid içindeki div
            '.search-results .product',  # Search results container
            '.product-card',         # Card yapısı
            '.item.product',         # Item class
            '.products .item',       # Products container
            '.product-list .product', # List görünümü
            '.catalog-products .product', # Katalog yapısı
        ]
        
        for sel in selektorler:
            try:
                sonuclar = soup.select(sel)
                if sonuclar and len(sonuclar) > 0:
                    logger.info(f"🔍 Selektör '{sel}' ile {len(sonuclar)} sonuç bulundu")
                    return sonuclar
            except Exception as e:
                logger.debug(f"Selektör '{sel}' hatası: {e}")
                continue
        
        return []
    
    def search(self, query: str, direct_url: str = None) -> Optional[Dict[str, Any]]:
        """
        Kitapyurdu'da arama yap
        """
        try:
            if direct_url:
                logger.info(f"🔗 Direct URL ile fetch: {direct_url[:60]}...")
                return self.fetch_by_url(direct_url)

            if not query or len(query.strip()) < 3:
                logger.warning("❌ Arama sorgusu çok kısa")
                return None

            logger.info(f"🔎 Kitapyurdu'da aranıyor: {query[:60]}...")

            encoded_query = quote_plus(query)
            url = f"{self.BASE_URL}/index.php?route=product/search&filter_name={encoded_query}"

            response = self.get_response(url, use_scraper=False)
            if not response:
                logger.warning("❌ Arama sayfası alınamadı, fallback'a geçiliyor")
                return self._improved_fallback_search(query)

            try:
                html_content = response.content.decode('utf-8')
            except:
                html_content = response.content.decode('iso-8859-9', errors='replace')

            # lxml parser kullan
            soup = BeautifulSoup(html_content, 'lxml')

            # Çoklu selektör ile ürünleri bul
            kitaplar = self._find_all_products(soup)

            if not kitaplar:
                logger.warning("❌ Normal arama sonuç bulunamadı, fallback'a geçiliyor")
                return self._improved_fallback_search(query)

            logger.info(f"📚 {len(kitaplar)} sonuç bulundu")

            # Benzerlik skoruna göre en uygun kitabı bul
            en_iyi_kitap = None
            en_yuksek_skor = 0

            for idx, kitap in enumerate(kitaplar[:10], 1):
                try:
                    # Link bulma
                    link_elem = kitap.select_one('a')
                    if not link_elem or 'href' not in link_elem.attrs:
                        continue

                    link = link_elem['href']
                    link = self._normalize_url(link)

                    # Başlık bulma - çoklu selektör
                    baslik_elem = (
                        kitap.select_one('.name span') or 
                        kitap.select_one('.name a') or
                        kitap.select_one('.product-name') or
                        kitap.select_one('.title') or
                        kitap.select_one('h3') or
                        kitap.select_one('h2') or
                        link_elem  # Son çare olarak link metni
                    )
                    
                    kitap_baslik = metin_duzelt(baslik_elem.text) if baslik_elem else ""

                    if not kitap_baslik or len(kitap_baslik) < 3:
                        logger.debug(f"   [{idx}] Başlık bulunamadı")
                        continue

                    skor = benzerlik_orani(query.lower(), kitap_baslik.lower())

                    logger.debug(f"   [{idx}] '{kitap_baslik[:50]}' → {skor:.2f}")

                    if skor > en_yuksek_skor:
                        en_yuksek_skor = skor
                        en_iyi_kitap = link

                except Exception as e:
                    logger.debug(f"Sonuç parse hatası: {e}")
                    continue

            # İlk kitabı döndür (fallback'a girme)
            if not en_iyi_kitap and kitaplar:
                logger.info("ℹ️ Benzerlik skoru düşük, ilk sonuç seçiliyor")
                first_link = kitaplar[0].select_one('a')
                if first_link and 'href' in first_link.attrs:
                    en_iyi_kitap = self._normalize_url(first_link['href'])
                    en_yuksek_skor = 0

            # Sadece kitap hiç bulunmadığında fallback'a git
            if not en_iyi_kitap:
                logger.warning("❌ Kitap seçilemedi, fallback'a geçiliyor")
                return self._improved_fallback_search(query)

            logger.info(f"✅ Seçilen kitap (skor: {en_yuksek_skor:.2f})")

            return self.fetch_by_url(en_iyi_kitap)

        except Exception as e:
            logger.error(f"❌ Kitapyurdu arama hatası: {e}, fallback'a geçiliyor")
            return self._improved_fallback_search(query)

    def _improved_fallback_search(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Gelişmiş fallback arama: Google → DuckDuckGo
        """
        try:
            time.sleep(2)
            
            logger.info(f"🔍 Fallback arama deneniyor: {query[:50]}...")
            
            # Sorguyu temizle
            query_clean = query.replace("_okunmadı", "").replace("_", " ").strip()
            
            # 1. Google ile arama
            result = self._google_fallback_search(query_clean)
            if result:
                logger.info("✅ Fallback aramasında kitap bulundu (Google)")
                return result
            
            # 2. DuckDuckGo ile arama
            if HAS_SCRAPER:
                result = self._duckduckgo_fallback_search(query_clean)
                if result:
                    logger.info("✅ Fallback aramasında kitap bulundu (DuckDuckGo)")
                    return result
            
            logger.warning("❌ Tüm fallback yöntemler başarısız")
            return None
        
        except Exception as e:
            logger.error(f"❌ Fallback arama hatası: {e}")
            return None

    def _google_fallback_search(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Google ile site:kitapyurdu.com araması
        """
        try:
            time.sleep(1)
            
            logger.debug(f"🔍 Google fallback araması: {query[:50]}...")
            
            # Google arama URL'si
            google_query = f"site:kitapyurdu.com \"{query}\""
            google_encoded = quote_plus(google_query)
            google_url = f"https://www.google.com/search?q={google_encoded}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
            }
            
            response = self.session.get(google_url, headers=headers, timeout=15, allow_redirects=True)
            
            if response.status_code != 200:
                logger.debug(f"⚠️ Google başarısız: {response.status_code}")
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Google arama sonuçları
            results = soup.select('div.g a[href*="kitapyurdu.com"]')
            
            if not results:
                logger.debug("❌ Google sonuç bulunamadı")
                return None
            
            logger.debug(f"📚 Google'da {len(results)} sonuç bulundu")
            
            for result in results:
                try:
                    link = result.get('href', '')
                    
                    # /url?q= formatını düzelt
                    if '/url?q=' in link:
                        link = link.split('/url?q=')[1].split('&')[0]
                    
                    if not link or not link.startswith('http'):
                        continue
                    
                    if 'kitapyurdu.com' not in link or '/kitap/' not in link:
                        continue
                    
                    logger.debug(f"✅ Google URL bulundu: {link[:80]}...")
                    
                    kitap_data = self.fetch_by_url(link)
                    if kitap_data:
                        baslik_skoru = benzerlik_orani(query.lower(), kitap_data['baslik'].lower())
                        if baslik_skoru >= 0.5:
                            logger.debug(f"✅ Uygun kitap bulundu (skor: {baslik_skoru:.2f})")
                            return kitap_data
                
                except Exception as e:
                    logger.debug(f"Google sonuç hatası: {e}")
                    continue
            
            logger.debug("❌ Google'da uygun link bulunamadı")
            return None
            
        except Exception as e:
            logger.debug(f"❌ Google fallback hatası: {e}")
            return None

    def _duckduckgo_fallback_search(self, query: str) -> Optional[Dict[str, Any]]:
        """
        DuckDuckGo ile site:kitapyurdu.com araması
        """
        try:
            time.sleep(2)
            
            logger.debug(f"🔍 DuckDuckGo fallback araması: {query[:50]}...")
            
            ddg_query = f"site:kitapyurdu.com \"{query}\""
            ddg_encoded = quote_plus(ddg_query)
            ddg_url = f"https://duckduckgo.com/html/?q={ddg_encoded}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
            }
            
            response = self.scraper.get(ddg_url, headers=headers, timeout=15)
            
            if response.status_code != 200:
                logger.debug(f"⚠️ DuckDuckGo başarısız: {response.status_code}")
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            results = soup.select('.result')
            
            if not results:
                logger.debug("❌ DuckDuckGo sonuç bulunamadı")
                return None
            
            logger.debug(f"📚 DuckDuckGo'da {len(results)} sonuç bulundu")
            
            for result in results:
                try:
                    link_elem = result.select_one('a.result__url')
                    if not link_elem:
                        continue
                    
                    link = link_elem.get('href', '')
                    if link.startswith('//'):
                        link = 'https:' + link
                    elif not link.startswith('http'):
                        continue
                    
                    if 'kitapyurdu.com' not in link or '/kitap/' not in link:
                        continue
                    
                    logger.debug(f"✅ DuckDuckGo URL bulundu: {link[:80]}...")
                    
                    kitap_data = self.fetch_by_url(link)
                    if kitap_data:
                        baslik_skoru = benzerlik_orani(query.lower(), kitap_data['baslik'].lower())
                        if baslik_skoru >= 0.5:
                            logger.debug(f"✅ Uygun kitap bulundu (skor: {baslik_skoru:.2f})")
                            return kitap_data
                
                except Exception as e:
                    logger.debug(f"DuckDuckGo sonuç hatası: {e}")
                    continue
            
            logger.debug("❌ DuckDuckGo'da uygun link bulunamadı")
            return None
        
        except Exception as e:
            logger.debug(f"❌ DuckDuckGo fallback hatası: {e}")
            return None

    def _parse_detail_page(self, soup, link: str) -> Optional[Dict[str, Any]]:
        """Detay sayfasını parse et"""
        data = veri_kalibi()
        data["link"] = link
        
        try:
            # JSON-LD ve Meta
            DataParser.extract_json_ld(soup, data)
            DataParser.extract_meta_tags(soup, data)
            
            # Başlık
            if not data["baslik"]:
                h1 = soup.select_one('h1.pr_header__heading')
                if h1:
                    data["baslik"] = metin_duzelt(h1.text)
            
            if data["baslik"]:
                data["baslik"] = baslik_teknik_temizle(data["baslik"])
            
            # Yazar
            yazar_isimleri = []
            yazar_span_list = soup.select('.pr_producers__manufacturer')
            
            for span in yazar_span_list:
                label = span.select_one('.pr_producers__label')
                role = label.text.strip() if label else "Yazar"
                
                if "Çevir" in role:
                    continue
                
                links = span.select('.pr_producers__link')
                for lnk in links:
                    isim = metin_duzelt(lnk.text)
                    if isim and isim not in yazar_isimleri:
                        yazar_isimleri.append(isim)
            
            # Tablolardan ek yazar bilgisi
            rows = soup.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 2:
                    label = cells[0].get_text().strip()
                    value = cells[1].get_text().strip()
                    
                    if any(x in label for x in ["Yazar", "Derleyici", "Editör", "Hazırlayan"]):
                        links = cells[1].find_all('a')
                        if links:
                            for l in links:
                                isim = metin_duzelt(l.get_text())
                                if isim and isim not in yazar_isimleri:
                                    yazar_isimleri.append(isim)
                        else:
                            isim = metin_duzelt(value)
                            if isim and isim not in yazar_isimleri:
                                yazar_isimleri.append(isim)
            
            if yazar_isimleri:
                data["yazar"] = ", ".join(yazar_isimleri)
            
            # Açıklama
            desc_raw = soup.select_one('.info__text')
            if desc_raw:
                raw_text = desc_raw.get_text(separator=' ')
                data["aciklama"] = metin_duzelt(raw_text)
            
            # Yayınevi
            yayinevi_tag = soup.select_one('.pr_producers__publisher .pr_producers__link')
            if yayinevi_tag:
                raw_pub = metin_duzelt(yayinevi_tag.text)
                data["yayinevi"] = turkce_baslik(raw_pub)
            
            # Özellikler
            attributes = soup.select('.attributes tr')
            for row in attributes:
                cols = row.select('td')
                if len(cols) == 2:
                    key = cols[0].text.strip()
                    val = metin_duzelt(cols[1].text)
                    
                    if "Sayfa Sayısı" in key:
                        data["sayfa"] = val
                    elif "Yayın Tarihi" in key:
                        data["tarih"] = val
                    elif "ISBN" in key:
                        data["isbn"] = val.replace('-', '')
                    elif "Çevirmen" in key:
                        data["cevirmen"] = val
                    elif "Orijinal Adı" in key:
                        data["orijinal_ad"] = val
            
            # ISBN fallback
            if not data["isbn"]:
                data["isbn"] = isbn_bul(str(soup))
            
            logger.info(f"✅ Parse edildi: {data['baslik']} ({data.get('isbn', 'N/A')})")
            
            return data
            
        except Exception as e:
            logger.error(f"❌ Parse hatası: {e}", exc_info=True)
            return None

    def test_search(self, query: str):
        """Debug arama testi - Geliştirilmiş versiyon"""