"""Sabit değerler"""

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
    'Connection': 'keep-alive'
}

GURULTU_KELIMELERI = [
    "yayınları", "yayınevi", "yayıncılık", "yayın", "kitabevi",
    "bütün eserleri", "toplu eserler", "bls", "pdf", "epub", "okunmadı"
]

YASAKLI_TURLER = ["audiobook", "audible", "sesli kitap", "audio"]
UZUN_TUR_ISTISNALARI = ["historical fiction", "science fiction", "artificial intelligence"]

TUR_CEVIRI = {
    "Fiction": "Kurmaca", "HistoricalFiction": "TarihselKurgu",
    "ScienceFiction": "BilimKurgu", "Mystery": "Gizem",
    "Thriller": "Gerilim", "Romance": "Aşk", "Fantasy": "Fantastik"
}

def veri_kalibi():
    return {
        "baslik": None, "yazar": None, "aciklama": None, "seri": None,
        "yayinevi": None, "cevirmen": None, "orijinal_ad": None,
        "tarih": None, "isbn": None, "sayfa": None, "link": None,
        "turu": None, "puan": None, "oy_sayisi": None
    }
