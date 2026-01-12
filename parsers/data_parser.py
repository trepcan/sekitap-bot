import json
import html
import logging
from typing import Dict, Any
from bs4 import BeautifulSoup

from utils.text_utils import metin_duzelt

logger = logging.getLogger(__name__)


class DataParser:
    """HTML ve JSON verilerini parse etme yardımcı sınıfı"""
    
    @staticmethod
    def extract_meta_tags(soup: BeautifulSoup, data: Dict[str, Any]):
        """Meta tag'lerden bilgi çıkar"""
        try:
            # Open Graph meta tags
            if not data.get("baslik"):
                meta_title = soup.find("meta", property="og:title")
                if not meta_title:
                    meta_title = soup.find("meta", attrs={"name": "title"})
                if meta_title and meta_title.get("content"):
                    data["baslik"] = metin_duzelt(meta_title["content"])
            
            if not data.get("aciklama"):
                meta_desc = soup.find("meta", property="og:description")
                if not meta_desc:
                    meta_desc = soup.find("meta", attrs={"name": "description"})
                if meta_desc and meta_desc.get("content"):
                    data["aciklama"] = metin_duzelt(meta_desc["content"])
            
            # Twitter meta tags
            if not data.get("baslik"):
                twitter_title = soup.find("meta", attrs={"name": "twitter:title"})
                if twitter_title and twitter_title.get("content"):
                    data["baslik"] = metin_duzelt(twitter_title["content"])
            
            if not data.get("aciklama"):
                twitter_desc = soup.find("meta", attrs={"name": "twitter:description"})
                if twitter_desc and twitter_desc.get("content"):
                    data["aciklama"] = metin_duzelt(twitter_desc["content"])
            
        except Exception as e:
            logger.error(f"❌ Meta tag parse hatası: {e}")
    
    @staticmethod
    def extract_json_ld(soup: BeautifulSoup, data: Dict[str, Any]):
        """JSON-LD schema.org verilerini çıkar"""
        try:
            scripts = soup.find_all('script', type='application/ld+json')
            
            for script in scripts:
                if not script.string:
                    continue
                
                try:
                    # HTML entity'leri decode et
                    json_str = html.unescape(script.string)
                    json_data = json.loads(json_str)
                    
                    # Liste ise her elemanı işle
                    items = json_data if isinstance(json_data, list) else [json_data]
                    
                    for item in items:
                        # Book veya Product tipini bul
                        item_type = item.get('@type', '')
                        
                        if item_type in ['Book', 'Product']:
                            # Başlık
                            if not data.get("baslik") and item.get('name'):
                                data["baslik"] = metin_duzelt(item['name'])
                            
                            # Yazar
                            if not data.get("yazar"):
                                author = item.get('author')
                                if author:
                                    if isinstance(author, dict):
                                        if author.get('name'):
                                            data["yazar"] = metin_duzelt(author['name'])
                                    elif isinstance(author, list):
                                        author_names = []
                                        for a in author:
                                            if isinstance(a, dict) and a.get('name'):
                                                author_names.append(metin_duzelt(a['name']))
                                            elif isinstance(a, str):
                                                author_names.append(metin_duzelt(a))
                                        if author_names:
                                            data["yazar"] = ", ".join(author_names)
                                    elif isinstance(author, str):
                                        data["yazar"] = metin_duzelt(author)
                            
                            # Açıklama
                            if not data.get("aciklama") and item.get('description'):
                                data["aciklama"] = metin_duzelt(item['description'])
                            
                            # ISBN
                            if not data.get("isbn"):
                                isbn = item.get('isbn')
                                if not isbn:
                                    isbn = item.get('identifier')
                                if isbn:
                                    if isinstance(isbn, str):
                                        data["isbn"] = isbn.replace('-', '').replace(' ', '')
                                    elif isinstance(isbn, list) and isbn:
                                        data["isbn"] = str(isbn[0]).replace('-', '').replace(' ', '')
                            
                            # Sayfa sayısı
                            if not data.get("sayfa"):
                                pages = item.get('numberOfPages')
                                if not pages:
                                    pages = item.get('bookFormat')
                                if pages:
                                    data["sayfa"] = str(pages)
                            
                            # Yayınevi
                            if not data.get("yayinevi"):
                                publisher = item.get('publisher')
                                if publisher:
                                    if isinstance(publisher, dict):
                                        pub_name = publisher.get('name')
                                    else:
                                        pub_name = publisher
                                    if pub_name:
                                        from utils.text_utils import turkce_baslik
                                        data["yayinevi"] = turkce_baslik(metin_duzelt(str(pub_name)))
                            
                            # Yayın tarihi
                            if not data.get("tarih"):
                                date_published = item.get('datePublished')
                                if date_published:
                                    data["tarih"] = metin_duzelt(str(date_published))
                            
                            # Puan
                            if not data.get("puan"):
                                agg_rating = item.get('aggregateRating')
                                if isinstance(agg_rating, dict):
                                    rating_value = agg_rating.get('ratingValue')
                                    rating_count = agg_rating.get('ratingCount')
                                    if rating_value and rating_count:
                                        try:
                                            if int(rating_count) >= 100:
                                                data["puan"] = str(rating_value)
                                                data["oy_sayisi"] = str(rating_count)
                                        except:
                                            pass
                
                except json.JSONDecodeError as je:
                    logger.debug(f"⚠️ JSON-LD parse hatası: {je}")
                    continue
                except Exception as e:
                    logger.debug(f"⚠️ JSON-LD item parse hatası: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"❌ JSON-LD genel hatası: {e}")
    
    @staticmethod
    def clean_and_validate(data: Dict[str, Any]) -> Dict[str, Any]:
        """Veriyi temizle ve doğrula"""
        # Boş değerleri temizle
        cleaned = {}
        for key, value in data.items():
            if value is not None and str(value).strip():
                cleaned[key] = value
        
        # ISBN formatını düzelt
        if cleaned.get("isbn"):
            cleaned["isbn"] = cleaned["isbn"].replace('-', '').replace(' ', '')
        
        # Puan formatını düzelt
        if cleaned.get("puan"):
            try:
                puan_float = float(str(cleaned["puan"]).replace(',', '.'))
                cleaned["puan"] = f"{puan_float:.1f}"
            except:
                pass
        
        # Açıklama uzunluğunu sınırla (Telegram mesaj limiti)
        if cleaned.get("aciklama") and len(cleaned["aciklama"]) > 1000:
            cleaned["aciklama"] = cleaned["aciklama"][:997] + "..."
        
        return cleaned