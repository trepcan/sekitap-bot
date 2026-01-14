"""Sabit değerler"""

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
    'Connection': 'keep-alive'
}

GURULTU_KELIMELERI = [
    # Mevcutlar
    "yayınları", "yayınevi", "yayıncılık", "yayın", "kitabevi",
    "bütün eserleri", "toplu eserler", "bls", "pdf", "epub", "okunmadı",
    
    # --- Senin Verdiklerin ve Varyasyonları ---
    "cs", "[cs]", "-cs", "_cs", "okundu", "okunmadı", "_okundu", "v1", "v2", "v3",
    "pdf", "epub", "mobi", "azw3", "yayınları", "yayınevi", "yayın", "kitabevi", "_ham",

    # --- Dijital Arşiv Etiketleri (Release Tags) ---
    "indir", "download", "yandex", "drive", "cloud", "share", "full", "tam-metin",
    "scan", "taranmış", "ocr", "ocred", "temiz", "600dpi", "300dpi", "hq",
    "ebook", "e-kitap", "ekitap", "digital", "web-dl", "retail", "fix",

    # --- Versiyon ve Düzenleme Notları ---
    "revised", "güncellenmiş", "genişletilmiş", "son", "final", "taslak", "draft",
    "copy", "kopya", "sample", "örnek", "demo", "preview", "tanıtım",
    "v1.0", "v2.0",  "v1", "v2",  "v3", "v4",  "new-edition", "edit", "edited", "düzeltilmiş",

    # --- Dil ve Çeviri Notları ---
    "tr", "eng", "en", "türkçe", "turkish", "çeviri", "cevirisi", "çev", "trans",
    "dual", "multi", "bilingual", "original", "orijinal",

    # --- Yayıncılık / Basım Detayları (Gürültü Yaratanlar) ---
    "baskı", "basim", "cilt", "ciltli", "kapak", "hardcover", "paperback",
    "1-baski", "10-baski", "yeni-baski", "meb", "is-bankasi", "can-yayinlari",
    "metis", "ithaki", "pegasus", "iletisim", "yky", # En çok gürültü yapan kısaltmalar

    # --- Gereksiz Karakter Kalıpları ---
    # Not: Bunlar genellikle bir temizleme fonksiyonuyla (regex) silinmelidir
    "---", "___", "...", "copy_of", "kitap-oku", "bedava-kitap", "arşiv", "arsiv",
    "arşivi", "arsivi", "kütüphane", "library", "collection"

    # --- Yayıncılık ve Basım Terimleri ---
    "baskı", "basım", "cilt", "ciltli", "ince kapak", "karton kapak",
    "özel baskı", "limited edition", "collector's edition", "revised edition",
    "genişletilmiş baskı", "tıpkıbasım", "facsimile", "birinci baskı",
    "hardcover", "paperback", "mass market", "cep boy", "prestij boy",

    # --- Dijital ve Dosya Formatı Varyasyonları ---
    "mobi", "azw3", "djvu", "ebook", "e-kitap", "ekitap", "indir", "download",
    "zip", "rar", "full izle", "oku", "ücretsiz", "bedava",

    # --- Akademik ve Dokümantasyon ---
    "tez", "makale", "sempozyum", "bildiri", "rapor", "çalışma kağıdı",
    "working paper", "proceedings", "doktora tezi", "yüksek lisans tezi",
    "dergi", "sayı", "cilt no", "issn", "isbn", "doi",

    # --- Temizlik Gerektiren Ekler/Kısaltmalar ---
    "hazırlayan", "derleyen", "çeviren", "çeviri", "editör", "editor",
    "yayına hazırlayan", "resimleyen", "illüstrasyon", "katkıda bulunan",
    "anonim", "anonymous", "et al", "ve diğerleri",

    # --- Kütüphane ve Raf Notları ---
    "kopya", "copy", "demo", "örnek", "sample", "tanıtım bülteni",
    "arka kapak", "içindekiler", "index", "dizin", "kaynakça",
    "taranmış", "scanned", "ocr", "temiz", "ikinci el", "sahaf"
]

YASAKLI_TURLER = ["audiobook", "audible", "sesli kitap", "audio"]
UZUN_TUR_ISTISNALARI = [
    # --- İNGİLİZCE TERİMLER (> 10 Karakter) ---
    "anthropology", "architecture", "artificial intelligence", "artificialintelligence",
    "astronomy", "autobiography", "billionaire romance", "billionaireromance",
    "biography", "childrens", "christian fiction", "christianfiction",
    "classic literature", "climate fiction", "climatefiction", "contemporary",
    "cozy mystery", "cozymystery", "cultural studies", "culturalstudies",
    "cyberpunk", "dark fantasy", "dark romance", "darkromance",
    "enemies to lovers", "enemiestolovers", "entrepreneurship", "environment",
    "environmentalism", "experimental", "food and drink", "found family",
    "foundfamily", "gothic horror", "gothichorror", "graphic novels",
    "graphicnovel", "graphicnovels", "high fantasy", "historical fiction",
    "historical romance", "historicalfiction", "historicalromance", "inspirational",
    "international", "international relations", "internationalrelations",
    "investigative journalism", "investigativejournalism", "journalism", "leadership",
    "literary criticism", "literary fiction", "literaryfiction", "literature",
    "mafia romance", "mafiaromance", "magicalrealism", "mathematics",
    "mental health", "mentalhealth", "middle grade", "middlegrade", "mythology",
    "neuroscience", "nonfiction", "office romance", "officeromance", "omegaverse",
    "paleontology", "paranormal romance", "paranormalromance", "philosophy",
    "photography", "picture book", "picture books", "picturebook",
    "political science", "politicalscience", "postapocalyptic",
    "psychological thriller", "psychologicalthriller", "psychology",
    "queer fiction", "queerfiction", "reverse harem", "reverseharem",
    "romantasy", "romantic comedy", "science fiction", "sciencefiction",
    "self improvement", "shifter romance", "shifterromance", "short stories",
    "shortstories", "slow burn", "slowburn", "social justice", "social sciences",
    "socialsciences", "sociology", "space opera", "spaceopera", "spirituality",
    "sports romance", "sportsromance", "sustainability", "technology",
    "true adventure", "true crime", "trueadventure", "urban fantasy",
    "urbanfantasy", "vampire romance", "vampireromance", "womens fiction",
    "womensfiction", "young adult", "youngadult",

    # --- TÜRKÇE KARŞILIKLAR (> 10 Karakter) ---
    "antropoloji", "araştırmacıgazetecilik", "arkeoloji", "astronomi", "aşkvefantastik",
    "bilimkurgu", "biyografi", "büyülügerçeklik", "çevrecilik", "çizgiroman",
    "çocukkitapları", "denemeler", "deneyselyazın", "değişenaşk", "distopya",
    "düşmanlıktanaşka", "edebieleştiri", "edebikurmaca", "edebiroman", "felsefe",
    "fotoğrafçılık", "gazetecilik", "gençyetişkin", "gerçekmacera", "gerçeksuç",
    "girişimcilik", "gotikkorku", "grafikroman", "günümüzedebiyatı", "hiciv",
    "hristiyankurgusu", "iklimkurgusu", "ilhamverici", "kadınyazını", "karanlıkaşk",
    "karanlıkfantastik", "kendisesinden", "kısaöyküler", "kişiselgelişim",
    "klasikedebiyat", "klasikler", "kurgudışı", "kültürelçalışmalar", "liderlik",
    "mafyaaşkı", "matematik", "merakuyandırıcı", "milyarderaşkı", "mitoloji",
    "nörobilim", "ofisaşkı", "omegaverse", "ortaokulseviyesi", "otobiyografi",
    "paleontoloji", "paranormalaşk", "postapokaliptik", "psikoloji",
    "psikolojikgerilim", "rahatpolisiye", "resimlikitaplar", "romantikfantastik",
    "romantikkomedi", "ruhsağlığı", "seçilmişaile", "şehirfantastiği", "siyasetbilimi",
    "sosyaladalet", "sosyalbilimler", "sosyoloji", "sporaşkı", "spiritüellik",
    "sürdürülebilirlik", "tarihselaşk", "tarihselkurgu", "teknoloji",
    "tiyatrooyunları", "uluslararası", "uluslararasıilişkiler", "uzayoperası",
    "vampiraşkı", "yapayzeka", "yavaşyananaşk", "yemekkitapları", "yiyecekveiçecek"
]

TUR_CEVIRI = {
    # Kurgu ve Ana Türler
    "Magical Realism": "BüyülüGerçeklik",
    "MagicalRealism": "BüyülüGerçeklik",
    "Magic": "Büyü",
    "Short Stories": "KısaÖyküler",
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
    "Space Opera": "UzayOperası",
    "SpaceOpera": "UzayOperası",
    "Novels": "Roman",
    "Romance": "Aşk",
    "Romantasy": "RomantikFantastik",
    "Young Adult": "GençYetişkin",
    "YoungAdult": "GençYetişkin",
    "Psychology": "Psikoloji",
    "Horror": "Korku",
    "Technology": "Teknoloji",
    "Classics": "Klasikler",
    "Adventure": "Macera",
    "Poetry": "Şiir",
    "Philosophy": "Felsefe",
    "Biography": "Biyografi",
    "Science Fiction": "BilimKurgu",
    "ScienceFiction": "BilimKurgu",
    "Artificial Intelligence": "YapayZeka",
    "ArtificialIntelligence": "YapayZeka",
    "Experimental": "DeneyselYazın",
    "Post Apocalyptic": "PostApokaliptik",
    "Steampunk": "Steampunk",
    "Cyberpunk": "Cyberpunk",
    "High Fantasy": "YüksekFantastik",
    "Historical Romance": "TarihselAşk",
    "Romantic Comedy": "RomantikKomedi",
    "Rom-Com": "RomantikKomedi",
    "Psychological Thriller": "PsikolojikGerilim",
    "Dark Fantasy": "KaranlıkFantastik",
    "Urban Fantasy": "ŞehirFantastiği",
    "Classic Literature": "KlasikEdebiyat",

    # Kişisel Gelişim, Sağlık ve Yaşam
    "Self Help": "KişiselGelişim",
    "SelfHelp": "KişiselGelişim",
    "Self Improvement": "KişiselGelişim",
    "Health": "Sağlık",
    "Mental Health": "RuhSağlığı",
    "MentalHealth": "RuhSağlığı",
    "Spirituality": "Spiritüellik",
    "Religion": "Din",
    "Travel": "Gezi",
    "Cooking": "YemekKitapları",
    "Food and Drink": "YiyecekVeİçecek",
    "Memoir": "Anı",
    "Autobiography": "Otobiyografi",
    "Inspirational": "IlhamVerici",

    # Bilim, Doğa ve Akademi
    "Science": "Bilim",
    "Nature": "Doğa",
    "Environment": "Çevre",
    "Environmentalism": "Çevrecilik",
    "Astronomy": "Astronomi",
    "Physics": "Fizik",
    "Biology": "Biyoloji",
    "Mathematics": "Matematik",
    "Paleontology": "Paleontoloji",
    "Neuroscience": "Nörobilim",
    "Archaeology": "Arkeoloji",
    "Political Science": "SiyasetBilimi",
    "Social Sciences": "SosyalBilimler",
    "International Relations": "Uluslararasıİlişkiler",
    "Sustainability": "Sürdürülebilirlik",
    "Sociology": "Sosyoloji",
    "Anthropology": "Antropoloji",
    "Literary Criticism": "EdebiEleştiri",
    "Social Justice": "SosyalAdalet",
    "Language":"Dil",
    "Medicine":"İlaç",

    # Formatlar ve Yaş Grupları
    "Childrens": "ÇocukKitapları",
    "Middle Grade": "OrtaOkulSeviyesi",
    "Middlegrade": "OrtaOkulSeviyesi",
    "Picture Book": "ResimliKitaplar",
    "Picture Books": "ResimliKitaplar",
    "Graphic Novel": "GrafikRoman",
    "Graphic Novels": "GrafikRoman",
    "Comics": "ÇizgiRoman",
    "Manga": "Manga",
    "Audiobook": "SesliKitap",

    # Goodreads Popüler Tropelar ve Trendler (2025-2026)
    "Cozy Mystery": "RahatPolisiye",
    "CozyMystery": "RahatPolisiye",
    "Cli Fi": "İklimKurgusu",
    "CliFi": "İklimKurgusu",
    "Climate Fiction": "İklimKurgusu",
    "Enemies to Lovers": "DüşmanlıktanAşka",
    "EnemiesToLovers": "DüşmanlıktanAşka",
    "Found Family": "SeçilmişAile",
    "FoundFamily": "SeçilmişAile",
    "Slow Burn": "YavaşYananAşk",
    "SlowBurn": "YavaşYananAşk",
    "Sports Romance": "Sporaşkı",
    "SportsRomance": "Sporaşkı",
    "Dark Romance": "KaranlıkAşk",
    "DarkRomance": "KaranlıkAşk",
    "Mafia Romance": "MafyaAşkı",
    "MafiaRomance": "MafyaAşkı",
    "Reverse Harem": "TersHarem",
    "ReverseHarem": "TersHarem",
    "Omegaverse": "Omegaverse",
    "Shifter Romance": "Değişenaşk",
    "ShifterRomance": "Değişenaşk",
    "Vampire Romance": "Vampiraşkı",
    "Vampireromance": "Vampiraşkı",
    "LGBT Romance": "LGBTAşk",
    "Queer Fiction": "QueerKurgu",
    "Billionaire Romance": "Milyarderaşkı",
    "Billionaireromance": "Milyarderaşkı",
    "Office Romance": "OfisAşkı",
    "OfficeRomance": "OfisAşkı",
    "Gothic Horror": "GotikKorku",
    "Own Voices": "KendiSesinden",

    # Diğer Alt Türler
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
    "Literary Fiction": "EdebiKurmaca",
    "Paranormal Romance": "ParanormalAşk",
    "Investigative Journalism": "AraştırmacıGazetecilik",
    "Architecture": "Mimarlık",
    "Christian Fiction": "HristiyanKurgusu",
    "Womens Fiction": "KadınYazını",
    "Cultural Studies": "KültürelÇalışmalar",
    "Music": "Müzik",
    "Gardening": "Bahçecilik",
    "Sports": "Spor",
    "Finance": "Finans",
    "Law": "Hukuk",
    "Design": "Tasarım",
    "Photography": "Fotoğrafçılık",
    "Leadership": "Liderlik",
    "Entrepreneurship": "Girişimcilik",
    "Journalism": "Gazetecilik",
    "Reference": "Referans",
    "True Adventure": "GerçekMacera"
}

def veri_kalibi():
    return {
        "baslik": None, "yazar": None, "aciklama": None, "seri": None,
        "yayinevi": None, "cevirmen": None, "orijinal_ad": None,
        "tarih": None, "isbn": None, "sayfa": None, "link": None,
        "turu": None, "puan": None, "oy_sayisi": None
    }
