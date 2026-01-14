"""
Kitap arama ve zenginleştirme servisi
"""
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


class BookService:
    """Kitap arama ve zenginleştirme servisi"""
    
    def __init__(self):
        self.scrapers = {
            'kitapyurdu': KitapyurduScraper(),
            'goodreads': GoodreadsScraper(),
            'binkitap': BinKitapScraper()
        }
        self.executor = ThreadPoolExecutor(max_workers=3)
        
        # Gürültü kelimelerini regex pattern'e çevir (performans için)
        self._gurultu_pattern = self._create_noise_pattern()
        
        # Kitapyurdu URL pattern
        self._kitapyurdu_url_pattern = re.compile(
            r'https?://(?:www\.)?kitapyurdu\.com/kitap/[^/]+/(\d+)\.html',
            re.IGNORECASE
        )
    
    def _create_noise_pattern(self) -> re.Pattern:
        """Gürültü kelimelerinden tek bir regex pattern oluştur"""
        escaped_words = [re.escape(word) for word in GURULTU_KELIMELERI]
        pattern_str = r'\b(' + '|'.join(escaped_words) + r')\b'
        return re.compile(pattern_str, re.IGNORECASE | re.UNICODE)
    
    def _extract_kitapyurdu_id(self, text: str) -> Optional[str]:
        """
        Metinden Kitapyurdu kitap ID'sini çıkar
        
        Args:
            text: URL veya URL içeren metin
            
        Returns:
            Kitap ID'si veya None
        """
        if not text:
            return None
        
        # Direkt URL pattern
        match = self._kitapyurdu_url_pattern.search(text)
        if match:
            return match.group(1)
        
        # Alternatif: /kitap/.../12345.html pattern
        match = re.search(r'/kitap/[^/]+/(\d+)\.html', text)
        if match:
            return match.group(1)
        
        # Son çare: sadece /12345.html
        match = re.search(r'/(\d{4,})\.html', text)
        if match:
            return match.group(1)
        
        return None
    
    def _is_kitapyurdu_url(self, text: str) -> bool:
        """Metnin Kitapyurdu URL'si içerip içermediğini kontrol et"""
        if not text:
            return False
        return 'kitapyurdu.com/kitap/' in text.lower()
    
    def _temizle_gurultu(self, text: str) -> str:
        """Metinden gürültü kelimelerini temizle"""
        if not text:
            return text
        
        temiz = self._gurultu_pattern.sub(' ', text)
        temiz = re.sub(r'[_\-\.]+', ' ', temiz)
        temiz = re.sub(r'\[([^\]]*)\]', lambda m: '' if self._is_noise(m.group(1)) else m.group(0), temiz)
        temiz = re.sub(r'\(([^\)]*)\)', lambda m: '' if self._is_noise(m.group(1)) else m.group(0), temiz)
        temiz = re.sub(r'\.(epub|pdf|mobi|azw3|djvu|txt)$', '', temiz, flags=re.IGNORECASE)
        temiz = re.sub(r'\b\d+\.\s*', ' ', temiz)
        temiz = re.sub(r'\s+', ' ', temiz)
        
        return temiz.strip()
    
    def _is_noise(self, text: str) -> bool:
        """Verilen metnin tamamen gürültü olup olmadığını kontrol et"""
        if not text:
            return True
        
        text_lower = text.lower().strip()
        
        if len(text_lower) < 2:
            return True
        
        if re.match(r'^[\d\s\.\-_]+$', text_lower):
            return True
        
        return text_lower in [g.lower() for g in GURULTU_KELIMELERI]
    
    async def search_book(
        self, 
        query: str, 
        isbn: str = None,
        manuel_mod: bool = False,
        direct_url: str = None,
        book_id: str = None
    ):
        """
        Kitap ara ve zenginleştir
        
        Args:
            query: Arama sorgusu (URL de olabilir, otomatik algılanır)
            isbn: ISBN numarası (opsiyonel)
            manuel_mod: True ise zenginleştirme atlanır
            direct_url: Doğrudan kitap linki (opsiyonel)
            book_id: Kitapyurdu kitap ID'si (opsiyonel)
        
        Returns:
            tuple: (kitap_bilgileri: dict|None, kaynak: str, basarili: bool)
        """
        logger.info(f"🔎 Aranıyor (ham): {query[:100] if query else 'N/A'}...")
        
        # ============================================
        # 🔗 ÖNCELİK SIRASI: 
        # 1. book_id parametresi (en yüksek)
        # 2. direct_url'den ID çıkar
        # 3. query URL ise ondan ID çıkar (en düşük)
        # ============================================
        
        # 1. Önce book_id parametresine bak
        if book_id:
            logger.info(f"🔢 book_id parametresi mevcut: {book_id}")
        
        # 2. book_id yoksa ve direct_url varsa, ondan ID çıkar
        if not book_id and direct_url:
            extracted_id = self._extract_kitapyurdu_id(direct_url)
            if extracted_id:
                book_id = extracted_id
                logger.info(f"🔢 direct_url'den Kitapyurdu ID çıkarıldı: {book_id}")
        
        # 3. Hala book_id yoksa ve query bir URL ise, ondan ID çıkar
        if not book_id and query and self._is_kitapyurdu_url(query):
            extracted_id = self._extract_kitapyurdu_id(query)
            if extracted_id:
                book_id = extracted_id
                logger.info(f"🔢 Query URL'den Kitapyurdu ID çıkarıldı: {book_id}")
        
        # ============================================
        # 🎯 ID VARSA DİREKT GİT (EN YÜKSEK ÖNCELİK)
        # ============================================
        if book_id:
            logger.info(f"🔗 Kitap ID ile direkt çekiliyor: {book_id}")
            try:
                kitapyurdu_data = await self._fetch_by_id(book_id)
                
                if kitapyurdu_data:
                    kaynak = "Kitapyurdu"
                    kitapyurdu_data["kaynak"] = kaynak
                    logger.info(f"✅ Bulundu: {kaynak} - {kitapyurdu_data.get('baslik', 'N/A')}")
                    
                    if not manuel_mod:
                        enriched_data = await self._enrich_data(kitapyurdu_data)
                        return (enriched_data, kaynak, True)
                    else:
                        logger.info("ℹ️ Manuel mod, zenginleştirme atlandı")
                        return (kitapyurdu_data, kaynak, True)
                else:
                    logger.warning(f"⚠️ ID ile bulunamadı: {book_id}")
            except Exception as e:
                logger.error(f"❌ ID ile çekme hatası: {e}")
        
        # ============================================
        # 🔍 NORMAL ARAMA
        # ============================================
        # Query tamamen URL ise ve ID çıkarılamadıysa, aramaya geçme
        if query and self._is_kitapyurdu_url(query):
            logger.warning("⚠️ Query bir URL ama ID çıkarılamadı, arama yapılmayacak")
            return (None, "Yok", False)
        
        # Gürültü temizliği
        temiz_query = self._temizle_gurultu(query) if query else ""
        
        if not temiz_query:
            logger.warning("❌ Arama sorgusu boş")
            return (None, "Yok", False)
        
        logger.info(f"🧹 Temizlenmiş sorgu: {temiz_query}")
        
        try:
            # Kitapyurdu'da ara
            kitapyurdu_data = await self._search_kitapyurdu(temiz_query, isbn)
            
            if not kitapyurdu_data:
                logger.warning(f"❌ Hiçbir kaynakta bulunamadı: {temiz_query}")
                return (None, "Yok", False)
            
            # Kaynak bilgisi
            kaynak = "Kitapyurdu"
            kitapyurdu_data["kaynak"] = kaynak
            
            logger.info(f"✅ Bulundu: {kaynak} - {kitapyurdu_data.get('baslik', 'N/A')}")
            
            # Zenginleştirme
            if not manuel_mod:
                enriched_data = await self._enrich_data(kitapyurdu_data)
                return (enriched_data, kaynak, True)
            else:
                logger.info("ℹ️ Manuel mod, zenginleştirme atlandı")
                return (kitapyurdu_data, kaynak, True)
        
        except Exception as e:
            logger.error(f"❌ Arama hatası: {e}")
            import traceback
            traceback.print_exc()
            return (None, "Hata", False)

    async def _fetch_by_id(self, book_id: str) -> Optional[Dict[str, Any]]:
        """Kitap ID'si ile direkt çek"""
        scraper = self.scrapers.get('kitapyurdu')
        if not scraper:
            logger.error("❌ Kitapyurdu scraper bulunamadı")
            return None
        
        try:
            result = await run_sync(scraper.fetch_by_id, book_id)
            return result
        except Exception as e:
            logger.error(f"❌ fetch_by_id hatası: {e}")
            return None

    async def _search_kitapyurdu(
        self, 
        query: str, 
        isbn: str = None
    ):
        """Kitapyurdu'da akıllı arama (ID/URL kontrolü zaten yapıldı)"""
        
        scraper = self.scrapers.get('kitapyurdu')
        if not scraper:
            logger.error("❌ Kitapyurdu scraper bulunamadı")
            return None
        
        # ISBN varsa ISBN ile ara
        if isbn:
            try:
                result = await run_sync(scraper.search, isbn)
                if result:
                    logger.info(f"✅ ISBN ile bulundu: {isbn}")
                    return result
            except Exception as e:
                logger.debug(f"ISBN araması başarısız: {e}")
        
        # Arama stratejileri
        strategies = []
        
        if query and len(query) >= 3:
            strategies.append(("Temizlenmiş sorgu", query))
        
        parantez_match = re.search(r'\(([^)]+)\)', query)
        if parantez_match:
            parantez_ici = parantez_match.group(1).strip()
            if len(parantez_ici) >= 3 and not self._is_noise(parantez_ici):
                yazar_match = re.match(r'^([^\s]+(?:\s+[^\s]+)?)', query)
                if yazar_match:
                    yazar = yazar_match.group(1)
                    strategies.append(("Parantez içi + Yazar", f"{parantez_ici} {yazar}"))
                strategies.append(("Parantez içi", parantez_ici))
        
        parantez_disindaki = re.sub(r'\([^)]*\)', '', query)
        parantez_disindaki = re.sub(r'\s+', ' ', parantez_disindaki).strip()
        if parantez_disindaki and len(parantez_disindaki) >= 3:
            strategies.append(("Parantez dışındaki", parantez_disindaki))
        
        sayisiz = re.sub(r'\b\d+\b', '', query)
        sayisiz = re.sub(r'\s+', ' ', sayisiz).strip()
        if sayisiz != query and len(sayisiz) >= 3:
            strategies.append(("Sayısız", sayisiz))
        
        noktalama_temiz = re.sub(r'[^\wğüşıöçĞÜŞİÖÇ\s]', ' ', query)
        noktalama_temiz = re.sub(r'\s+', ' ', noktalama_temiz).strip()
        if noktalama_temiz != query and len(noktalama_temiz) >= 3:
            strategies.append(("Noktalama temiz", noktalama_temiz))
        
        kelimeler = query.split()
        if len(kelimeler) >= 2:
            ilk_iki = ' '.join(kelimeler[:2])
            if len(ilk_iki) >= 5:
                strategies.append(("İlk 2 kelime", ilk_iki))
            if len(kelimeler) >= 3:
                ilk_uc = ' '.join(kelimeler[:3])
                strategies.append(("İlk 3 kelime", ilk_uc))
        
        if len(kelimeler) >= 2:
            son_iki = ' '.join(kelimeler[-2:])
            if len(son_iki) >= 5:
                strategies.append(("Son 2 kelime", son_iki))
        
        for index, (strateji_adi, sorgu) in enumerate(strategies, 1):
            if not sorgu or len(sorgu) < 3:
                continue
            
            logger.info(f"🔍 [{index}/{len(strategies)}] {strateji_adi}: '{sorgu[:60]}...'")
            
            try:
                result = await run_sync(scraper.search, sorgu)
                if result:
                    logger.info(f"✅ {strateji_adi} ile bulundu!")
                    return result
            except Exception as e:
                logger.debug(f"{strateji_adi} hatası: {e}")
        
        logger.warning(f"❌ {len(strategies)} aşamada da bulunamadı: {query[:60]}")
        return None

    async def _enrich_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Kitap bilgilerini zenginleştir"""
        logger.info("✨ Zenginleştirme başlatılıyor...")
        
        try:
            data = await self.enrich_with_goodreads(data, data.get("isbn"))
            data = await self.enrich_with_binkitap(data)
            logger.info("✅ Zenginleştirme tamamlandı")
        except Exception as e:
            logger.error(f"❌ Zenginleştirme hatası: {e}")
        
        return data
    
    async def enrich_with_goodreads(
        self, 
        data: Dict[str, Any], 
        isbn: str = None
    ) -> Dict[str, Any]:
        """Goodreads ile zenginleştir"""
        try:
            needs_enrichment = (
                not data.get("turu") or 
                not data.get("puan") or 
                not data.get("orijinal_ad") or
                not data.get("seri")
            )
            
            if not needs_enrichment:
                logger.info("ℹ️ Tüm bilgiler mevcut, Goodreads atlandı")
                return data
            
            scraper = self.scrapers['goodreads']
            gr_result = None
            
            if isbn or data.get("isbn"):
                search_term = isbn or data.get("isbn")
                logger.info(f"🔍 Goodreads'te aranıyor: {search_term}...")
                
                try:
                    gr_result = await run_sync(
                        scraper.search, 
                        search_term, 
                        is_isbn_search=True
                    )
                except Exception as e:
                    error_str = str(e)
                    if "404" in error_str or "Not Found" in error_str:
                        logger.warning("⚠️ ISBN ile bulunamadı, başlık+yazar ile deneniyor...")
                        gr_result = None
                    else:
                        logger.debug(f"Goodreads ISBN hatası: {e}")
                        gr_result = None
            
            if not gr_result:
                search_term = f"{data.get('baslik', '')} {data.get('yazar', '')}".strip()
                
                if not search_term:
                    return data
                
                logger.info(f"🔍 Goodreads'te aranıyor: {search_term[:50]}...")
                
                try:
                    gr_result = await run_sync(scraper.search, search_term)
                except Exception as e:
                    logger.debug(f"Goodreads arama hatası: {e}")
                    return data
            
            if gr_result:
                updated = False
                
                if not data.get("orijinal_ad") and gr_result.get("orijinal_ad"):
                    data["orijinal_ad"] = gr_result["orijinal_ad"]
                    updated = True
                    logger.info(f"   ➕ Orijinal Ad: {data['orijinal_ad']}")
                
                if not data.get("turu") and gr_result.get("turu"):
                    data["turu"] = gr_result["turu"]
                    updated = True
                    logger.info(f"   ➕ Tür: {data['turu']}")
                
                if not data.get("puan") and gr_result.get("puan"):
                    data["puan"] = gr_result["puan"]
                    data["oy_sayisi"] = gr_result.get("oy_sayisi")
                    updated = True
                    logger.info(f"   ➕ Puan: {data['puan']} ({data.get('oy_sayisi')} oy)")
                
                if gr_result.get("seri"):
                    existing_series = data.get("seri")
                    translated_series = translate_series_name(gr_result["seri"])
                    final_series = prefer_turkish_series(existing_series, translated_series)
                    
                    if final_series and final_series != existing_series:
                        data["seri"] = final_series
                        updated = True
                        logger.info(f"   ➕ Seri: {data['seri']}")
                
                mevcut_aciklama = data.get("aciklama", "").lower()
                is_weak_desc = (
                    not data.get("aciklama") or 
                    len(data.get("aciklama", "")) < 25 or
                    "açıklama bulunamadı" in mevcut_aciklama
                )
                
                if is_weak_desc and gr_result.get("aciklama") and len(gr_result["aciklama"]) > 25:
                    data["aciklama"] = gr_result["aciklama"]
                    updated = True
                    logger.info("   ➕ Açıklama güncellendi")
                
                if updated:
                    logger.info("✅ Goodreads ile zenginleştirildi")
                else:
                    logger.info("ℹ️ Goodreads'ten yeni bilgi eklenmedi")
            else:
                logger.debug("⚠️ Goodreads'te sonuç bulunamadı")
        
        except Exception as e:
            logger.error(f"❌ Goodreads zenginleştirme hatası: {e}")
        
        return data
    
    async def enrich_with_binkitap(
        self, 
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """1000Kitap ile zenginleştir"""
        try:
            if data.get("orijinal_ad") and data.get("seri") and data.get("cevirmen"):
                logger.info("ℹ️ Tüm bilgiler mevcut, 1000Kitap atlandı")
                return data
            
            if not data.get("baslik"):
                return data
            
            search_term = f"{data.get('baslik', '')} {data.get('yazar', '')}".strip()
            
            logger.info(f"🔍 1000Kitap'ta aranıyor: {search_term[:50]}...")
            
            scraper = self.scrapers['binkitap']
            
            try:
                bk_result = await run_sync(scraper.search, search_term)
            except Exception as e:
                logger.debug(f"1000Kitap arama hatası: {e}")
                return data
            
            if bk_result:
                benzerlik = benzerlik_orani(
                    data.get('baslik', ''), 
                    bk_result.get('baslik', '')
                )
                
                if benzerlik < 0.6:
                    logger.debug(f"⚠️ Düşük benzerlik ({benzerlik:.2f}), atlanıyor")
                    return data
                
                updated = False
                
                if not data.get("orijinal_ad") and bk_result.get("orijinal_ad"):
                    data["orijinal_ad"] = bk_result["orijinal_ad"]
                    updated = True
                    logger.info(f"   ➕ Orijinal Ad: {data['orijinal_ad']}")
                
                if not data.get("cevirmen") and bk_result.get("cevirmen"):
                    data["cevirmen"] = bk_result["cevirmen"]
                    updated = True
                    logger.info(f"   ➕ Çevirmen: {data['cevirmen']}")
                
                if not data.get("seri") and bk_result.get("seri"):
                    data["seri"] = bk_result["seri"]
                    updated = True
                    logger.info(f"   ➕ Seri: {data['seri']}")
                
                if updated:
                    logger.info("✅ 1000Kitap ile zenginleştirildi")
                else:
                    logger.info("ℹ️ 1000Kitap'tan yeni bilgi eklenmedi")
            else:
                logger.debug("⚠️ 1000Kitap'ta sonuç bulunamadı")
        
        except Exception as e:
            logger.error(f"❌ 1000Kitap zenginleştirme hatası: {e}")
        
        return data
    
    def close(self):
        """Kaynakları temizle"""
        self.executor.shutdown(wait=False)


# ========================================
# 🎯 Singleton Instance
# ========================================
book_service = BookService()