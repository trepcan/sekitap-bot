"""
Kitap arama ve zenginleştirme servisi
"""
import logging
from typing import Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor
import asyncio

from scrapers.kitapyurdu import KitapyurduScraper
from scrapers.goodreads import GoodreadsScraper
from scrapers.binkitap import BinKitapScraper
from utils.async_utils import run_sync
from utils.text_utils import metin_duzelt, benzerlik_orani
from utils.series_utils import translate_series_name, prefer_turkish_series

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
    
    async def search_book(
        self, 
        query: str, 
        isbn: str = None,
        manuel_mod: bool = False
    ):
        """
        Kitap ara ve zenginleştir
        
        Returns:
            tuple: (kitap_bilgileri: dict|None, kaynak: str, basarili: bool)
        """
        logger.info(f"🔎 Aranıyor: {query}")
        
        try:
            # Kitapyurdu'da ara
            kitapyurdu_data = await self._search_kitapyurdu(query, isbn)
            
            if not kitapyurdu_data:
                logger.warning(f"❌ Hiçbir kaynakta bulunamadı: {query}")
                return (None, "Yok", False)  # ← TUPLE!
            
            # Kaynak bilgisi
            kaynak = "Kitapyurdu"
            kitapyurdu_data["kaynak"] = kaynak
            
            logger.info(f"✅ Bulundu: {kaynak} - {kitapyurdu_data.get('baslik', 'N/A')}")
            
            # Zenginleştirme
            if not manuel_mod:
                enriched_data = await self._enrich_data(kitapyurdu_data)
                return (enriched_data, kaynak, True)  # ← TUPLE!
            else:
                logger.info("ℹ️ Manuel mod, zenginleştirme atlandı")
                return (kitapyurdu_data, kaynak, True)  # ← TUPLE!
        
        except Exception as e:
            logger.error(f"❌ Arama hatası: {e}")
            import traceback
            traceback.print_exc()
            return (None, "Hata", False)  # ← TUPLE!


    async def _search_kitapyurdu(self, query: str, isbn: str = None):
        """Kitapyurdu'da akıllı arama - 3 aşamalı"""
        import re
        
        scraper = self.scrapers.get('kitapyurdu')
        if not scraper:
            logger.error("❌ Kitapyurdu scraper bulunamadı")
            return None
        
        # ISBN varsa önce ISBN ile ara
        if isbn:
            try:
                result = await run_sync(scraper.search, isbn)
                if result:
                    logger.info(f"✅ ISBN ile bulundu: {isbn}")
                    return result
            except Exception as e:
                logger.debug(f"ISBN araması başarısız: {e}")
        
        # 1️⃣ TAM SORGU ile ara
        logger.info(f"🔍 [1/3] Tam sorgu: {query[:60]}...")
        try:
            result = await run_sync(scraper.search, query)
            if result:
                logger.info("✅ Tam sorgu ile bulundu")
                return result
        except Exception as e:
            logger.debug(f"Tam sorgu hatası: {e}")
        
        # 2️⃣ BASİTLEŞTİRİLMİŞ SORGU (uzantı ve boşluklar temizlendi)
        basit = re.sub(r'\.(epub|pdf)$', '', query, flags=re.IGNORECASE)
        basit = basit.replace('_', ' ').replace('-', ' ')
        basit = re.sub(r'\s+', ' ', basit).strip()
        
        if basit != query:
            logger.info(f"🔍 [2/3] Basit sorgu: {basit[:60]}...")
            try:
                result = await run_sync(scraper.search, basit)
                if result:
                    logger.info("✅ Basit sorgu ile bulundu")
                    return result
            except Exception as e:
                logger.debug(f"Basit sorgu hatası: {e}")
        
        # 3️⃣ TEMİZ SORGU (sayılar ve özel karakterler temizlendi)
        temiz = re.sub(r'[^\wğüşıöçĞÜŞİÖÇ\s]', ' ', basit)
        temiz = re.sub(r'\b\d+\b', '', temiz)  # Sayıları kaldır
        temiz = re.sub(r'\s+', ' ', temiz).strip()
        
        if temiz and temiz != basit:
            logger.info(f"🔍 [3/3] Temiz sorgu: {temiz[:60]}...")
            try:
                result = await run_sync(scraper.search, temiz)
                if result:
                    logger.info("✅ Temiz sorgu ile bulundu")
                    return result
            except Exception as e:
                logger.debug(f"Temiz sorgu hatası: {e}")
        
        logger.warning(f"❌ 3 aşamada da bulunamadı: {query[:60]}")
        return None    
    async def _enrich_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Kitap bilgilerini zenginleştir
        
        Zenginleştirme sırası:
        1. Goodreads (puan, tür, orijinal ad, seri)
        2. 1000Kitap (çevirmen, orijinal ad, seri)
        """
        logger.info("✨ Zenginleştirme başlatılıyor...")
        
        try:
            # Goodreads ile zenginleştir
            data = await self.enrich_with_goodreads(data, data.get("isbn"))
            
            # 1000Kitap ile zenginleştir
            data = await self.enrich_with_binkitap(data)
            
            logger.info("✅ Zenginleştirme tamamlandı")
        
        except Exception as e:
            logger.error(f"❌ Zenginleştirme hatası: {e}")
            # Hata olsa bile ana veriyi koru!
        
        return data
    
    async def enrich_with_goodreads(
        self, 
        data: Dict[str, Any], 
        isbn: str = None
    ) -> Dict[str, Any]:
        """
        Goodreads ile zenginleştir
        - Orijinal ad ➕
        - Puan
        - Tür
        - Seri ➕ (Türkçeleştirilmiş)
        - Açıklama
        """
        try:
            # Zenginleştirme gerekli mi kontrol et
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
            
            # 1️⃣ İlk olarak ISBN varsa ISBN ile ara
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
            
            # 2️⃣ ISBN yoksa veya ISBN'de bulunamadıysa başlık+yazar ile ara
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
                
                # Orijinal ad
                if not data.get("orijinal_ad") and gr_result.get("orijinal_ad"):
                    data["orijinal_ad"] = gr_result["orijinal_ad"]
                    updated = True
                    logger.info(f"   ➕ Orijinal Ad: {data['orijinal_ad']}")
                
                # Tür
                if not data.get("turu") and gr_result.get("turu"):
                    data["turu"] = gr_result["turu"]
                    updated = True
                    logger.info(f"   ➕ Tür: {data['turu']}")
                
                # Puan
                if not data.get("puan") and gr_result.get("puan"):
                    data["puan"] = gr_result["puan"]
                    data["oy_sayisi"] = gr_result.get("oy_sayisi")
                    updated = True
                    logger.info(f"   ➕ Puan: {data['puan']} ({data.get('oy_sayisi')} oy)")
                
                # ➕ Seri (Türkçeleştirilmiş)
                if gr_result.get("seri"):
                    existing_series = data.get("seri")
                    translated_series = translate_series_name(gr_result["seri"])
                    final_series = prefer_turkish_series(existing_series, translated_series)
                    
                    if final_series and final_series != existing_series:
                        data["seri"] = final_series
                        updated = True
                        logger.info(f"   ➕ Seri: {data['seri']}")
                
                # Açıklama
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
        """
        1000Kitap ile zenginleştir
        - Orijinal ad ➕
        - Çevirmen ➕
        - Seri ➕ (Zaten Türkçe)
        """
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
# 🎯 Singleton Instance (ÖNEMLİ!)
# ========================================
book_service = BookService()