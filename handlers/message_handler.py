import asyncio
import html
import logging
from datetime import datetime
from typing import Optional
from telethon.errors import MessageNotModifiedError

from services.book_service import book_service
from database.db_manager import db
from utils.text_utils import durum_belirle
from config.settings import settings

logger = logging.getLogger(__name__)


class MessageHandler:
    """Telegram mesaj işleyici"""
    
    # İstatistikler
    stats = {
        "toplam_taranan": 0,
        "bulunan": 0,
        "bulunamayan": 0,
        "su_an_islenen": "Bekleniyor...",
        "aktif_kanal_id": None,
        "islem_tipi": "Boşta",
        "son_islem_zamani": datetime.now()
    }
    
    @classmethod
    async def process_message(
        cls, 
        message, 
        zorla_guncelle: bool = False,
        sadece_dosya_adi: bool = False
    ):
        """Mesajı işle"""
        # Dosya kontrolü
        if not message.file or not message.file.name:
            return
        
        dosya_adi = message.file.name.lower()
        if not (dosya_adi.endswith('.pdf') or dosya_adi.endswith('.epub')):
            return
        
        # İstatistikleri güncelle
        cls.stats["toplam_taranan"] += 1
        cls.stats["su_an_islenen"] = message.file.name
        cls.stats["aktif_kanal_id"] = message.chat_id
        cls.stats["son_islem_zamani"] = datetime.now()
        
        logger.info(f"📄 İşleniyor: {message.file.name}")
        
        # Mesaj metnini al
        text = message.text or ""
        
        # Bot imzası kontrolü
        bot_imzasi = ("Kitap adı:" in text or "✍️" in text or "📖" in text)
        has_link = "http" in text
        
        # Zaten işlenmiş ve zorla güncelleme yoksa atla
        if bot_imzasi and not zorla_guncelle and not has_link:
            logger.debug("⏩ Zaten işlenmiş, atlanıyor")
            return
        
        # Dosya bilgileri
        dosya_turu = "PDF" if dosya_adi.endswith('.pdf') else "EPUB"
        durum = durum_belirle(message.file.name)
        
        # Kitap bilgilerini ara
        bilgi = None
        kaynak = None
        basarili = False
        
        # 1. Link varsa önce linkten ara
        if has_link and not sadece_dosya_adi:
            logger.info("🔗 Link bulundu, URL'den aranıyor...")
            bilgi, kaynak, basarili = await book_service.search_book(
                text, 
                manuel_mod=True  # Link aramasında zenginleştirme yapma
            )
        
        # 2. Link yoksa veya linkten bulunamadıysa dosya adından ara
        if not basarili:
            logger.info("📝 Dosya adından aranıyor...")
            bilgi, kaynak, basarili = await book_service.search_book(
                message.file.name,
                #manuel_mod=sadece_dosya_adi  # Sadece dosya adı modunda zenginleştirme yapma
            )
        
        # 3. Hiçbir şekilde bulunamadı - fallback veri oluştur
        if not basarili or not bilgi:
            cls.stats["bulunamayan"] += 1
            logger.warning(f"❌ Bulunamadı: {message.file.name}")
            
            # Fallback veri oluştur
            bilgi = cls._create_fallback_data(message.file.name)
            kaynak = "Otomatik (Dosya Adı)"
        else:
            cls.stats["bulunan"] += 1
        
        # Mesajı düzenle
        await cls._edit_message(message, bilgi, kaynak, dosya_turu, durum)
    
    @classmethod
    def _create_fallback_data(cls, dosya_adi: str) -> dict:
        """
        Kitap bulunamadığında dosya adından temel bilgiler çıkar
        
        Args:
            dosya_adi: Dosya adı
        
        Returns:
            Temel kitap bilgileri
        """
        import re
        from utils.text_utils import temizle_dosya_adi
        
        # Dosya adını temizle
        temiz_ad = temizle_dosya_adi(dosya_adi)
        
        # Yazar ve kitap adını ayırmaya çalış
        # Format: "Yazar_Adi_Kitap_Adi.epub"
        parcalar = temiz_ad.split('_', 1)
        
        if len(parcalar) >= 2:
            yazar = parcalar[0].strip()
            baslik = parcalar[1].strip()
        else:
            yazar = "Bilinmiyor"
            baslik = temiz_ad
        
        # Sayı bilgilerini temizle (seri numaraları vs.)
        baslik = re.sub(r'\b\d+\b', '', baslik).strip()
        baslik = re.sub(r'\s+', ' ', baslik)
        
        return {
            "baslik": baslik or "Bilinmeyen Kitap",
            "yazar": yazar,
            "aciklama": "Bu kitap hakkında bilgi bulunamadı. Dosya adından otomatik olarak oluşturulmuştur.",
            "kaynak": "Otomatik (Dosya Adı)"
        }
    
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
        # HTML escape
        baslik = html.escape(bilgi.get("baslik") or "Bilinmiyor")
        yazar = html.escape(bilgi.get("yazar") or "Bilinmiyor")
        
        # Açıklama (maksimum 3000 karakter)
        aciklama_raw = bilgi.get("aciklama") or "Açıklama bulunamadı."
        if len(aciklama_raw) > 3000:
            aciklama_raw = aciklama_raw[:2997] + "..."
        ozet = html.escape(aciklama_raw)
        
        # Mesaj formatı
        metin = f"✍️ <b>Yazar:</b> {yazar}\n"
        metin += f"📖 <b>Kitap:</b> {baslik}\n"
        
        # Orijinal ad (Goodreads/1000Kitap'tan gelebilir)
        if bilgi.get("orijinal_ad"):
            orijinal = html.escape(bilgi["orijinal_ad"])
            metin += f"📝 <b>Orijinal Ad:</b> {orijinal}\n"        
        
        # Seri bilgisi (✅ Türkçeleştirilmiş)
        if bilgi.get("seri"):
            seri = html.escape(bilgi["seri"])
            metin += f"📚 <b>Seri:</b> {seri}\n"
        
        # Dosya bilgileri
        metin += f"📂 <b>Tür:</b> {dosya_turu}\n"
        metin += f"📊 <b>Durum:</b> {durum}\n"
        
        # Yayın bilgileri
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
        
        # Çevirmen (1000Kitap'tan gelebilir)
        if bilgi.get("cevirmen"):
            cevirmen = html.escape(bilgi["cevirmen"])
            metin += f"🌍 <b>Çevirmen:</b> {cevirmen}\n"
       
        
        # Puan (Goodreads'ten gelebilir)
        if bilgi.get("puan"):
            puan = bilgi["puan"]
            oy = bilgi.get("oy_sayisi", "")
            if oy:
                metin += f"⭐ <b>Puan:</b> {puan}/5 ({oy} oy)\n"
            else:
                metin += f"⭐ <b>Puan:</b> {puan}/5\n"
        
        # Türler (Goodreads'ten gelebilir)
        if bilgi.get("turu"):
            metin += f"\n🏷 {bilgi['turu']}\n"
        
        # Açıklama
        metin += f"\nℹ️ <b>Açıklama:</b>\n<blockquote>{ozet}</blockquote>\n"
        
        # Link ve kaynak
        if bilgi.get("link"):
            link = html.escape(bilgi["link"])
            metin += f"\n🌐 <a href=\"{link}\">{kaynak}</a>"
        else:
            metin += f"\n🔍 <i>Kaynak: {kaynak}</i>"
        
        # Mesajı düzenle
        try:
            await message.edit(
                text=metin, 
                parse_mode='html', 
                link_preview=False
            )
            logger.info(f"✅ Güncellendi: {baslik} ({kaynak})")
        
        except MessageNotModifiedError:
            logger.debug("⚠️ Mesaj zaten aynı, değişiklik yapılmadı")
        
        except Exception as e:
            logger.error(f"❌ Mesaj düzenleme hatası: {e}")
            # Fallback: Basit format
            try:
                basit_metin = f"✍️ {yazar} - {baslik}\n\n{ozet}"
                await message.edit(text=basit_metin, link_preview=False)
            except:
                logger.error("❌ Basit format da başarısız")