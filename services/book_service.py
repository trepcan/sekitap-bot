import asyncio
import re
import logging
from typing import Optional, Dict, Any, Tuple

from scrapers.kitapyurdu import KitapyurduScraper
from scrapers.binkitap import BinKitapScraper
from scrapers.goodreads import GoodreadsScraper
from utils.text_utils import metni_temizle, benzerlik_orani, kelime_kumesi_orani, turkce_kucult
from utils.helpers import run_sync, basit_bilgi_cikar
from database.db_manager import db
from config.settings import settings
from config.constants import veri_kalibi

logger = logging.getLogger(__name__)


class BookService:
    """Kitap arama ve veri zenginleştirme servisi"""
    
    def __init__(self):
        self.scrapers = {
            'kitapyurdu': KitapyurduScraper(),
            'binkitap': BinKitapScraper(),
            'goodreads': GoodreadsScraper(),
        }
    
    async def search_book(
        self, 
        search_text: str, 
        manuel_mod: bool = False
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str], Optional[str]]:
        """
        Kitap ara
        
        Returns:
            (kitap_verisi, kaynak_adi, temiz_arama_metni)
        """
        # URL ile arama
        if "http" in search_text:
            return await self._search_by_url(search_text)
        
        # Metni temizle
        temiz_ad = metni_temizle(search_text, manuel_mod)
        logger.info(f"🔎 Aranıyor: {temiz_ad}")
        
        # ISBN kontrolü
        is_isbn = temiz_ad.isdigit() and len(temiz_ad) in [10, 13]
        
        # Önbellek kontrolü (ISBN veya manuel mod değilse)
        if not manuel_mod and not is_isbn:
            cached = db.getir(temiz_ad)
            if cached:
                logger.info(f"💾 Önbellekten alındı: {temiz_ad}")
                return cached, "Önbellek", temiz_ad
        
        # Kaynaklarda ara
        sources = [
            ('kitapyurdu', 'Kitapyurdu'),
            ('binkitap', '1000Kitap'),
            ('goodreads', 'Goodreads'),
        ]
        
        for key, name in sources:
            # Rate limiting
            await asyncio.sleep(settings.RATE_LIMIT_DELAY)
            
            try:
                scraper = self.scrapers[key]
                
                # ISBN araması için özel işlem (Goodreads)
                if is_isbn and key == 'goodreads':
                    sonuc = await run_sync(scraper.search, temiz_ad, is_isbn_search=True)
                else:
                    sonuc = await run_sync(scraper.search, temiz_ad)
                
                if sonuc:
                    # Validasyon
                    if self._validate_result(sonuc, temiz_ad, is_isbn, manuel_mod):
                        logger.info(f"✅ Bulundu: {name} - {sonuc.get('baslik')}")
                        
                        # Önbelleğe kaydet
                        if not manuel_mod and not is_isbn:
                            db.kaydet(temiz_ad, sonuc)
                        
                        return sonuc, name, temiz_ad
                    else:
                        logger.debug(f"⚠️ Validasyon başarısız: {name}")
            
            except Exception as e:
                logger.error(f"❌ Hata ({name}): {e}")
                continue
        
        # Hiçbir kaynakta bulunamadı
        logger.warning(f"❌ Hiçbir kaynakta bulunamadı: {temiz_ad}")
        return None, None, None
    
    async def _search_by_url(
        self, 
        text: str
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str], Optional[str]]:
        """URL ile direkt arama"""
        # URL'yi çıkar
        match = re.search(r'(https?://\S+)', text)
        if not match:
            return None, None, None
        
        url = match.group(1)
        logger.info(f"🔗 URL ile arama: {url}")
        
        # URL'ye göre scraper seç
        if 'kitapyurdu.com' in url:
            scraper = self.scrapers['kitapyurdu']
            kaynak = "Kitapyurdu"
        elif '1000kitap.com' in url:
            scraper = self.scrapers['binkitap']
            kaynak = "1000Kitap"
        elif 'goodreads.com' in url:
            scraper = self.scrapers['goodreads']
            kaynak = "Goodreads"
        else:
            logger.warning(f"⚠️ Desteklenmeyen URL: {url}")
            return None, None, None
        
        try:
            result = await run_sync(scraper.search, None, direct_url=url)
            if result:
                logger.info(f"✅ URL'den bulundu: {kaynak}")
                return result, kaynak, None
        except Exception as e:
            logger.error(f"❌ URL arama hatası: {e}")
        
        return None, None, None
    
    def _validate_result(
        self, 
        sonuc: Dict[str, Any], 
        temiz_ad: str, 
        is_isbn: bool, 
        manuel_mod: bool
    ) -> bool:
        """Sonucu doğrula"""
        if not sonuc:
            return False
        
        # ISBN aramasıysa direkt ISBN karşılaştır
        if is_isbn:
            gelen_isbn = re.sub(r'\D', '', sonuc.get('isbn', '') or '')
            if gelen_isbn:
                return temiz_ad == gelen_isbn
            # ISBN gelmemişse manuel modda kabul et
            return manuel_mod
        
        # Manuel modsa doğrulama yapma
        if manuel_mod:
            return True
        
        # Başlık kontrolü
        if not sonuc.get('baslik'):
            return False
        
        # Basit substring kontrolü
        aranan = turkce_kucult(temiz_ad)
        bulunan_baslik = turkce_kucult(sonuc.get('baslik', ''))
        bulunan_yazar = turkce_kucult(sonuc.get('yazar', ''))
        bulunan_tam = f"{bulunan_baslik} {bulunan_yazar}"
        
        # Direkt içerme kontrolü
        if aranan in bulunan_tam or bulunan_baslik in aranan:
            return True
        
        # Benzerlik oranı kontrolü
        oran = benzerlik_orani(temiz_ad, bulunan_tam)
        if oran >= settings.BENZERLIK_ORANI:
            return True
        
        # Kelime kümesi eşleşme oranı
        kelime_oran = kelime_kumesi_orani(temiz_ad, bulunan_tam)
        if kelime_oran >= settings.KELIME_ESLESME_ORANI:
            return True
        
        return False
    
    def create_fallback_data(self, file_name: str) -> Dict[str, Any]:
        """Bulunamayan kitaplar için fallback veri oluştur"""
        basit = basit_bilgi_cikar(file_name)
        
        data = veri_kalibi()
        data.update(basit)
        data["aciklama"] = "Kitap bilgisi otomatik olarak bulunamadı."
        
        return data
    
    async def enrich_with_goodreads(
        self, 
        data: Dict[str, Any], 
        isbn: str = None
    ) -> Dict[str, Any]:
        """
        Goodreads ile zenginleştir (puan, tür, seri)
        """
        try:
            if not data.get("turu") or not data.get("puan"):
                # ISBN varsa ISBN ile ara
                if isbn or data.get("isbn"):
                    search_term = isbn or data.get("isbn")
                    is_isbn = True
                else:
                    # Başlık + yazar ile ara
                    search_term = f"{data.get('baslik', '')} {data.get('yazar', '')}".strip()
                    is_isbn = False
                
                if search_term:
                    scraper = self.scrapers['goodreads']
                    gr_result = await run_sync(
                        scraper.search, 
                        search_term, 
                        is_isbn_search=is_isbn
                    )
                    
                    if gr_result:
                        # Eksik alanları doldur
                        if not data.get("turu") and gr_result.get("turu"):
                            data["turu"] = gr_result["turu"]
                        if not data.get("puan") and gr_result.get("puan"):
                            data["puan"] = gr_result["puan"]
                            data["oy_sayisi"] = gr_result.get("oy_sayisi")
                        if not data.get("seri") and gr_result.get("seri"):
                            data["seri"] = gr_result["seri"]
                        if not data.get("aciklama") and gr_result.get("aciklama"):
                            data["aciklama"] = gr_result["aciklama"]
                        
                        logger.info("✨ Goodreads ile zenginleştirildi")
        
        except Exception as e:
            logger.error(f"❌ Goodreads zenginleştirme hatası: {e}")
        
        return data


# Global instance
book_service = BookService()