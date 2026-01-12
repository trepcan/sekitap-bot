import json
import re
from typing import Optional, Dict, Any
from urllib.parse import quote_plus
from datetime import datetime
import logging

from scrapers.base_scraper import BaseScraper
from parsers.data_parser import DataParser
from utils.text_utils import metin_duzelt, turkce_baslik, baslik_teknik_temizle, isbn_bul
from utils.helpers import tur_cevir_ve_filtrele
from config.constants import veri_kalibi

logger = logging.getLogger(__name__)


class GoodreadsScraper(BaseScraper):
    """Goodreads.com scraper"""
    
    BASE_URL = "https://www.goodreads.com"
    
    def get_name(self) -> str:
        return "Goodreads"
    
    def search(self, query: str, direct_url: str = None, is_isbn_search: bool = False) -> Optional[Dict[str, Any]]:
        """Goodreads'te arama yap"""
        try:
            if direct_url:
                url = direct_url
            elif is_isbn_search and query:
                clean_isbn = re.sub(r'\D', '', query)
                url = f"{self.BASE_URL}/book/isbn/{clean_isbn}"
            else:
                encoded_query = quote_plus(query)
                url = f"{self.BASE_URL}/search?q={encoded_query}"
            
            response = self.get_response(url)
            if not response:
                return None
            
            response.encoding = 'utf-8'
            soup = self.parse_html(response)
            if not soup:
                return None
            
            link = url
            
            # Direkt URL veya ISBN değilse arama sonucunda ilk kitabı bul
            if not direct_url and not is_isbn_search:
                ilk_sonuc = soup.select_one('tr[itemtype="http://schema.org/Book"]')
                if not ilk_sonuc:
                    ilk_sonuc = soup.select_one('table.tableList tr')
                if not ilk_sonuc:
                    return None
                
                link_tag = ilk_sonuc.select_one('a.bookTitle')
                if not link_tag:
                    return None
                
                link = self.BASE_URL + link_tag['href']
                
                # Detay sayfasını çek
                detay_res = self.get_response(link)
                if not detay_res:
                    return None
                detay_res.encoding = 'utf-8'
                soup = self.parse_html(detay_res)
            
            return self._parse_detail_page(soup, link)
            
        except Exception as e:
            logger.error(f"❌ Goodreads arama hatası: {e}")
            return None
    
    def _parse_detail_page(self, soup, link: str) -> Optional[Dict[str, Any]]:
        """Detay sayfasını parse et"""
        data = veri_kalibi()
        data["link"] = link
        
        try:
            # JSON verilerini parse et
            json_data = self._parse_apollo_state(soup)
            if json_data:
                for k, v in json_data.items():
                    if v:
                        data[k] = v
            
            # HTML'den eksik verileri tamamla
            self._extract_html_data(soup, data)
            
            # Başlığı temizle
            if data["baslik"]:
                data["baslik"] = baslik_teknik_temizle(data["baslik"])
            
            # JSON-LD
            DataParser.extract_json_ld(soup, data)
            DataParser.extract_meta_tags(soup, data)
            
            # ISBN fallback
            if not data["isbn"]:
                data["isbn"] = isbn_bul(str(soup))
            
            return data
            
        except Exception as e:
            logger.error(f"❌ Parse hatası: {e}")
            return None
    
    def _parse_apollo_state(self, soup) -> Optional[Dict[str, Any]]:
        """Apollo State JSON'unu parse et"""
        try:
            script = soup.find("script", id="__NEXT_DATA__")
            if not script:
                return None
            
            data_obj = json.loads(script.string)
            apollo_state = data_obj.get("props", {}).get("pageProps", {}).get("apolloState", {})
            
            # Kitap verisini bul
            book_data = None
            for key, value in apollo_state.items():
                if value.get("__typename") == "Book":
                    if value.get("details") or value.get("bookSeries") or value.get("title"):
                        book_data = value
                        break
            
            if not book_data:
                return None
            
            parsed = {}
            
            # Temel bilgiler
            if book_data.get("title"):
                parsed["baslik"] = metin_duzelt(book_data["title"])
            
            if book_data.get("description"):
                desc = book_data["description"]
                try:
                    from bs4 import BeautifulSoup
                    d_soup = BeautifulSoup(str(desc), 'html.parser')
                    parsed["aciklama"] = d_soup.get_text(separator='\n').strip()
                except:
                    parsed["aciklama"] = metin_duzelt(desc)
            
            # Yazarlar
            authors = []
            translators = []
            
            def process_contributor(contributor_data, role):
                name = metin_duzelt(contributor_data.get("name"))
                if not name:
                    return
                role = str(role).lower()
                if "translator" in role or "çevirmen" in role:
                    if name not in translators:
                        translators.append(name)
                else:
                    if name not in authors:
                        authors.append(name)
            
            # Primary contributor
            p_edge = book_data.get("primaryContributorEdge")
            if isinstance(p_edge, dict):
                if p_edge.get("__ref"):
                    edge = apollo_state.get(p_edge.get("__ref"))
                    if edge:
                        role = edge.get("role", "Author")
                        contributor_ref = edge.get("node", {}).get("__ref")
                        contributor = apollo_state.get(contributor_ref)
                        if contributor:
                            process_contributor(contributor, role)
                else:
                    role = p_edge.get("role", "Author")
                    node = p_edge.get("node", {})
                    if node.get("name"):
                        process_contributor(node, role)
            
            # Secondary contributors
            s_edges = book_data.get("secondaryContributorEdges", [])
            for edge_item in s_edges:
                if isinstance(edge_item, dict):
                    if edge_item.get("__ref"):
                        edge = apollo_state.get(edge_item.get("__ref"))
                        if edge:
                            role = edge.get("role", "Author")
                            contributor_ref = edge.get("node", {}).get("__ref")
                            contributor = apollo_state.get(contributor_ref)
                            if contributor:
                                process_contributor(contributor, role)
                    else:
                        role = edge_item.get("role", "Author")
                        node = edge_item.get("node", {})
                        if node.get("name"):
                            process_contributor(node, role)
            
            if authors:
                parsed["yazar"] = ", ".join(authors)
            if translators:
                parsed["cevirmen"] = ", ".join(translators)
            
            # İstatistikler
            stats = None
            if book_data.get("stats"):
                stats = book_data.get("stats")
            else:
                work_ref = book_data.get("work", {}).get("__ref")
                if work_ref:
                    work_data = apollo_state.get(work_ref)
                    if work_data and work_data.get("stats"):
                        stats = work_data["stats"]
            
            if stats:
                rating_count = stats.get("ratingsCount")
                parsed["oy_sayisi"] = str(rating_count) if rating_count else None
                if rating_count and int(rating_count) >= 100:
                    if stats.get("averageRating"):
                        parsed["puan"] = str(stats.get("averageRating"))
            
            # Türler
            raw_genres = []
            if book_data.get("bookGenres"):
                for bg in book_data.get("bookGenres"):
                    if bg.get("genre") and bg.get("genre").get("name"):
                        raw_genres.append(bg.get("genre").get("name"))
            
            if not raw_genres:
                for key, val in apollo_state.items():
                    if val.get("__typename") == "Genre":
                        if val.get("name"):
                            raw_genres.append(val.get("name"))
            
            if raw_genres:
                raw_genres = list(dict.fromkeys(raw_genres))
                parsed["turu"] = tur_cevir_ve_filtrele(raw_genres)
            
            # Seri
            series_list = book_data.get("bookSeries", [])
            if series_list:
                series_item = series_list[0]
                series_pos = series_item.get("userPosition", "")
                series_ref = series_item.get("series", {}).get("__ref")
                if series_ref and series_ref in apollo_state:
                    series_title = apollo_state[series_ref].get("title")
                    if series_title:
                        parsed["seri"] = f"{series_title} #{series_pos}" if series_pos else series_title
            
            # Detaylar
            details = book_data.get("details", {})
            if details:
                if details.get("publisher"):
                    parsed["yayinevi"] = turkce_baslik(metin_duzelt(details["publisher"]))
                if details.get("numPages"):
                    parsed["sayfa"] = str(details["numPages"])
                if details.get("isbn13"):
                    parsed["isbn"] = str(details["isbn13"])
                
                pub_time = details.get("publicationTime")
                if pub_time:
                    try:
                        dt = datetime.fromtimestamp(pub_time / 1000)
                        aylar = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
                                "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
                        parsed["tarih"] = f"{dt.day} {aylar[dt.month-1]} {dt.year}"
                    except:
                        pass
            
            return parsed
            
        except Exception as e:
            logger.error(f"⚠️ Apollo State parse hatası: {e}")
            return None
    
    def _extract_html_data(self, soup, data: Dict[str, Any]):
        """HTML'den veri çıkar"""
        # Başlık
        if not data["baslik"]:
            title_tag = soup.select_one('h1[data-testid="bookTitle"]')
            if not title_tag:
                title_tag = soup.select_one('h1#bookTitle')
            if title_tag:
                data["baslik"] = metin_duzelt(title_tag.text)
        
        # Yazar
        if not data["yazar"]:
            author_spans = soup.select('span[data-testid="name"]')
            if not author_spans:
                author_spans = soup.select('a.authorName span')
            authors = []
            for span in author_spans:
                name = metin_duzelt(span.text)
                if name and name not in authors:
                    authors.append(name)
            if authors:
                data["yazar"] = ", ".join(authors)
        
        # Açıklama
        if not data["aciklama"]:
            at = soup.select_one('div[data-testid="description"] span')
            if not at:
                at = soup.select_one('div#description span')
            if at:
                data["aciklama"] = metin_duzelt(at.text)
        
        # Seri
        if not data["seri"]:
            st = soup.select_one('.BookPageTitleSection__title h3 a')
            if not st:
                st = soup.select_one('h3[data-testid="bookSeries"] a')
            if not st:
                st = soup.select_one('h2#bookSeries a')
            if st:
                data["seri"] = metin_duzelt(st.text)
        
        # Sayfa
        if not data["sayfa"]:
            pg = soup.select_one('p[data-testid="pagesFormat"]')
            if not pg:
                pg = soup.select_one('span[itemprop="numberOfPages"]')
            if pg:
                data["sayfa"] = pg.text.split()[0]
        
        # Puan
        if not data.get("puan"):
            rating_col = soup.select_one('div.RatingStatistics__column')
            if rating_col and rating_col.has_attr('aria-label'):
                match = re.search(r'(\d+[.,]\d+)', rating_col['aria-label'])
                if match:
                    data["puan"] = match.group(1)
        
        # Oy sayısı
        if not data.get("oy_sayisi"):
            rating_count = soup.select_one('span[data-testid="ratingsCount"]')
            if not rating_count:
                rating_count = soup.select_one('meta[itemprop="ratingCount"]')
            if rating_count:
                val = rating_count.get("content") if rating_count.name == "meta" else rating_count.text
                data["oy_sayisi"] = re.sub(r'\D', '', val.strip())
        
        # Puan kontrolü (100'den az oy varsa iptal)
        if data.get("oy_sayisi"):
            try:
                cnt = int(data["oy_sayisi"].replace('.', '').replace(',', ''))
                if cnt < 100:
                    data["puan"] = None
            except:
                pass
        
        # Türler
        if not data.get("turu"):
            genre_divs = soup.select('div[data-testid="genresList"] a')
            if not genre_divs:
                genre_divs = soup.select('.elementList .left .bookPageGenreLink')
            if genre_divs:
                raw_genres = [g.text for g in genre_divs]
                data["turu"] = tur_cevir_ve_filtrele(raw_genres)
        
        # Yayın bilgileri
        if not data["tarih"] or not data["yayinevi"]:
            pub_info = soup.select_one('p[data-testid="publicationInfo"]')
            if not pub_info:
                pub_info = soup.select_one('div#details')
            if pub_info:
                text = pub_info.text.strip()
                if "by" in text:
                    parts = text.split("by")
                    raw_date = parts[0].replace("Published", "").replace("First published", "").strip()
                    raw_pub = parts[1].strip()
                    if not data["tarih"]:
                        data["tarih"] = metin_duzelt(raw_date)
                    if not data["yayinevi"]:
                        data["yayinevi"] = turkce_baslik(metin_duzelt(raw_pub))
