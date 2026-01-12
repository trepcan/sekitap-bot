import re
import html
import difflib
from typing import Optional
import ftfy
from bs4 import BeautifulSoup

from config.constants import GURULTU_KELIMELERI


def turkce_kucult(metin: str) -> str:
    """Türkçe karakterlere duyarlı küçültme"""
    if not metin:
        return ""
    return metin.replace('I', 'ı').replace('İ', 'i').lower()


def turkce_baslik_yap(metin: str) -> Optional[str]:
    """Türkçe başlık formatı (Her Kelimenin İlk Harfi Büyük)"""
    if not metin:
        return None
    
    kucuk = turkce_kucult(metin)
    kelimeler = kucuk.split()
    yeni_kelimeler = []
    
    for kelime in kelimeler:
        if not kelime:
            continue
        
        ilk_harf = kelime[0]
        geri_kalan = kelime[1:]
        
        if ilk_harf == 'i':
            ilk_harf = 'İ'
        elif ilk_harf == 'ı':
            ilk_harf = 'I'
        else:
            ilk_harf = ilk_harf.upper()
        
        yeni_kelimeler.append(ilk_harf + geri_kalan)
    
    return " ".join(yeni_kelimeler)


def metin_duzelt(metin: str) -> str:
    """HTML ve encoding sorunlarını düzelt"""
    if not metin:
        return ""
    
    try:
        # HTML tag'lerini temizle
        if "<" in str(metin) and ">" in str(metin):
            soup = BeautifulSoup(str(metin), 'html.parser')
            metin = soup.get_text(separator=' ')
    except:
        pass
    
    # HTML entity'leri çöz
    metin = html.unescape(str(metin))
    
    # Encoding problemlerini düzelt
    metin = ftfy.fix_text(metin)
    
    # Fazla boşlukları temizle
    metin = re.sub(r'\s+', ' ', metin).strip()
    
    return metin.strip()


def baslik_teknik_temizle(baslik: str) -> Optional[str]:
    """Başlıktan teknik bilgileri temizle"""
    if not baslik:
        return None
    
    regex = r'\s*\((?:Karton Kapak|Ciltli|İnce Kapak|Cep Boy|Büyük Boy|Ciltli Kapak|Tam Metin|Kutulu)\)'
    temiz = re.sub(regex, '', baslik, flags=re.IGNORECASE)
    return temiz.strip()


def turkce_baslik(metin: str) -> Optional[str]:
    """Tam başlık temizleme ve formatlama"""
    if not metin:
        return None
    
    metin = metin_duzelt(metin)
    metin = baslik_teknik_temizle(metin)
    return turkce_baslik_yap(metin)


def metni_temizle(metin: str, manuel_mod: bool = False) -> str:
    """Dosya adını veya arama metnini temizle"""
    # ISBN kontrolü
    saf_rakamlar = re.sub(r'[^\d]', '', metin)
    if len(saf_rakamlar) in [10, 13]:
        if re.match(r'^[\d\-\sX]+$', metin.strip(), re.IGNORECASE):
            return saf_rakamlar
    
    temiz = turkce_kucult(metin)
    
    if not manuel_mod:
        temiz = temiz.replace('.pdf', '').replace('.epub', '')
        temiz = re.sub(r'\b(19|20)\d{2}\b', '', temiz)
    
    # Teknik ekleri temizle
    temiz = re.sub(r'-km$', '', temiz)
    temiz = re.sub(r'(\[|\(|\{|_|-|\s)+(cs|ham|bls)(\]|\)|\}|\b)', '', temiz)
    temiz = temiz.replace('_okunmadı', '').replace('_okunmadi', '')
    
    # Parantez içlerini temizle
    temiz = re.sub(r'\(.*?\)', '', temiz)
    temiz = re.sub(r'\[.*?\]', '', temiz)
    temiz = re.sub(r'\{.*?\}', '', temiz)
    temiz = temiz.replace('_', ' ')
    
    # Gürültü kelimelerini çıkar
    for kelime in GURULTU_KELIMELERI:
        pattern = r'\b' + re.escape(kelime) + r'(\s+\d+)?\b'
        temiz = re.sub(pattern, '', temiz)
    
    genel_ekler_regex = r'\b\w+\s+(yayınları|yayınevi|yayıncılık|yayın|kitabevi|edebiyat)\b'
    temiz = re.sub(genel_ekler_regex, '', temiz)
    
    if not manuel_mod:
        # Yazar-Kitap formatını düzenle
        parcalar = temiz.split('-')
        if len(parcalar) >= 3:
            yeni_metin = f"{parcalar[0]} {parcalar[-1]}"
            temiz = " ".join(yeni_metin.split())
        else:
            temiz = temiz.replace('-', ' ')
        temiz = re.sub(r'\s+\d+$', '', temiz)
    
    return " ".join(temiz.split())


def benzerlik_orani(a: str, b: str) -> float:
    """İki metin arasındaki benzerlik oranı (0-1)"""
    if not a or not b:
        return 0.0
    return difflib.SequenceMatcher(None, turkce_kucult(a), turkce_kucult(b)).ratio()


def kelime_kumesi_orani(aranan: str, bulunan: str) -> float:
    """Kelime kümesi eşleşme oranı"""
    if not aranan or not bulunan:
        return 0.0
    
    def tokenize(text):
        text = turkce_kucult(text)
        return set(re.findall(r'\w+', text))
    
    aranan_set = tokenize(aranan)
    bulunan_set = tokenize(bulunan)
    
    if not aranan_set:
        return 0.0
    
    kesisim = aranan_set.intersection(bulunan_set)
    return len(kesisim) / len(aranan_set)


def isbn_bul(text: str) -> Optional[str]:
    """Metinden ISBN çıkar"""
    if not text:
        return None
    
    match = re.search(r'978[\d-]{10,14}', text)
    if match:
        return match.group(0).replace('-', '').replace(' ', '')
    return None


def durum_belirle(dosya_adi: str) -> str:
    """Dosya durumunu belirle"""
    ad = dosya_adi.lower()
    
    if ad.endswith('.epub'):
        if 'okunmadı' in ad or 'okunmadi' in ad:
            return "Okunmadı"
        if 'storytel' in ad:
            return "Storytel, Orijinal"
        if 'orj' in ad:
            return "Orijinal"
        return "Okundu"
    elif ad.endswith('.pdf'):
        if re.search(r'(?:^|[\s_\-\(\[])ham[\s_\-\)\]]*\.pdf$', ad):
            return "Ham Tarama"
        return "Clear Scan"
    
    return "-"