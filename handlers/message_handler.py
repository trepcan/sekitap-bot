"""
Telegram Mesaj İşleyici
Kitap bilgilerini çeker ve mesajları günceller
"""

import asyncio
import html
import logging
import re
import time
from datetime import datetime
from typing import Optional, Tuple, Dict, Any
from telethon.errors import (
    MessageNotModifiedError, 
    FloodWaitError,
    MessageIdInvalidError,
    ChatAdminRequiredError,
    MessageAuthorRequiredError
)

from services.book_service import book_service
from database.db_manager import db
from utils.text_utils import durum_belirle, temizle_dosya_adi
from utils.statistics import bot_stats
from config.settings import settings, ACIKLAMA_MAX_LENGTH, ACIKLAMA_KISALTMA_LENGTH

logger = logging.getLogger(__name__)


class MessageHandler:
    """Telegram mesaj işleyici"""
    
    stats = {
        "toplam_taranan": 0,
        "bulunan": 0,
        "bulunamayan": 0,
        "su_an_islenen": "Bekleniyor...",
        "aktif_kanal_id": None,
        "islem_tipi": "Boşta",
        "son_islem_zamani": datetime.now()
    }
    
    _cache = {}
    _cache_max_size = 100
    
    # Elle düzenlenen mesajlar
    _protected_messages = {}  # {message_id: protection_time}
    _protection_duration = 600  # 10 dakika
    
    # ============================================================
    # URL EXTRACTION
    # ============================================================
    
    @staticmethod
    def _extract_url(text: str) -> Optional[str]:
        """Metinden URL'yi çıkar"""
        if not text:
            return None
        
        # 1. Markdown link formatı: [text](url)
        markdown_match = re.search(r'\[([^\]]*)\]\(([^)]+)\)', text)
        if markdown_match:
            url = markdown_match.group(2).strip()
            if 'kitapyurdu.com' in url:
                logger.debug(f"📎 Markdown link tespit edildi: {url[:70]}...")
                return url
        
        # 2. Kitapyurdu URL (tam format)
        url_match = re.search(
            r'https?://(?:www\.)?kitapyurdu\.com/kitap/[^/\s)]+/\d+\.html',
            text
        )
        if url_match:
            url = url_match.group(0)
            logger.debug(f"📎 Kitapyurdu URL tespit edildi: {url[:70]}...")
            return url
        
        # 3. Genel HTTPS URL
        general_match = re.search(r'https?://[^\s)]+', text)
        if general_match:
            url = general_match.group(0)
            logger.debug(f"📎 Genel URL tespit edildi: {url[:70]}...")
            return url
        
        return None
    
    # ============================================================
    # MESSAGE PROTECTION
    # ============================================================
    
    @classmethod
    def _is_protected(cls, message_id: int) -> bool:
        """
        Mesaj korunuyor mu kontrol et
        
        Args:
            message_id: Mesaj ID'si
            
        Returns:
            True eğer korunuyorsa
        """
        if message_id not in cls._protected_messages:
            return False
        
        protection_time = cls._protected_messages[message_id]
        elapsed = time.time() - protection_time
        
        # Koruma süresi geçmişse kaldır
        if elapsed > cls._protection_duration:
            del cls._protected_messages[message_id]
            logger.info(f"🔓 Koruma kaldırıldı: {message_id}")
            return False
        
        remaining = cls._protection_duration - elapsed
        logger.debug(f"🔒 Mesaj korunuyor ({remaining:.0f}s kaldı): {message_id}")
        return True
    
    @classmethod
    def _protect_message(cls, message_id: int):
        """
        Mesajı koru (elle düzenlenmiş olarak işaretle)
        
        Args:
            message_id: Mesaj ID'si
        """
        cls._protected_messages[message_id] = time.time()
        logger.info(f"🔒 Mesaj korunuyor (10 dakika): {message_id}")
        
        # Cache'ten sil
        cls._clear_cache_for_message(message_id)
    
    # ============================================================
    # CACHE MANAGEMENT
    # ============================================================
    
    @classmethod
    def _update_cache(cls, message_id: int, data: dict):
        """Cache'i güncelle"""
        if len(cls._cache) >= cls._cache_max_size:
            oldest_keys = list(cls._cache.keys())[:10]
            for key in oldest_keys:
                del cls._cache[key]
        
        cls._cache[message_id] = {
            'data': data,
            'timestamp': datetime.now()
        }
    
    @classmethod
    def _get_from_cache(cls, message_id: int) -> Optional[dict]:
        """Cache'den veri al"""
        cached = cls._cache.get(message_id)
        if cached:
            age = (datetime.now() - cached['timestamp']).total_seconds()
            if age < 3600:  # 1 saat
                return cached['data']
            else:
                del cls._cache[message_id]
        return None
    
    @classmethod
    def _clear_cache_for_message(cls, message_id: int):
        """Belirli bir mesajın cache'ini temizle"""
        if message_id in cls._cache:
            del cls._cache[message_id]
            logger.info(f"🗑️ Cache temizlendi: {message_id}")
    
    # ============================================================
    # MESSAGE VALIDATION
    # ============================================================
    
    @classmethod
    def _should_skip_message(
        cls, 
        message, 
        text: str, 
        zorla_guncelle: bool
    ) -> Tuple[bool, str]:
        """
        Mesajın atlanıp atlanmayacağını kontrol et
        
        Returns:
            (skip: bool, reason: str)
        """
        # Dosya kontrolü
        if not message.file or not message.file.name:
            return True, "Dosya yok"
        
        dosya_adi = message.file.name.lower()
        if not (dosya_adi.endswith('.pdf') or dosya_adi.endswith('.epub')):
            return True, "Desteklenmeyen format"
        
        # 🔴 EN ÖNEMLİ: Korunan mesajlar mutlaka atlanmalı
        if cls._is_protected(message.id):
            logger.info(f"🛡️ PROTECTED MESAJ ATLANDIĞI: {message.id}")
            return True, "🛡️ PROTECTED - DOKUNMA!"
        
        # Bot imzası var mı
        bot_imzasi = ("✍️" in text or "📖" in text or "📂 <b>Tür:</b>" in text)
        has_link = "http" in text
        
        # 🔴 ÖNEMLİ: Link varsa MUTLAKA işle! (protect kaldırılmasın)
        if has_link:
            logger.info(f"🔗 Link bulundu, işleniyor: {message.id}")
            return False, "Link var"
        
        # Bot işlemiş ve güncelleme istemiyorsa atla
        if bot_imzasi and not zorla_guncelle:
            logger.debug(f"⏭️ Zaten işlenmiş mesaj atlanıyor")
            return True, "Zaten işlenmiş"
        
        return False, ""
    
    @classmethod
    async def _verify_message_exists(cls, message) -> bool:
        """Mesajın var olup olmadığını kontrol et"""
        try:
            fresh_message = await message.client.get_messages(
                message.peer_id,
                ids=message.id
            )
            if fresh_message:
                logger.debug(f"✅ Mesaj doğrulandı: {message.id}")
                return True
            else:
                logger.warning(f"⚠️ Mesaj bulunamadı (ID: {message.id})")
                bot_stats.increment("mesaj_silinmis")
                return False
                
        except Exception as e:
            logger.error(f"❌ Mesaj doğrulama hatası: {e}")
            return True
    
    # ============================================================
    # STATISTICS
    # ============================================================
    
    @classmethod
    def _update_stats(cls, dosya_adi: str, kanal_id: int):
        """İstatistikleri güncelle"""
        cls.stats["toplam_taranan"] += 1
        cls.stats["su_an_islenen"] = dosya_adi
        cls.stats["aktif_kanal_id"] = kanal_id
        cls.stats["son_islem_zamani"] = datetime.now()
        bot_stats.increment("toplam_mesaj_islendi")
    
    # ============================================================
    # MAIN PROCESSING
    # ============================================================
    
    @classmethod
    async def process_message(
        cls, 
        message, 
        zorla_guncelle: bool = False,
        sadece_dosya_adi: bool = False
    ):
        """
        Mesajı işle ve kitap bilgilerini ekle
        
        Args:
            message: Telethon mesaj objesi
            zorla_guncelle: Zaten işlenmiş mesajları da güncelle
            sadece_dosya_adi: Sadece dosya adından ara
        """
        start_time = time.time()
        
        try:
            text = message.raw_text or ""
            
            # Atlanacak mı kontrol et
            should_skip, skip_reason = cls._should_skip_message(
                message, text, zorla_guncelle
            )
            if should_skip:
                logger.debug(f"⏩ Atlandı: {skip_reason}")
                # Cache'ten sil
                cls._clear_cache_for_message(message.id)
                return
            
            cls._update_stats(message.file.name, message.chat_id)
            logger.info(f"📄 İşleniyor: {message.file.name}")
            
            # Cache kontrolü
            cached_data = cls._get_from_cache(message.id) if not zorla_guncelle else None
            if cached_data:
                logger.info("💾 Cache'den yüklendi")
                bilgi = cached_data
                kaynak = bilgi.get("kaynak", "Cache")
                basarili = True
            else:
                # Kitap bilgilerini ara
                bilgi, kaynak, basarili = await cls._search_book_info(
                    message, text, sadece_dosya_adi
                )
                
                # Cache'e ekle
                if basarili and bilgi:
                    bilgi["kaynak"] = kaynak
                    cls._update_cache(message.id, bilgi)
            
            # İstatistikleri güncelle
            if basarili:
                cls.stats["bulunan"] += 1
                bot_stats.increment("basarili_kitap_bulma")
            else:
                cls.stats["bulunamayan"] += 1
                bot_stats.increment("basarisiz_kitap_bulma")
            
            # Dosya bilgileri
            dosya_turu = "PDF" if message.file.name.lower().endswith('.pdf') else "EPUB"
            durum = durum_belirle(message.file.name)
            
            # Mesajı düzenle
            await cls._edit_message_with_retry(
                message, bilgi, kaynak, dosya_turu, durum
            )
            
            # Performans metrikleri
            elapsed = time.time() - start_time
            logger.info(f"⏱️  İşlem süresi: {elapsed:.2f}s")
            bot_stats.set("ortalama_islem_suresi", elapsed)
            
            # Veritabanına kaydet
            await cls._save_to_database(message, bilgi, kaynak, basarili)
            
        except FloodWaitError as e:
            logger.warning(f"⏳ Rate limit: {e.seconds}s bekleniyor...")
            bot_stats.increment("rate_limit_sayisi")
            await asyncio.sleep(e.seconds)
            await cls.process_message(message, zorla_guncelle, sadece_dosya_adi)
            
        except Exception as e:
            logger.error(f"❌ İşleme hatası: {e}", exc_info=True)
            bot_stats.increment("islem_hatalari")
            cls.stats["su_an_islenen"] = "Hata!"
    
    # ============================================================
    # BOOK SEARCH
    # ============================================================
    
    @classmethod
    async def _search_book_info(
        cls, 
        message, 
        text: str, 
        sadece_dosya_adi: bool
    ) -> Tuple[dict, str, bool]:
        """Kitap bilgilerini ara"""
        bilgi = None
        kaynak = None
        basarili = False
        
        bot_stats.increment("toplam_api_cagrisi")
        
        try:
            # 1. Link varsa önce linkten ara
            has_link = "http" in text
            if has_link and not sadece_dosya_adi:
                direct_url = cls._extract_url(text)
                if direct_url:
                    logger.info(f"🔗 Link bulundu: {direct_url[:70]}...")
                    bilgi, kaynak, basarili = await book_service.search_book(
                        query="",
                        direct_url=direct_url,
                        manuel_mod=False
                    )
                    
                    if basarili:
                        bot_stats.increment("linkten_bulunan")
                else:
                    logger.warning("⚠️ Link bulundu ama parse edilemedi")
            
            # 2. Link yoksa veya linkten bulunamadıysa dosya adından ara
            if not basarili:
                logger.info("📝 Dosya adından aranıyor...")
                bilgi, kaynak, basarili = await book_service.search_book(
                    query=message.file.name,
                    manuel_mod=False
                )
                
                if basarili:
                    bot_stats.increment("dosya_adindan_bulunan")
            
            # 3. Hiçbir şekilde bulunamadı - fallback
            if not basarili or not bilgi:
                logger.warning(f"❌ Bulunamadı: {message.file.name}")
                bilgi = cls._create_fallback_data(message.file.name)
                kaynak = "Otomatik (Dosya Adı)"
                bot_stats.increment("fallback_kullanimi")
            else:
                bot_stats.increment("basarili_api")
            
            return bilgi, kaynak, basarili
            
        except Exception as e:
            logger.error(f"❌ Arama hatası: {e}", exc_info=True)
            bot_stats.increment("basarisiz_api")
            
            bilgi = cls._create_fallback_data(message.file.name)
            kaynak = "Otomatik (Hata)"
            return bilgi, kaynak, False
    
    @classmethod
    def _create_fallback_data(cls, dosya_adi: str) -> dict:
        """Kitap bulunamadığında dosya adından temel bilgiler çıkar"""
        temiz_ad = temizle_dosya_adi(dosya_adi)
        parcalar = temiz_ad.split('_', 1)
        
        if len(parcalar) >= 2:
            yazar = parcalar[0].strip()
            baslik = parcalar[1].strip()
        else:
            yazar = "Bilinmiyor"
            baslik = temiz_ad
        
        baslik = re.sub(r'\b\d+\b', '', baslik).strip()
        baslik = re.sub(r'\s+', ' ', baslik)
        
        return {
            "baslik": baslik or "Bilinmeyen Kitap",
            "yazar": yazar,
            "aciklama": "Bu kitap hakkında bilgi bulunamadı. Dosya adından oluşturulmuştur.",
            "kaynak": "Otomatik (Dosya Adı)"
        }
    
    # ============================================================
    # MESSAGE EDITING
    # ============================================================
    
    @classmethod
    async def _edit_message_with_retry(
        cls, 
        message, 
        bilgi: dict, 
        kaynak: str,
        dosya_turu: str,
        durum: str,
        max_retries: int = 3
    ):
        """Mesajı düzenle (retry logic ile)"""
        if not await cls._verify_message_exists(message):
            logger.warning(f"⚠️ Mesaj düzenleme iptal edildi (mesaj yok): {message.id}")
            bot_stats.increment("mesaj_duzenlenemedi")
            return
        
        for attempt in range(max_retries):
            try:
                await cls._edit_message(message, bilgi, kaynak, dosya_turu, durum)
                bot_stats.increment("basarili_mesaj_duzenleme")
                return
                
            except MessageNotModifiedError:
                logger.debug("⚠️ Mesaj zaten aynı")
                bot_stats.increment("mesaj_zaten_ayni")
                return
            
            except MessageIdInvalidError:
                logger.error(f"❌ Geçersiz mesaj ID (deneme {attempt+1}/{max_retries}): {message.id}")
                bot_stats.increment("gecersiz_mesaj_id")
                
                if attempt < max_retries - 1:
                    await asyncio.sleep(2)
                    if not await cls._verify_message_exists(message):
                        logger.warning("⚠️ Mesaj silinmiş, düzenleme sonlandırılıyor")
                        bot_stats.increment("mesaj_silinmis")
                        return
                else:
                    logger.error("❌ Mesaj ID geçersiz, düzenleme başarısız")
                    bot_stats.increment("basarisiz_mesaj_duzenleme")
            
            except ChatAdminRequiredError:
                logger.error("❌ Admin yetkisi gerekli, mesaj düzenlenemedi")
                bot_stats.increment("admin_yetkisi_yok")
                return
            
            except MessageAuthorRequiredError:
                logger.error("❌ Mesaj sahibi değil, düzenleme yapılamadı")
                bot_stats.increment("sahip_degil")
                return
                
            except FloodWaitError as e:
                if attempt < max_retries - 1:
                    logger.warning(f"⏳ Rate limit (deneme {attempt+1}/{max_retries}): {e.seconds}s")
                    await asyncio.sleep(min(e.seconds, 60))
                    continue
                else:
                    logger.error(f"❌ Rate limit aşıldı")
                    bot_stats.increment("basarisiz_mesaj_duzenleme")
                    raise
                    
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.warning(f"⚠️ Düzenleme hatası (deneme {attempt+1}/{max_retries}): {e}")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    logger.error(f"❌ Mesaj düzenleme başarısız: {e}", exc_info=True)
                    bot_stats.increment("basarisiz_mesaj_duzenleme")
    
    @classmethod
    async def _edit_message(
        cls, 
        message, 
        bilgi: dict, 
        kaynak: str,
        dosya_turu: str,
        durum: str
    ):
        """Mesajı formatla ve düzenle"""
        try:
            baslik = html.escape(bilgi.get("baslik") or "Bilinmiyor")
            yazar = html.escape(bilgi.get("yazar") or "Bilinmiyor")
            
            aciklama_raw = bilgi.get("aciklama") or "Açıklama bulunamadı."
            if len(aciklama_raw) > ACIKLAMA_MAX_LENGTH:
                aciklama_raw = aciklama_raw[:ACIKLAMA_KISALTMA_LENGTH] + "..."
            ozet = html.escape(aciklama_raw)
            
            metin = cls._format_message_text(
                bilgi, baslik, yazar, ozet, dosya_turu, durum, kaynak
            )
            
            await message.edit(
                text=metin, 
                parse_mode='html', 
                link_preview=False
            )
            
            logger.info(f"✅ Güncellendi: {baslik} ({kaynak})")
            
        except ValueError as e:
            logger.error(f"❌ Format hatası: {e}")
            raise
    
    # ============================================================
    # MESSAGE FORMATTING
    # ============================================================
    
    @classmethod
    def _format_message_text(
        cls,
        bilgi: dict,
        baslik: str,
        yazar: str,
        ozet: str,
        dosya_turu: str,
        durum: str,
        kaynak: str
    ) -> str:
        """Mesaj metnini formatla"""
        metin = f"✍️ <b>Yazar:</b> {yazar}\n"
        metin += f"📖 <b>Kitap:</b> {baslik}\n"
        
        if bilgi.get("orijinal_ad"):
            orijinal = html.escape(bilgi["orijinal_ad"])
            metin += f"📝 <b>Orijinal Ad:</b> {orijinal}\n"        
        
        if bilgi.get("seri"):
            seri = html.escape(bilgi["seri"])
            metin += f"📚 <b>Seri:</b> {seri}\n"
        
        metin += f"📂 <b>Tür:</b> {dosya_turu}\n"
        metin += f"📊 <b>Durum:</b> {durum}\n"
        
        if bilgi.get("yayinevi"):
            yayinevi = html.escape(bilgi["yayinevi"])
            metin += f"🏢 <b>Yayınevi:</b> {yayinevi}\n"
        
        if bilgi.get("tarih"):
            tarih = html.escape(str(bilgi["tarih"]))
            metin += f"📅 <b>Yayın Tarihi:</b> {tarih}\n"
        
        if bilgi.get("sayfa"):
            metin += f"📄 <b>Sayfa:</b> {bilgi['sayfa']}\n"
        
        if bilgi.get("isbn"):
            metin += f"🔢 <b>ISBN:</b> {html.escape(bilgi['isbn'])}\n"
        
        if bilgi.get("cevirmen"):
            cevirmen = html.escape(bilgi["cevirmen"])
            metin += f"🌍 <b>Çevirmen:</b> {cevirmen}\n"
        
        if bilgi.get("puan"):
            puan = bilgi["puan"]
            oy = bilgi.get("oy_sayisi", "")
            if oy:
                metin += f"⭐ <b>Puan:</b> {puan}/5 ({oy} oy)\n"
            else:
                metin += f"⭐ <b>Puan:</b> {puan}/5\n"
        
        if bilgi.get("turu"):
            metin += f"\n🏷 {bilgi['turu']}\n"
        
        metin += f"\nℹ️ <b>Açıklama:</b>\n<blockquote>{ozet}</blockquote>\n"
        
        if bilgi.get("link"):
            link = html.escape(bilgi["link"])
            metin += f"\n🌐 <a href=\"{link}\">{kaynak}</a>"
        else:
            metin += f"\n🔍 <i>Kaynak: {kaynak}</i>"
        
        return metin
    
    # ============================================================
    # DATABASE
    # ============================================================
    
    @classmethod
    async def _save_to_database(
        cls,
        message,
        bilgi: dict,
        kaynak: str,
        basarili: bool
    ):
        """Kitap bilgilerini veritabanına kaydet"""
        try:
            await db.kitap_ekle(
                dosya_adi=message.file.name,
                kanal_id=message.chat_id,
                mesaj_id=message.id,
                baslik=bilgi.get("baslik"),
                yazar=bilgi.get("yazar"),
                kaynak=kaynak,
                basarili=basarili,
                link=bilgi.get("link")
            )
            bot_stats.increment("veritabani_kayit")
            
        except Exception as e:
            logger.error(f"❌ Veritabanı kayıt hatası: {e}", exc_info=True)
            bot_stats.increment("veritabani_hata")
    
    # ============================================================
    # PUBLIC API
    # ============================================================
    
    @classmethod
    def get_stats(cls) -> dict:
        """İstatistikleri al"""
        return cls.stats.copy()
    
    @classmethod
    def reset_stats(cls):
        """İstatistikleri sıfırla"""
        cls.stats = {
            "toplam_taranan": 0,
            "bulunan": 0,
            "bulunamayan": 0,
            "su_an_islenen": "Bekleniyor...",
            "aktif_kanal_id": None,
            "islem_tipi": "Boşta",
            "son_islem_zamani": datetime.now()
        }
        logger.info("📊 MessageHandler stats sıfırlandı")