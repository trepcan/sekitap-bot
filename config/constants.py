"""Sabit değerler"""

# HTTP Headers
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
    'Connection': 'keep-alive'
}

# Gürültü Kelimeleri
GURULTU_KELIMELERI = [
    "yayınları", "yayınevi", "yayıncılık", "yayın", "kitabevi", "kitaplığı",
    "can yayınları", "can yayın", "remzi kitabevi", "remzi yayınları",
    "bilgi yayınevi", "bilgi yayınları", "dost kitabevi", "dost yayınları",
    "iletişim yayınları", "metis yayınları", "doğan kitap", "yapı kredi",
    "yky yayınları", "yky", "timaş", "pegasus yayınları",
    "bütün eserleri", "toplu eserler", "seçme eserler", "tüm eserleri",
    "bütün öyküleri", "toplu öyküler", "toplu şiirler", "bütün şiirleri",
    "modern klasikler", "dünya klasikleri", "türk klasikleri",
    "bls", "pdf", "epub", "okunmadı", "tam metin", "cilt", "baskı"
]

# Yasaklı Türler
YASAKLI_TURLER = [
    "audiobook", "audible", "sesli kitap", "audio", "cd", "kaset",
    "ebooks", "bookclub", "book club"
]

# Uzun Tür İstisnaları
UZUN_TUR_ISTISNALARI = [
    "historical fiction", "science fiction", "artificial intelligence",
    "tarihsel kurgu", "bilim kurgu", "yapay zeka", "magicalrealism"
]

# Tür Çevirisi Sözlüğü
TUR_CEVIRI = {
    "MagicalRealism": "BüyülüGerçeklik",
    "Magic": "Büyü",
    "ShortStories": "KısaÖyküler",
    "Fiction": "Kurmaca",
    "Historical Fiction": "TarihselKurgu",
    "HistoricalFiction": "TarihselKurgu",
    "Economics": "Ekonomi",
    "Nonfiction": "Kurgudışı",
    "Politics": "Politika",
    "History": "Tarih",
    "Business": "İş",
    "Literature": "EdebiRoman",
    "Art": "Sanat",
    "Mystery": "Gizem",
    "Thriller": "Gerilim",
    "Crime": "Polisiye",
    "Suspense": "MerakUyandırıcı",
    "Fantasy": "Fantastik",
    "SpaceOpera": "UzayOperası",
    "Novels": "Roman",
    "Romance": "Aşk",
    "YoungAdult": "GençYetişkin",
    "Psychology": "Psikoloji",
    "Horror": "Korku",
    "Technology": "Teknoloji",
    "Classics": "Klasikler",
    "Adventure": "Macera",
    "Poetry": "Şiir",
    "Philosophy": "Felsefe",
    "Biography": "Biyografi",
    "ScienceFiction": "BilimKurgu",
    "Science Fiction": "BilimKurgu",
    "ArtificialIntelligence": "YapayZeka",
    "Artificial Intelligence": "YapayZeka",
}

# Veri Şablonu
def veri_kalibi():
    """Kitap verisi için boş şablon"""
    return {
        "baslik": None,
        "yazar": None,
        "aciklama": None,
        "seri": None,
        "yayinevi": None,
        "cevirmen": None,
        "orijinal_ad": None,
        "tarih": None,
        "isbn": None,
        "sayfa": None,
        "link": None,
        "turu": None,
        "puan": None,
        "oy_sayisi": None
    }
