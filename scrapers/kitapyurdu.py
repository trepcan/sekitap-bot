from typing import Optional, Dict, Any
from urllib.parse import quote_plus
import logging
import re

from scrapers.base_scraper import BaseScraper
from parsers.data_parser import DataParser
from utils.text_utils import metin_duzelt, turkce_baslik, baslik_teknik_temizle, isbn_bul
from config.constants import veri_kalibi

logger = logging.getLogger(__name__)


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
            
            from bs4 import BeautifulSoup
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
        # ID'den URL oluştur (slug kısmı "-" olabilir, yönlendirme yapılır)
        url = f"{self.BASE_URL}/kitap/-/{book_id}.html"
        return self.fetch_by_url(url)
    
    @staticmethod
    def extract_id_from_url(url: str) -> Optional[str]:
        """
        URL'den kitap ID'sini çıkar
        
        Örnek: 
            https://www.kitapyurdu.com/kitap/pratik-rusca-konusma-kilavuzu/82977.html
            -> "82977"
        """
        if not url:
            return None
        
        # Pattern: /kitap/herhangi-slug/12345.html
        match = re.search(r'/kitap/[^/]+/(\d+)\.html', url)
        if match:
            return match.group(1)
        
        # Alternatif: sadece sayı.html
        match = re.search(r'/(\d+)\.html', url)
        if match:
            return match.group(1)
        
        return None
    
    def search(self, query: str, direct_url: str = None) -> Optional[Dict[str, Any]]:
        """Kitapyurdu'da arama yap"""
        try:
            # Direct URL verilmişse direkt fetch et
            if direct_url:
                return self.fetch_by_url(direct_url)
            
            encoded_query = quote_plus(query)
            url = f"{self.BASE_URL}/index.php?route=product/search&filter_name={encoded_query}"
            
            response = self.get_response(url, use_scraper=False)
            if not response:
                return None
            
            # Encoding ayarla
            try:
                html_content = response.content.decode('utf-8')
            except:
                html_content = response.content.decode('iso-8859-9', errors='replace')
            
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # İlk sonucu bul
            ilk_kitap = soup.select_one('.product-cr')
            if not ilk_kitap:
                return None
            
            link = ilk_kitap.select_one('a')['href']
            
            # Detay sayfasını çek
            detay_res = self.session.get(link, timeout=self.timeout)
            try:
                html_detay = detay_res.content.decode('utf-8')
            except:
                html_detay = detay_res.content.decode('iso-8859-9', errors='replace')
            
            detay_soup = BeautifulSoup(html_detay, 'html.parser')
            
            return self._parse_detail_page(detay_soup, link)
            
        except Exception as e:
            logger.error(f"❌ Kitapyurdu arama hatası: {e}")
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
            
            return data
            
        except Exception as e:
            logger.error(f"❌ Parse hatası: {e}")
            return None