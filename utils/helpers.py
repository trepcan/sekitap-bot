import asyncio
import functools
import logging
from typing import Optional, Dict, Any
from config.constants import TUR_CEVIRI, YASAKLI_TURLER, UZUN_TUR_ISTISNALARI

logger = logging.getLogger(__name__)


async def run_sync(func, *args, **kwargs):
    """Senkron fonksiyonu async olarak çalıştır"""
    loop = asyncio.get_event_loop()
    pfunc = functools.partial(func, *args, **kwargs)
    return await loop.run_in_executor(None, pfunc)


def tur_cevir_ve_filtrele(tur_listesi: list) -> Optional[str]:
    """Türleri çevir ve filtrele"""
    if not tur_listesi:
        return None
    
    formatted_genres = []
    
    for g in tur_listesi:
        raw_genre = g.strip()
        
        # Yasaklı türleri atla
        if any(banned in raw_genre.lower() for banned in YASAKLI_TURLER):
            continue
        
        # Çeviri yap
        translated_genre = TUR_CEVIRI.get(
            raw_genre,
            TUR_CEVIRI.get(raw_genre.replace(" ", ""), raw_genre)
        )
        
        clean_g = translated_genre.replace(" ", "")
        
        # İstisna kontrolü
        is_exception = any(
            exc.lower() in clean_g.lower() 
            for exc in UZUN_TUR_ISTISNALARI
        )
        
        # Uzun türleri atla (istisnalar hariç)
        if len(clean_g) > 12 and not is_exception:
            continue
        
        if clean_g and f"#{clean_g}" not in formatted_genres:
            formatted_genres.append(f"#{clean_g}")
        
        if len(formatted_genres) >= 5:
            break
    
    return " ".join(formatted_genres) if formatted_genres else None


def basit_bilgi_cikar(metin: str) -> Dict[str, str]:
    """Dosya adından basit bilgi çıkar"""
    from utils.text_utils import turkce_baslik
    
    orijinal_temiz = metin.replace('.pdf', '').replace('.epub', '').replace('_', ' ')
    parcalar = orijinal_temiz.split('-')
    
    yazar = "Bilinmiyor"
    kitap = turkce_baslik(orijinal_temiz)
    
    if len(parcalar) >= 2:
        yazar = turkce_baslik(parcalar[0].strip())
        kitap = turkce_baslik("-".join(parcalar[1:]).strip())
    
    return {"yazar": yazar, "baslik": kitap}