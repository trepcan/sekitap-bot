"""
Veritabanı Yöneticisi
Async SQLite ile kitap kayıt ve cache sistemi
"""

import aiosqlite
import asyncio
import json
import os
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List

from config.settings import settings

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Async veritabanı yöneticisi"""
    
    def __init__(self, db_file: str = None):
        self.db_file = db_file or settings.DB_FILE
        self.conn: Optional[aiosqlite.Connection] = None
        self.lock = asyncio.Lock()
        self._initialized = False
    
    async def initialize(self):
        """Veritabanını başlat ve tabloları oluştur"""
        try:
            # Klasörü oluştur
            Path(self.db_file).parent.mkdir(parents=True, exist_ok=True)
            
            # Bağlantı oluştur
            self.conn = await aiosqlite.connect(self.db_file)
            self.conn.row_factory = aiosqlite.Row
            
            # Tabloları oluştur
            await self._create_tables()
            
            self._initialized = True
            logger.info(f"✅ Veritabanı başlatıldı: {self.db_file}")
            
        except Exception as e:
            logger.error(f"❌ Veritabanı başlatma hatası: {e}", exc_info=True)
            raise
    
    async def _ensure_connected(self):
        """Bağlantı kontrolü"""
        if not self._initialized or not self.conn:
            await self.initialize()
    
    async def _create_tables(self):
        """Veritabanı tablolarını oluştur"""
        try:
            # 1. Cache tablosu (eski sistem - geriye dönük uyumluluk)
            await self.conn.execute("""
                CREATE TABLE IF NOT EXISTS kitaplar (
                    anahtar TEXT PRIMARY KEY,
                    veri TEXT NOT NULL,
                    tarih TEXT NOT NULL,
                    guncelleme_tarihi TEXT NOT NULL
                )
            """)
            
            # 2. Yeni kitap kayıtları tablosu
            await self.conn.execute("""
                CREATE TABLE IF NOT EXISTS kitap_kayitlari (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dosya_adi TEXT NOT NULL,
                    kanal_id INTEGER NOT NULL,
                    mesaj_id INTEGER NOT NULL,
                    baslik TEXT,
                    yazar TEXT,
                    kaynak TEXT,
                    basarili INTEGER DEFAULT 0,
                    link TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT,
                    UNIQUE(kanal_id, mesaj_id)
                )
            """)
            
            # İndeksler
            await self.conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_kitaplar_tarih 
                ON kitaplar(tarih DESC)
            """)
            
            await self.conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_kayit_baslik 
                ON kitap_kayitlari(baslik)
            """)
            
            await self.conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_kayit_yazar 
                ON kitap_kayitlari(yazar)
            """)
            
            await self.conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_kayit_tarih 
                ON kitap_kayitlari(created_at DESC)
            """)
            
            await self.conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_kayit_kanal 
                ON kitap_kayitlari(kanal_id, mesaj_id)
            """)
            
            await self.conn.commit()
            logger.debug("✅ Veritabanı tabloları hazır")
            
        except Exception as e:
            logger.error(f"❌ Tablo oluşturma hatası: {e}", exc_info=True)
            raise
    
    # ==================== CACHE SİSTEMİ (ESKİ) ====================
    
    async def kaydet(self, anahtar: str, veri_dict: Dict[str, Any]) -> bool:
        """
        Cache'e kaydet (eski sistem - geriye dönük uyumluluk)
        
        Args:
            anahtar: Benzersiz anahtar
            veri_dict: Kaydedilecek veri
            
        Returns:
            Başarılı ise True
        """
        if not anahtar or not veri_dict:
            return False
        
        try:
            async with self.lock:
                await self._ensure_connected()
                
                veri_json = json.dumps(veri_dict, ensure_ascii=False)
                tarih_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                await self.conn.execute("""
                    INSERT OR REPLACE INTO kitaplar 
                    (anahtar, veri, tarih, guncelleme_tarihi) 
                    VALUES (?, ?, ?, ?)
                """, (anahtar, veri_json, tarih_str, tarih_str))
                
                await self.conn.commit()
                logger.debug(f"💾 Cache kaydedildi: {anahtar}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Cache kayıt hatası: {e}", exc_info=True)
            return False
    
    async def getir(
        self, 
        anahtar: str, 
        cache_ttl_hours: int = None
    ) -> Optional[Dict[str, Any]]:
        """
        Cache'den getir
        
        Args:
            anahtar: Benzersiz anahtar
            cache_ttl_hours: Cache geçerlilik süresi (saat)
            
        Returns:
            Veri dictionary veya None
        """
        if not anahtar:
            return None
        
        ttl = cache_ttl_hours or settings.CACHE_TTL
        
        try:
            async with self.lock:
                await self._ensure_connected()
                
                cursor = await self.conn.execute(
                    "SELECT veri, guncelleme_tarihi FROM kitaplar WHERE anahtar = ?",
                    (anahtar,)
                )
                sonuc = await cursor.fetchone()
                
                if sonuc:
                    veri_json, guncelleme_str = sonuc
                    
                    # TTL kontrolü
                    if guncelleme_str:
                        try:
                            guncelleme = datetime.strptime(
                                guncelleme_str, 
                                '%Y-%m-%d %H:%M:%S'
                            )
                            if datetime.now() - guncelleme > timedelta(hours=ttl):
                                logger.debug(f"⏰ Cache süresi dolmuş: {anahtar}")
                                return None
                        except Exception as e:
                            logger.warning(f"⚠️ Tarih parse hatası: {e}")
                    
                    logger.debug(f"💾 Cache'den yüklendi: {anahtar}")
                    return json.loads(veri_json)
                
                return None
                
        except Exception as e:
            logger.error(f"❌ Cache okuma hatası: {e}", exc_info=True)
            return None
    
    # ==================== YENİ KİTAP KAYIT SİSTEMİ ====================
    
    async def kitap_ekle(
        self,
        dosya_adi: str,
        kanal_id: int,
        mesaj_id: int,
        baslik: Optional[str] = None,
        yazar: Optional[str] = None,
        kaynak: Optional[str] = None,
        basarili: bool = False,
        link: Optional[str] = None
    ) -> bool:
        """
        Kitap kaydı ekle veya güncelle
        
        Args:
            dosya_adi: Dosya adı
            kanal_id: Kanal ID
            mesaj_id: Mesaj ID
            baslik: Kitap başlığı
            yazar: Yazar adı
            kaynak: Bilgi kaynağı
            basarili: Arama başarılı mı?
            link: Kitap linki
            
        Returns:
            Başarılı ise True
        """
        try:
            async with self.lock:
                await self._ensure_connected()
                
                # Önce mevcut kaydı kontrol et
                cursor = await self.conn.execute(
                    """
                    SELECT id FROM kitap_kayitlari 
                    WHERE kanal_id = ? AND mesaj_id = ?
                    """,
                    (kanal_id, mesaj_id)
                )
                existing = await cursor.fetchone()
                
                if existing:
                    # Güncelle
                    await self.conn.execute(
                        """
                        UPDATE kitap_kayitlari 
                        SET dosya_adi = ?, baslik = ?, yazar = ?, 
                            kaynak = ?, basarili = ?, link = ?, 
                            updated_at = ?
                        WHERE kanal_id = ? AND mesaj_id = ?
                        """,
                        (
                            dosya_adi, baslik, yazar, kaynak,
                            1 if basarili else 0, link,
                            datetime.now().isoformat(),
                            kanal_id, mesaj_id
                        )
                    )
                    logger.debug(f"🔄 Güncellendi: {baslik or dosya_adi}")
                else:
                    # Yeni kayıt
                    await self.conn.execute(
                        """
                        INSERT INTO kitap_kayitlari (
                            dosya_adi, kanal_id, mesaj_id, baslik, yazar,
                            kaynak, basarili, link, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            dosya_adi, kanal_id, mesaj_id, baslik, yazar,
                            kaynak, 1 if basarili else 0, link,
                            datetime.now().isoformat()
                        )
                    )
                    logger.debug(f"✅ Eklendi: {baslik or dosya_adi}")
                
                await self.conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"❌ Kitap kayıt hatası: {e}", exc_info=True)
            return False
    
    async def toplam_kayit_sayisi(self) -> int:
        """Toplam kitap kayıt sayısı"""
        try:
            async with self.lock:
                await self._ensure_connected()
                
                cursor = await self.conn.execute(
                    "SELECT COUNT(*) FROM kitap_kayitlari"
                )
                row = await cursor.fetchone()
                return row[0] if row else 0
                
        except Exception as e:
            logger.error(f"❌ Toplam kayıt hatası: {e}")
            return 0
    
    async def basarili_kayit_sayisi(self) -> int:
        """Başarılı arama sayısı"""
        try:
            async with self.lock:
                await self._ensure_connected()
                
                cursor = await self.conn.execute(
                    "SELECT COUNT(*) FROM kitap_kayitlari WHERE basarili = 1"
                )
                row = await cursor.fetchone()
                return row[0] if row else 0
                
        except Exception as e:
            logger.error(f"❌ Başarılı kayıt hatası: {e}")
            return 0
    
    async def son_kayitlar(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Son kayıtları getir
        
        Args:
            limit: Maksimum kayıt sayısı
            
        Returns:
            Kayıt listesi
        """
        try:
            async with self.lock:
                await self._ensure_connected()
                
                cursor = await self.conn.execute(
                    """
                    SELECT dosya_adi, baslik, yazar, kaynak, 
                           basarili, created_at, link
                    FROM kitap_kayitlari
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    (limit,)
                )
                
                rows = await cursor.fetchall()
                
                return [
                    {
                        'dosya_adi': row[0],
                        'baslik': row[1],
                        'yazar': row[2],
                        'kaynak': row[3],
                        'basarili': bool(row[4]),
                        'created_at': row[5],
                        'link': row[6]
                    }
                    for row in rows
                ]
                
        except Exception as e:
            logger.error(f"❌ Son kayıtlar hatası: {e}", exc_info=True)
            return []
    
    async def kitap_ara(self, arama: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Kitap ara
        
        Args:
            arama: Arama terimi
            limit: Maksimum sonuç sayısı
            
        Returns:
            Sonuç listesi
        """
        try:
            async with self.lock:
                await self._ensure_connected()
                
                cursor = await self.conn.execute(
                    """
                    SELECT dosya_adi, baslik, yazar, kaynak, link, created_at
                    FROM kitap_kayitlari
                    WHERE baslik LIKE ? OR yazar LIKE ? OR dosya_adi LIKE ?
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    (f'%{arama}%', f'%{arama}%', f'%{arama}%', limit)
                )
                
                rows = await cursor.fetchall()
                
                return [
                    {
                        'dosya_adi': row[0],
                        'baslik': row[1],
                        'yazar': row[2],
                        'kaynak': row[3],
                        'link': row[4],
                        'created_at': row[5]
                    }
                    for row in rows
                ]
                
        except Exception as e:
            logger.error(f"❌ Kitap arama hatası: {e}", exc_info=True)
            return []
    
    # ==================== İSTATİSTİKLER ====================
    
    async def istatistikler(self) -> str:
        """
        Veritabanı istatistikleri
        
        Returns:
            Formatlanmış istatistik metni
        """
        if not os.path.exists(self.db_file):
            return "📊 Veritabanı dosyası henüz oluşmamış."
        
        try:
            async with self.lock:
                await self._ensure_connected()
                
                # Cache tablosu istatistikleri
                cursor = await self.conn.execute("SELECT COUNT(*) FROM kitaplar")
                cache_sayisi = (await cursor.fetchone())[0]
                
                cursor = await self.conn.execute(
                    "SELECT MAX(tarih) FROM kitaplar"
                )
                cache_son_tarih = (await cursor.fetchone())[0]
                
                # Kitap kayıtları istatistikleri
                cursor = await self.conn.execute(
                    "SELECT COUNT(*) FROM kitap_kayitlari"
                )
                toplam_kayit = (await cursor.fetchone())[0]
                
                cursor = await self.conn.execute(
                    "SELECT COUNT(*) FROM kitap_kayitlari WHERE basarili = 1"
                )
                basarili_kayit = (await cursor.fetchone())[0]
                
                cursor = await self.conn.execute(
                    "SELECT MAX(created_at) FROM kitap_kayitlari"
                )
                son_kayit_tarih = (await cursor.fetchone())[0]
                
                # Dosya boyutu
                boyut_mb = os.path.getsize(self.db_file) / (1024 * 1024)
                
                return f"""📊 <b>Veritabanı İstatistikleri</b>

💾 <b>Dosya:</b> {self.db_file}
📦 <b>Boyut:</b> {boyut_mb:.2f} MB

📚 <b>Kitap Kayıtları:</b>
   • Toplam: {toplam_kayit}
   • Başarılı: {basarili_kayit}
   • Başarısız: {toplam_kayit - basarili_kayit}
   • Son Kayıt: {son_kayit_tarih or 'Yok'}

🗄️ <b>Cache:</b>
   • Toplam: {cache_sayisi}
   • Son: {cache_son_tarih or 'Yok'}
"""
                
        except Exception as e:
            logger.error(f"❌ İstatistik hatası: {e}", exc_info=True)
            return f"❌ İstatistik hatası: {e}"
    
    async def temizle_eski_cache(self, gun: int = 7) -> int:
        """
        Eski cache kayıtlarını temizle
        
        Args:
            gun: Kaç günden eski kayıtlar silinsin
            
        Returns:
            Silinen kayıt sayısı
        """
        try:
            async with self.lock:
                await self._ensure_connected()
                
                sil_tarihi = (
                    datetime.now() - timedelta(days=gun)
                ).strftime('%Y-%m-%d %H:%M:%S')
                
                cursor = await self.conn.execute(
                    "DELETE FROM kitaplar WHERE guncelleme_tarihi < ?",
                    (sil_tarihi,)
                )
                
                await self.conn.commit()
                silinen = cursor.rowcount
                
                logger.info(f"🧹 {silinen} eski cache kaydı silindi")
                return silinen
                
        except Exception as e:
            logger.error(f"❌ Cache temizleme hatası: {e}", exc_info=True)
            return 0
    
    async def close(self):
        """Veritabanı bağlantısını kapat"""
        if self.conn:
            await self.conn.close()
            self.conn = None
            self._initialized = False
            logger.info("🔌 Veritabanı bağlantısı kapatıldı")


# Global instance
db = DatabaseManager()