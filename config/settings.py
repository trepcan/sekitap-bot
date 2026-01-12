"""Bot konfigürasyon ayarları"""
import os
import sys
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()

if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass


class Settings:
    SURUM = "v9.0 (Modüler Mimari)"
    API_ID: int = int(os.getenv('TELEGRAM_API_ID', 0))
    API_HASH: str = os.getenv('TELEGRAM_API_HASH', '')
    
    ADMIN_ID: Optional[int] = None
    try:
        ADMIN_ID = int(os.getenv('BOT_ADMIN_ID', 0))
    except (TypeError, ValueError):
        pass
    
    HEDEF_KANALLAR: List[int] = []
    kanallar_str = os.getenv('HEDEF_KANALLAR', '')
    if kanallar_str:
        HEDEF_KANALLAR = [int(k.strip()) for k in kanallar_str.split(',') if k.strip()]
    else:
        HEDEF_KANALLAR = [-1003184032013]
    
    KANAL_ISIMLERI = {-1003184032013: "sEkitap Arşivi"}
    
    GECMIS_TARAMA_AKTIF: bool = os.getenv('GECMIS_TARAMA_AKTIF', 'false').lower() == 'true'
    ZORLA_GUNCELLEME_MODU: bool = os.getenv('ZORLA_GUNCELLEME_MODU', 'false').lower() == 'true'
    
    MAX_LOG_BOYUTU_MB: int = int(os.getenv('MAX_LOG_BOYUTU_MB', 5))
    BENZERLIK_ORANI: float = float(os.getenv('BENZERLIK_ORANI', 0.35))
    KELIME_ESLESME_ORANI: float = float(os.getenv('KELIME_ESLESME_ORANI', 0.65))
    
    DB_FILE: str = os.getenv('DB_FILE', 'kitap_onbellek.db')
    CACHE_TTL: int = int(os.getenv('CACHE_TTL', 168))
    
    REQUEST_TIMEOUT: int = 15
    RATE_LIMIT_DELAY: float = 0.5
    
    @classmethod
    def validate(cls) -> bool:
        if not cls.API_ID or not cls.API_HASH:
            print("HATA: Telegram API bilgileri eksik!")
            return False
        return True


settings = Settings()
