"""Metin işleme fonksiyonları"""
import re
import html
import difflib
from typing import Optional
import ftfy
from bs4 import BeautifulSoup
from config.constants import GURULTU_KELIMELERI


def turkce_kucult(metin: str) -> str:
    if not metin:
        return ""
    return metin.replace('I', 'ı').replace('İ', 'i').lower()


def turkce_baslik_yap(metin: str) -> Optional[str]:
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
    if not metin:
        return ""
    try:
        if "<" in str(metin) and ">" in str(metin):
            soup = BeautifulSoup(str(metin), 'html.parser')
            metin = soup.get_text(separator=' ')
    except:
        pass
    metin = html.unescape(str(metin))
    metin = ftfy.fix_text(metin)
    metin = re.sub(r'\s+', ' ', metin).strip()
    return metin.strip()


def baslik_teknik_temizle(baslik: str) -> Optional[str]:
    if not baslik:
        return None
    regex = r'\s*\((?:Karton Kapak|Ciltli|İnce Kapak|Cep Boy)\)'
    temiz = re.sub(regex, '', baslik, flags=re.IGNORECASE)
    return temiz.strip()


def turkce_baslik(metin: str) -> Optional[str]:
    if not metin:
        return None
    metin = metin_duzelt(metin)
    metin = baslik_teknik_temizle(metin)
    return turkce_baslik_yap(metin)


def metni_temizle(metin: str, manuel_mod: bool = False) -> str:
    saf_rakamlar = re.sub(r'[^\d]', '', metin)
    if len(saf_rakamlar) in [10, 13]:
        if re.match(r'^[\d\-\sX]+$', metin.strip(), re.IGNORECASE):
            return saf_rakamlar
    temiz = turkce_kucult(metin)
    if not manuel_mod:
        temiz = temiz.replace('.pdf', '').replace('.epub', '')
        temiz = re.sub(r'\b(19|20)\d{2}\b', '', temiz)
    temiz = re.sub(r'-km$', '', temiz)
    temiz = re.sub(r'(\[|\(|\{|_|-|\s)+(cs|ham|bls)(\]|\)|\}|\b)', '', temiz)
    temiz = temiz.replace('_okunmadı', '').replace('_okunmadi', '')
    temiz = re.sub(r'\(.*?\)', '', temiz)
    temiz = re.sub(r'\[.*?\]', '', temiz)
    temiz = temiz.replace('_', ' ')
    for kelime in GURULTU_KELIMELERI:
        pattern = r'\b' + re.escape(kelime) + r'(\s+\d+)?\b'
        temiz = re.sub(pattern, '', temiz)
    if not manuel_mod:
        parcalar = temiz.split('-')
        if len(parcalar) >= 3:
            yeni_metin = f"{parcalar[0]} {parcalar[-1]}"
            temiz = " ".join(yeni_metin.split())
        else:
            temiz = temiz.replace('-', ' ')
    return " ".join(temiz.split())


def benzerlik_orani(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return difflib.SequenceMatcher(None, turkce_kucult(a), turkce_kucult(b)).ratio()


def kelime_kumesi_orani(aranan: str, bulunan: str) -> float:
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
    if not text:
        return None
    match = re.search(r'978[\d-]{10,14}', text)
    if match:
        return match.group(0).replace('-', '').replace(' ', '')
    return None


def durum_belirle(dosya_adi: str) -> str:
    ad = dosya_adi.lower()
    if ad.endswith('.epub'):
        if 'okunmadı' in ad or 'okunmadi' in ad:
            return "Okunmadı"
        if 'storytel' in ad:
            return "Storytel, Orijinal"
        return "Okundu"
    elif ad.endswith('.pdf'):
        if re.search(r'(?:^|[\s_\-\(\[])ham[\s_\-\)\]]*\.pdf$', ad):
            return "Ham Tarama"
        return "Clear Scan"
    return "-"
# utils/text_utils.py

def dosya_adini_arama_icin_temizle(dosya_adi: str) -> str:
    """
    Dosya adını arama için optimize et
    
    Örnek:
        "Sarah J. Maas - Cam Şato 2 - Karanlık Taç.epub"
        → "Karanlık Taç Sarah J Maas"
    """
    
    # Uzantıyı kaldır
    ad = re.sub(r'\.(epub|pdf)$', '', dosya_adi, flags=re.IGNORECASE)
    
    # " - " ile böl (yazar - seri - kitap formatı)
    parcalar = ad.split(' - ')
    
    if len(parcalar) >= 3:
        yazar = parcalar[0].strip()
        kitap = parcalar[-1].strip()  # Son parça kitap adı
        return f"{kitap} {yazar}"  # Kitap adı önce
    
    elif len(parcalar) == 2:
        return f"{parcalar[1]} {parcalar[0]}"
    
    # Alt çizgileri boşluğa çevir
    ad = ad.replace('_', ' ')
    ad = re.sub(r'\s+', ' ', ad).strip()
    
    return ad
def temizle_dosya_adi(dosya_adi: str) -> str:
    """
    Dosya adını temizle ve normalize et
    
    Args:
        dosya_adi: Ham dosya adı
    
    Returns:
        Temizlenmiş dosya adı
    
    Examples:
        >>> temizle_dosya_adi("Harry_Potter_1.epub")
        'Harry Potter 1'
    """
    import re
    
    # Uzantıyı kaldır
    ad = re.sub(r'\.(epub|pdf)$', '', dosya_adi, flags=re.IGNORECASE)
    
    # Alt çizgi ve tire → boşluk
    ad = ad.replace('_', ' ').replace('-', ' ')
    
    # Birden fazla boşluk → tek boşluk
    ad = re.sub(r'\s+', ' ', ad).strip()
    
    return ad    