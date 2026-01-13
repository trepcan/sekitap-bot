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
UZUN_TUR_ISTISNALARI = [
    # İngilizce Terimler (> 10 Karakter)
    "magicalrealism", "shortstories", "historical fiction", "historicalfiction",
    "nonfiction", "literature", "merakuyandırıcı", "spaceopera", 
    "youngadult", "psychology", "technology", "philosophy", "biography",
    "sciencefiction", "science fiction", "artificialintelligence", 
    "artificial intelligence", "spirituality", "cooking", "food and drink", 
    "autobiography", "environment", "astronomy", "mathematics", "childrens", 
    "middle grade", "picture books", "graphic novels", "contemporary", 
    "mythology", "true crime", "anthropology", "sociology", "Romantasy", "literaryfiction", "paranormalromance", "urbanfantasy", "self improvement", 
    "inspirational", "investigativejournalism", "politicalscience", "socialsciences",
    "internationalrelations", "sustainability", "architecture", "middlegrade",
    "graphicnovels", "christianfiction", "womensfiction", "culturalstudies",

    # Türkçe Karşılıklar (> 10 Karakter)
    "büyülügerçeklik", "kısaöyküler", "tarihselkurgu", "kurgudışı", 
    "edebiroman", "merakuyandırıcı", "uzayoperası", "gençyetişkin", 
    "psikoloji", "teknoloji", "klasikler", "biyografi", "bilimkurgu", 
    "yapayzeka", "kişiselgelişim", "spiritüellik", "yemekkitapları", 
    "yiyecekveiçecek", "otobiyografi", "astronomi", "matematik", 
    "çocukkitapları", "ortaokulseviyesi", "resimlikitaplar", "grafikroman", 
    "çizgiroman", "günümüzedebiyatı", "mitoloji", "gerçeksuç", 
    "tiyatrooyunları", "sosyoloji", "antropoloji", "AşkveFantastik", "edebikurmaca", "paranormalaşk", "şehirfantastiği", "kişiselgelişim",
    "ilhamverici", "araştırmacıgazetecilik", "siyasetbilimi", "sosyalbilimler",
    "uluslararasıilişkiler", "sürdürülebilirlik", "kadınyazını", "kültürelçalışmalar"
]

TUR_CEVIRI = {
    # Mevcutlar ve Varyasyonlar
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
    "Romantasy":"AşkveFantastik",
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

    # --- Yeni Eklenebilecekler ---
    
    # Kişisel Gelişim ve Yaşam
    "Self Help": "KişiselGelişim",
    "SelfHelp": "KişiselGelişim",
    "Health": "Sağlık",
    "Spirituality": "Spiritüellik",
    "Religion": "Din",
    "Travel": "Gezi",
    "Cooking": "YemekKitapları",
    "Food and Drink": "YiyecekVeİçecek",
    "Memoir": "Anı",
    "Autobiography": "Otobiyografi",

    # Bilim ve Doğa
    "Science": "Bilim",
    "Nature": "Doğa",
    "Environment": "Çevre",
    "Astronomy": "Astronomi",
    "Physics": "Fizik",
    "Biology": "Biyoloji",
    "Mathematics": "Matematik",

    # Çocuk ve Gençlik
    "Childrens": "ÇocukKitapları",
    "Middle Grade": "OrtaOkulSeviyesi",
    "Picture Books": "ResimliKitaplar",
    "Graphic Novels": "GrafikRoman",
    "Comics": "ÇizgiRoman",
    "Manga": "Manga",

    # Alt Türler ve Diğerleri
    "Contemporary": "GünümüzEdebiyatı",
    "Dystopia": "Distopya",
    "Utopia": "Ütopya",
    "Mythology": "Mitoloji",
    "True Crime": "GerçekSuç",
    "Humor": "Mizah",
    "Satire": "Hiciv",
    "War": "Savaş",
    "Western": "VahşiBatı",
    "Essays": "Denemeler",
    "Plays": "TiyatroOyunları",
    "Sociology": "Sosyoloji",
    "Anthropology": "Antropoloji",
    
    # --- Goodreads Temelli Yeni Eklemeler ---
    "Literary Fiction": "EdebiKurmaca",
    "LiteraryFiction": "EdebiKurmaca",
    "Paranormal Romance": "ParanormalAşk",
    "Urban Fantasy": "ŞehirFantastiği",
    "Self Improvement": "KişiselGelişim",
    "Inspirational": "IlhamVerici",
    "Investigative Journalism": "AraştırmacıGazetecilik",
    "Political Science": "SiyasetBilimi",
    "Social Sciences": "SosyalBilimler",
    "International Relations": "Uluslararasıİlişkiler",
    "Sustainability": "Sürdürülebilirlik",
    "Architecture": "Mimarlık",
    "Christian Fiction": "HristiyanKurgusu",
    "Womens Fiction": "KadınYazını",
    "Cultural Studies": "KültürelÇalışmalar",
    "Music": "Müzik",
    "Gardening": "Bahçecilik",
    "Sports": "Spor",
    "Finance": "Finans"
}

def veri_kalibi():
    return {
        "baslik": None, "yazar": None, "aciklama": None, "seri": None,
        "yayinevi": None, "cevirmen": None, "orijinal_ad": None,
        "tarih": None, "isbn": None, "sayfa": None, "link": None,
        "turu": None, "puan": None, "oy_sayisi": None
    }
