"""
Seri adı işleme yardımcıları
"""
import re
from typing import Optional
from config.series_translations import SERIES_TRANSLATIONS, SERIES_ALIASES

def normalize_series_name(series_name: str) -> str:
    """
    Seri adını normalize et (küçük harf, whitespace temizle)
    
    ⚠️ İngilizce seriler için basit .lower() kullan
    """
    if not series_name:
        return ""
    
    # Küçük harfe çevir (basit lowercase, Türkçe sorun çıkarmaz)
    normalized = series_name.lower()
    
    # Fazla boşlukları temizle
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    
    # Noktalama işaretlerini temizle
    normalized = re.sub(r'[\'"""'']', '', normalized)
    
    # Alias kontrolü
    if normalized in SERIES_ALIASES:
        normalized = SERIES_ALIASES[normalized]
    
    return normalized


def translate_series_name(series: str) -> str:
    """
    Seri adını İngilizce'den Türkçe'ye çevir
    
    Format: "Series Name #X" veya "Series Name"
    
    Args:
        series: Seri adı (ör: "Dune #1" veya "Foundation")
    
    Returns:
        Türkçeleştirilmiş seri adı
    
    Examples:
        >>> translate_series_name("Dune #1")
        "Dune Kum Gezegeni #1"
        
        >>> translate_series_name("The Lord of the Rings #1")
        "Yüzüklerin Efendisi #1"
        
        >>> translate_series_name("Harry Potter #3")
        "Harry Potter #3"
    """
    if not series:
        return series
    
    # Seri formatını parse et: "Seri Adı #X"
    match = re.match(r'^(.+?)\s*#(\d+)$', series)
    
    if match:
        series_name = match.group(1).strip()
        series_number = match.group(2)
        
        # Normalize et ve çeviri ara
        normalized = normalize_series_name(series_name)
        
        if normalized in SERIES_TRANSLATIONS:
            turkish_name = SERIES_TRANSLATIONS[normalized]
            return f"{turkish_name} #{series_number}"
        
        # Çeviri yoksa orijinali döndür
        return series
    else:
        # Numara yoksa sadece isim
        normalized = normalize_series_name(series)
        
        if normalized in SERIES_TRANSLATIONS:
            return SERIES_TRANSLATIONS[normalized]
        
        return series


def prefer_turkish_series(series1: Optional[str], series2: Optional[str]) -> Optional[str]:
    """
    İki seri adından Türkçe olanı tercih et
    
    Args:
        series1: İlk seri adı (genelde 1000Kitap'tan)
        series2: İkinci seri adı (genelde Goodreads'ten)
    
    Returns:
        Tercih edilen seri adı
    """
    if not series1 and not series2:
        return None
    
    if not series1:
        return translate_series_name(series2)
    
    if not series2:
        return series1
    
    # İkisi de varsa, Türkçe olan öncelikli
    # Basit kontrol: Türkçe karakterler var mı?
    turkish_chars = set('çğıöşüÇĞİÖŞÜ')
    
    has_turkish1 = any(c in turkish_chars for c in series1)
    has_turkish2 = any(c in turkish_chars for c in series2)
    
    if has_turkish1 and not has_turkish2:
        return series1
    elif has_turkish2 and not has_turkish1:
        return series2
    
    # İkisi de Türkçe veya ikisi de değilse, ilki tercih edilir (1000Kitap)
    if series1:
        return series1
    
    return translate_series_name(series2)