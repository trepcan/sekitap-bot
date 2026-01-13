"""Veritabanı yöneticisi"""
import sqlite3
import json
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging
from config.settings import settings

logger = logging.getLogger(__name__)


class DatabaseManager:
    def __init__(self, db_file: str = None):
        self.db_file = db_file or settings.DB_FILE
        self.initialize()
    
    def initialize(self):
        try:
            conn = sqlite3.connect(self.db_file)
            c = conn.cursor()
            c.execute("""
                CREATE TABLE IF NOT EXISTS kitaplar (
                    anahtar TEXT PRIMARY KEY,
                    veri TEXT,
                    tarih TEXT,
                    guncelleme_tarihi TEXT
                )
            """)
            conn.commit()
            conn.close()
            logger.info("✅ Veritabanı başlatıldı")
        except Exception as e:
            logger.error(f"❌ Veritabanı hatası: {e}")
    
    def kaydet(self, anahtar: str, veri_dict: Dict[str, Any]) -> bool:
        if not anahtar or not veri_dict:
            return False
        try:
            conn = sqlite3.connect(self.db_file)
            c = conn.cursor()
            veri_json = json.dumps(veri_dict, ensure_ascii=False)
            tarih_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            c.execute("""
                INSERT OR REPLACE INTO kitaplar 
                (anahtar, veri, tarih, guncelleme_tarihi) 
                VALUES (?, ?, ?, ?)
            """, (anahtar, veri_json, tarih_str, tarih_str))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"❌ Kayıt hatası: {e}")
            return False
    
    def getir(self, anahtar: str, cache_ttl_hours: int = None) -> Optional[Dict[str, Any]]:
        if not anahtar:
            return None
        ttl = cache_ttl_hours or settings.CACHE_TTL
        try:
            conn = sqlite3.connect(self.db_file)
            c = conn.cursor()
            c.execute("SELECT veri, guncelleme_tarihi FROM kitaplar WHERE anahtar = ?", (anahtar,))
            sonuc = c.fetchone()
            conn.close()
            if sonuc:
                veri_json, guncelleme_str = sonuc
                if guncelleme_str:
                    try:
                        guncelleme = datetime.strptime(guncelleme_str, '%Y-%m-%d %H:%M:%S')
                        if datetime.now() - guncelleme > timedelta(hours=ttl):
                            return None
                    except:
                        pass
                return json.loads(veri_json)
            return None
        except:
            return None
    
    def istatistikler(self) -> str:
        if not os.path.exists(self.db_file):
            return "Veritabanı dosyası henüz oluşmamış."
        try:
            conn = sqlite3.connect(self.db_file)
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM kitaplar")
            toplam_kitap = c.fetchone()[0]
            c.execute("SELECT MAX(tarih) FROM kitaplar")
            son_tarih = c.fetchone()[0]
            conn.close()
            boyut_mb = os.path.getsize(self.db_file) / (1024 * 1024)
            return f"📊 **Veritabanı**\n📚 Kitap: {toplam_kitap}\n💾 Boyut: {boyut_mb:.2f} MB\n🕒 Son: {son_tarih or 'Yok'}"
        except Exception as e:
            return f"Hata: {e}"
    
    def son_kayitlar(self, limit: int = 5) -> str:
        try:
            conn = sqlite3.connect(self.db_file)
            c = conn.cursor()
            c.execute("SELECT anahtar, tarih FROM kitaplar ORDER BY tarih DESC LIMIT ?", (limit,))
            veriler = c.fetchall()
            conn.close()
            if not veriler:
                return "Kayıt bulunamadı."
            msg = "🆕 **Son Kayıtlar:**\n"
            for anahtar, tarih in veriler:
                msg += f"• `{anahtar}` ({tarih})\n"
            return msg
        except Exception as e:
            return f"Hata: {e}"


db = DatabaseManager()
