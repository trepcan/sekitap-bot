from typing import Optional, Dict, Any
from urllib.parse import quote_plus
import logging
import re
import time
import json

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
        """
        try:
            logger.info(f"🔗 Direkt URL'den çekiliyor: {url[:80]}...")
            response = self.get_response(url, use_scraper=False)
            if not response:
                logger.error("❌ URL'den yanıt alınamadı")
                return None
            
            try:
                html_content = response.content.decode('utf-8')
            except:
                html_content = response.content.decode('iso-8859-9', errors='replace')
            
            soup = BeautifulSoup(html_content, 'html.parser')
            return self._parse_detail_page(soup, url)
            
        except Exception as e:
            logger.error(f"❌ Kitapyurdu fetch_by_url hatası: {e}")
            return None
    
    def fetch_by_id(self, book_id: str) -> Optional[Dict[str, Any]]:
        url = f"{self.BASE_URL}/kitap/-/{book_id}.html"
        return self.fetch_by_url(url)
    
    @staticmethod
    def extract_id_from_url(url: str) -> Optional[str]:
        if not url:
            return None
        match = re.search(r'/kitap/[a-zA-Z0-9\-_]+/(\d+)\.html', url)
        if match:
            return match.group(1)
        match = re.search(r'/(\d+)\.html$', url)
        if match:
            return match.group(1)
        match = re.search(r'[?&]id=(\d+)', url)
        if match:
            return match.group(1)
        return None
    
    def search_by_isbn(self, isbn: str) -> Optional[Dict[str, Any]]:
        if not isbn:
            return None
        try:
            isbn_clean = isbn.replace('-', '').strip()
            if len(isbn_clean) < 10:
                logger.warning(f"⚠️ Geçersiz ISBN: {isbn}")
                return None
            
            logger.info(f"🔢 ISBN ile aranıyor: {isbn_clean}")
            url = f"{self.BASE_URL}/index.php?route=product/search&filter_isbn={isbn_clean}"
            
            response = self.get_response(url, use_scraper=False)
            if not response:
                logger.warning("⚠️ ISBN araması başarısız (yanıt yok)")
                return None
            
            try:
                html_content = response.content.decode('utf-8')
            except:
                html_content = response.content.decode('iso-8859-9', errors='replace')
            
            soup = BeautifulSoup(html_content, 'html.parser')
            kitap = self._find_first_product(soup)
            if not kitap:
                logger.warning("⚠️ ISBN araması sonucu boş")
                return None
            
            link_elem = kitap.select_one('a')
            if not link_elem or 'href' not in link_elem.attrs:
                logger.warning("⚠️ Arama sonucunda link bulunamadı")
                return None
            
            link = self._normalize_url(link_elem['href'])
            logger.info(f"✅ ISBN sonucu bulundu: {link}")
            return self.fetch_by_url(link)
            
        except Exception as e:
            logger.error(f"❌ ISBN araması hatası: {e}")
            return None
    
    def _normalize_url(self, url: str) -> str:
        if url.startswith('http'):
            return url
        elif url.startswith('/'):
            return self.BASE_URL + url
        else:
            return self.BASE_URL + '/' + url
    
    def _find_first_product(self, soup) -> Optional[Any]:
        selektorler = [
            '.product-cr', '.product-item', 'div[data-product-id]',
            '.product-grid > div', '.search-results .product',
            '.product-card', '.item.product', '.products .item',
            '.product-list .product', '.catalog-products .product',
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
        selektorler = [
            '.product-cr', '.product-item', 'div[data-product-id]',
            '.product-grid > div', '.search-results .product',
            '.product-card', '.item.product', '.products .item',
            '.product-list .product', '.catalog-products .product',
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

            soup = BeautifulSoup(html_content, 'lxml')
            kitaplar = self._find_all_products(soup)

            if not kitaplar:
                logger.warning("❌ Normal arama sonuç bulunamadı, fallback'a geçiliyor")
                return self._improved_fallback_search(query)

            logger.info(f"📚 {len(kitaplar)} sonuç bulundu")
            en_iyi_kitap = None
            en_yuksek_skor = 0

            for idx, kitap in enumerate(kitaplar[:10], 1):
                try:
                    link_elem = kitap.select_one('a')
                    if not link_elem or 'href' not in link_elem.attrs:
                        continue
                    link = self._normalize_url(link_elem['href'])
                    baslik_elem = (
                        kitap.select_one('.name span') or 
                        kitap.select_one('.name a') or
                        kitap.select_one('.product-name') or
                        kitap.select_one('.title') or
                        kitap.select_one('h3') or
                        kitap.select_one('h2') or
                        link_elem
                    )
                    kitap_baslik = metin_duzelt(baslik_elem.text) if baslik_elem else ""
                    if not kitap_baslik or len(kitap_baslik) < 3:
                        continue
                    skor = benzerlik_orani(query.lower(), kitap_baslik.lower())
                    if skor > en_yuksek_skor:
                        en_yuksek_skor = skor
                        en_iyi_kitap = link
                except Exception as e:
                    logger.debug(f"Sonuç parse hatası: {e}")
                    continue

            if not en_iyi_kitap and kitaplar:
                logger.info("ℹ️ Benzerlik skoru düşük, ilk sonuç seçiliyor")
                first_link = kitaplar[0].select_one('a')
                if first_link and 'href' in first_link.attrs:
                    en_iyi_kitap = self._normalize_url(first_link['href'])
                    en_yuksek_skor = 0

            if not en_iyi_kitap:
                logger.warning("❌ Kitap seçilemedi, fallback'a geçiliyor")
                return self._improved_fallback_search(query)

            logger.info(f"✅ Seçilen kitap (skor: {en_yuksek_skor:.2f})")
            return self.fetch_by_url(en_iyi_kitap)

        except Exception as e:
            logger.error(f"❌ Kitapyurdu arama hatası: {e}, fallback'a geçiliyor")
            return self._improved_fallback_search(query)

    def _improved_fallback_search(self, query: str) -> Optional[Dict[str, Any]]:
        try:
            time.sleep(2)
            logger.info(f"🔍 Fallback arama deneniyor: {query[:50]}...")
            query_clean = query.replace("_okunmadı", "").replace("_", " ").strip()
            
            result = self._google_fallback_search(query_clean)
            if result:
                logger.info("✅ Fallback aramasında kitap bulundu (Google)")
                return result
            
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
        try:
            time.sleep(1)
            logger.debug(f"🔍 Google fallback araması: {query[:50]}...")
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
            results = soup.select('div.g a[href*="kitapyurdu.com"]')
            
            if not results:
                logger.debug("❌ Google sonuç bulunamadı")
                return None
            
            for result in results:
                try:
                    link = result.get('href', '')
                    if '/url?q=' in link:
                        link = link.split('/url?q=')[1].split('&')[0]
                    if not link or not link.startswith('http'):
                        continue
                    if 'kitapyurdu.com' not in link or '/kitap/' not in link:
                        continue
                    kitap_data = self.fetch_by_url(link)
                    if kitap_data:
                        baslik_skoru = benzerlik_orani(query.lower(), kitap_data['baslik'].lower())
                        if baslik_skoru >= 0.5:
                            return kitap_data
                except Exception as e:
                    logger.debug(f"Google sonuç hatası: {e}")
                    continue
            return None
        except Exception as e:
            logger.debug(f"❌ Google fallback hatası: {e}")
            return None

    def _duckduckgo_fallback_search(self, query: str) -> Optional[Dict[str, Any]]:
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
                    kitap_data = self.fetch_by_url(link)
                    if kitap_data:
                        baslik_skoru = benzerlik_orani(query.lower(), kitap_data['baslik'].lower())
                        if baslik_skoru >= 0.5:
                            return kitap_data
                except Exception as e:
                    logger.debug(f"DuckDuckGo sonuç hatası: {e}")
                    continue
            return None
        except Exception as e:
            logger.debug(f"❌ DuckDuckGo fallback hatası: {e}")
            return None

    # ------------------------------------------------------------------
    # JSON-LD yardımcıları
    # ------------------------------------------------------------------
    def _get_jsonld_books(self, soup) -> list:
        books = []

        def _walk(obj):
            if isinstance(obj, dict):
                t = obj.get("@type", "")
                types = t if isinstance(t, list) else [t]
                if any("Book" in str(x) for x in types):
                    books.append(obj)
                for v in obj.values():
                    _walk(v)
            elif isinstance(obj, list):
                for v in obj:
                    _walk(v)

        for tag in soup.find_all("script", type="application/ld+json"):
            raw = tag.string or tag.get_text()
            if not raw:
                continue
            try:
                obj = json.loads(raw)
            except Exception:
                continue
            _walk(obj if isinstance(obj, list) else [obj])
        return books

    def _jsonld_names(self, value) -> list:
        names = []
        if not value:
            return names
        items = value if isinstance(value, list) else [value]
        for it in items:
            if isinstance(it, dict):
                n = it.get("name")
                if n:
                    names.append(metin_duzelt(n))
            elif isinstance(it, str):
                names.append(metin_duzelt(it))
        return names

    def _jsonld_field(self, soup, *keys):
        for book in self._get_jsonld_books(soup):
            for k in keys:
                if k in book and book[k]:
                    return book[k]
        return None

    # ------------------------------------------------------------------
    # Genel tablo / key-value taraması
    # ------------------------------------------------------------------
    def _scan_spec_rows(self, soup, data: Dict[str, Any]) -> None:
        def _handle(label: str, value_node) -> None:
            label = label.strip().rstrip(":").strip()
            if not label or value_node is None:
                return
            value = metin_duzelt(
                value_node.get_text(" ", strip=True)
            ) if hasattr(value_node, "get_text") else str(value_node).strip()
            if not value:
                return

            checks = [
                ("sayfa", ["sayfa sayısı", "sayfa sayisi", "sayfa"], value),
                ("tarih", ["yayın tarihi", "yayin tarihi", "ilk baskı", "basım tarihi"], value),
                ("isbn", ["isbn"], re.sub(r"[^0-9Xx]", "", value)),
                ("cevirmen", ["çevirmen", "cevirmen", "çeviren", "çeviri"], value),
                ("orijinal_ad", ["orijinal adı", "orijinal adi", "orijinal isim"], value),
                ("yayinevi", ["yayınevi", "yayinevi", "yayıncı"], value),
            ]
            low = label.lower()
            for key, needles, val in checks:
                if not data.get(key) and any(n in low for n in needles):
                    if key == "sayfa":
                        m = re.search(r"(\d+)", val)
                        val = m.group(1) if m else val
                    data[key] = val

        # 1) Klasik tablo satırları (tr / td / th)
        for row in soup.find_all("tr"):
            cells = row.find_all(["td", "th"])
            if len(cells) >= 2:
                _handle(cells[0].get_text(strip=True), cells[-1])

        # 2) Yeni Yapı: Kitapyurdu .ky-pd-attributes__item blokları
        for item in soup.select(".ky-pd-attributes__item"):
            lbl = item.select_one(".ky-pd-attributes__label")
            val = item.select_one(".ky-pd-attributes__value")
            if lbl and val:
                _handle(lbl.get_text(strip=True), val)

        # 3) Diğer alternatif/eski tip key-value blokları
        for sel in [
            ".attributes .item", ".attributes li", ".product-attributes li",
            ".book-attributes li", ".detail-row", ".spec-item", ".attribute",
            ".product-feature", ".detail-item",
        ]:
            for block in soup.select(sel):
                lbl = block.select_one(".label, .name, .key, .title, strong, b")
                val = block.select_one(".value, .val, .data")
                if lbl and val and lbl is not val:
                    _handle(lbl.get_text(strip=True), val)

    def _extract_people(self, soup) -> tuple:
        """Yazar ve çevirmen isimlerini filtreleyerek topla."""
        yazarlar, cevirmenler = [], []

        def _clean_name(name: str) -> str:
            name = metin_duzelt(name)
            # İstenmeyen buton ve ek metinleri temizle
            name = re.sub(r'Tüm Eserlerini Göster', '', name, flags=re.IGNORECASE)
            name = re.sub(r'Tüm Eserleri', '', name, flags=re.IGNORECASE)
            return name.strip(" ,-")

        def _add(target: list, isim: str) -> None:
            isim = _clean_name(isim)
            if isim and len(isim) > 1 and isim not in target:
                target.append(isim)

        # 1) Yeni Yapı: Doğrudan .ky-pd-attributes tablosundaki Çevirmen alanı
        for item in soup.select(".ky-pd-attributes__item"):
            lbl = item.select_one(".ky-pd-attributes__label")
            if lbl and "çevir" in lbl.get_text().lower():
                val = item.select_one(".ky-pd-attributes__value")
                if val:
                    for a in val.find_all("a"):
                        _add(cevirmenler, a.get_text())
                    if not cevirmenler:
                        _add(cevirmenler, val.get_text())

        # 2) Eski Üretici Bloğu (.pr_producers)
        for span in soup.select(".pr_producers__manufacturer"):
            label = span.select_one(".pr_producers__label")
            role = label.get_text(strip=True) if label else "Yazar"
            if "çevir" in role.lower():
                for a in span.select("a"):
                    _add(cevirmenler, a.get_text())
            else:
                for a in span.select("a"):
                    _add(yazarlar, a.get_text())

        # 3) JSON-LD Kontrolü
        for book in self._get_jsonld_books(soup):
            for n in self._jsonld_names(book.get("author")):
                _add(yazarlar, n)
            for n in self._jsonld_names(book.get("translator") or book.get("cevirmen")):
                _add(cevirmenler, n)

        # 4) Yeni ve Genel Selektörler (Öznitelik tablosundaki çevirmen linkleri hariç tutulur)
        for a in soup.select(
            'a[href*="/yazar/"]:not(.ky-pd-attributes__link), .authors a, .author a, '
            '.book-author a, .product-author a, [itemprop="author"] a'
        ):
            text = a.get_text(strip=True)
            if "tüm eserler" not in text.lower():
                _add(yazarlar, text)

        for a in soup.select(
            'a[href*="/cevirmen/"], .translators a, .translator a, '
            '.book-translator a, [itemprop="translator"] a'
        ):
            _add(cevirmenler, a.get_text())

        # 5) Başlık bloğundaki linkler
        header = soup.select_one(
            ".pr_header, .product-header, .book-header, [class*='header'] h1, h1"
        )
        if header:
            for a in header.find_all("a"):
                href = (a.get("href") or "").lower()
                text = a.get_text(strip=True)
                if "tüm eserler" in text.lower():
                    continue
                if "/yazar/" in href:
                    _add(yazarlar, text)
                elif "/cevirmen/" in href:
                    _add(cevirmenler, text)

        # 6) Tablo satırları
        for row in soup.find_all("tr"):
            cells = row.find_all(["td", "th"])
            if len(cells) < 2:
                continue
            label = cells[0].get_text(strip=True).lower()
            links = cells[-1].find_all("a")
            if "çevir" in label:
                for l in links or [cells[-1]]:
                    _add(cevirmenler, l.get_text())
            elif any(x in label for x in ["yazar", "derleyici", "editör", "hazırlayan"]):
                for l in links or [cells[-1]]:
                    _add(yazarlar, l.get_text())

        return yazarlar, cevirmenler

    def _extract_page_count(self, soup, data: Dict[str, Any]) -> None:
        """Sayfa sayısını bulamazsa metin içinden regex ile yakala."""
        if data.get("sayfa"):
            m = re.search(r"\d+", str(data["sayfa"]))
            data["sayfa"] = m.group(0) if m else data["sayfa"]
            return
        node = soup.select_one('[itemprop="numberOfPages"], [itemprop="pageCount"]')
        if node:
            m = re.search(r"\d+", node.get_text())
            if m:
                data["sayfa"] = m.group(0)
                return
        text = soup.get_text(" ", strip=True)
        m = re.search(r"(\d{1,5})\s*(?:Sayfa|sayfa)", text)
        if m:
            data["sayfa"] = m.group(1)

    def _parse_detail_page(self, soup, link: str) -> Optional[Dict[str, Any]]:
        """Detay sayfasını parse et"""
        data = veri_kalibi()
        data["link"] = link

        try:
            DataParser.extract_json_ld(soup, data)
            DataParser.extract_meta_tags(soup, data)

            # Başlık
            if not data["baslik"]:
                for sel in [
                    "h1.pr_header__heading", "h1.product-title",
                    "h1.book-title", '[itemprop="name"]', "h1",
                ]:
                    h1 = soup.select_one(sel)
                    if h1:
                        data["baslik"] = metin_duzelt(h1.get_text())
                        break

            if data["baslik"]:
                data["baslik"] = baslik_teknik_temizle(data["baslik"])

            # Yazar + Çevirmen
            yazarlar, cevirmenler = self._extract_people(soup)
            if yazarlar:
                data["yazar"] = ", ".join(yazarlar)
            if cevirmenler:
                data["cevirmen"] = ", ".join(cevirmenler)

            # Açıklama (Yeni ky-pd-about__description seçicisi eklendi ve önceliklendirildi)
            desc_elem = soup.select_one(
                ".ky-pd-about__description, .info__text, .book-description, "
                ".product-description, [itemprop='description']"
            )
            if desc_elem:
                desc_text = desc_elem.get_text(separator="\n", strip=True)
                desc_text = re.sub(r'\n\s*\n', '\n\n', desc_text)
                data["aciklama"] = desc_text
            elif not data.get("aciklama"):
                data["aciklama"] = ""

            # Yayınevi
            if not data.get("yayinevi"):
                for sel in [
                    ".pr_producers__publisher .pr_producers__link",
                    ".pr_producers__publisher a",
                    'a[href*="/yayinevi/"]', '[itemprop="publisher"] a',
                    ".publisher a", ".book-publisher a",
                ]:
                    tag = soup.select_one(sel)
                    if tag:
                        raw_pub = metin_duzelt(tag.get_text())
                        if raw_pub:
                            data["yayinevi"] = turkce_baslik(raw_pub)
                            break
            if not data.get("yayinevi"):
                pub = self._jsonld_field(soup, "publisher")
                names = self._jsonld_names(pub)
                if names:
                    data["yayinevi"] = turkce_baslik(names[0])

            # Sayfa, tarih, ISBN, çevirmen, orijinal ad (Tabloları tara)
            self._scan_spec_rows(soup, data)

            # JSON-LD'den kalan alanlar
            if not data.get("tarih"):
                dp = self._jsonld_field(soup, "datePublished")
                if dp:
                    data["tarih"] = str(dp)
            if not data.get("isbn"):
                isbn = self._jsonld_field(soup, "isbn")
                if isbn:
                    data["isbn"] = re.sub(r"[^0-9Xx]", "", str(isbn))
            if not data.get("sayfa"):
                np_ = self._jsonld_field(soup, "numberOfPages")
                if np_:
                    data["sayfa"] = str(np_)

            self._extract_page_count(soup, data)

            if not data["isbn"]:
                data["isbn"] = isbn_bul(str(soup))

            logger.info(f"✅ Parse edildi: {data['baslik']} ({data.get('isbn', 'N/A')})")
            return data

        except Exception as e:
            logger.error(f"❌ Parse hatası: {e}", exc_info=True)
            return None

    def test_search(self, query: str):
        """Debug arama testi - Geliştirilmiş versiyon"""
        logger.info(f"🧪 Test araması: {query}")
        sonuc = self.search(query)
        if sonuc:
            logger.info("✅ Sonuç bulundu:")
            for k, v in sonuc.items():
                logger.info(f"   {k}: {v}")
        else:
            logger.info("❌ Sonuç bulunamadı")
        return sonuc