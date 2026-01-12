"""
sEkitap Bot - Ana Uygulama
Modüler Mimari v9.0
"""
import asyncio
import logging
import sys
from datetime import datetime
from telethon import TelegramClient, events
from telethon.errors import MessageNotModifiedError

from config.settings import settings
from handlers.message_handler import MessageHandler
from handlers.admin_handler import AdminHandler

# Logging konfigürasyonu
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Telethon client
client = TelegramClient('user_oturumu', settings.API_ID, settings.API_HASH)


@client.on(events.NewMessage(chats=settings.HEDEF_KANALLAR))
async def yeni_mesaj_handler(event):
    """Yeni mesaj geldiğinde"""
    MessageHandler.stats["islem_tipi"] = "Canlı Mod"
    logger.info(f"🔔 Yeni Mesaj (Kanal ID: {event.chat_id})")
    await MessageHandler.process_message(event.message)


@client.on(events.MessageEdited(chats=settings.HEDEF_KANALLAR))
async def duzenlenen_mesaj_handler(event):
    """Mesaj düzenlendiğinde"""
    text = event.message.text or ""
    
    # Zaten bot tarafından düzenlenmişse ve link yoksa atla
    if ("✍️" in text or "Kitap adı:" in text or "📖" in text) and "http" not in text:
        logger.debug("⏩ Bot mesajı, atlanıyor")
        return
    
    # Link varsa ve eski açıklama da varsa, sadece linki al
    if "http" in text and ("✍️" in text or "Kitap adı:" in text):
        import re
        match = re.search(r'(https?://\S+)', text)
        if match:
            saf_link = match.group(1).strip()
            event.message.message = saf_link
            event.message.entities = []
            logger.info(f"♻️ Link Enjekte Edildi: {saf_link}")
    
    MessageHandler.stats["islem_tipi"] = "Canlı Mod (Düzenleme)"
    logger.info(f"🔔 Düzenleme Algılandı (Kanal ID: {event.chat_id})")
    await MessageHandler.process_message(event.message, zorla_guncelle=True)


# ==================== ADMIN KOMUTLARI ====================

@client.on(events.NewMessage(pattern='/admin'))
async def admin_help_handler(event):
    """Admin yardım komutu"""
    await AdminHandler.admin_help(event, client)


@client.on(events.NewMessage(pattern='/durum'))
async def durum_handler(event):
    """Durum komutu"""
    await AdminHandler.durum(event, client)


@client.on(events.NewMessage(pattern='/ping'))
async def ping_handler(event):
    """Ping komutu"""
    await AdminHandler.ping(event, client)


@client.on(events.NewMessage(pattern='/dbbilgi'))
async def dbbilgi_handler(event):
    """Veritabanı bilgi komutu"""
    await AdminHandler.dbbilgi(event, client)


@client.on(events.NewMessage(pattern='/sonkayitlar'))
async def sonkayitlar_handler(event):
    """Son kayıtlar komutu"""
    await AdminHandler.sonkayitlar(event, client)


@client.on(events.NewMessage(pattern='/logtemizle'))
async def logtemizle_handler(event):
    """Log temizleme komutu"""
    await AdminHandler.logtemizle(event, client)


# ==================== GEÇMİŞ TARAMA ====================

async def gecmis_tarama(zorla_modu: bool = False):
    """Geçmiş mesajları tara"""
    logger.info(f"\n{'='*60}")
    logger.info(f"⏳ GEÇMİŞ TARAMA BAŞLATILIYOR...")
    logger.info(f"Sürüm: {settings.SURUM}")
    logger.info(f"Zorla Güncelleme: {'Açık' if zorla_modu else 'Kapalı'}")
    logger.info(f"{'='*60}\n")
    
    MessageHandler.stats["islem_tipi"] = "Geçmiş Taraması"
    
    # Biraz bekle (bot tam açılsın)
    await asyncio.sleep(2)
    
    for kanal_id in settings.HEDEF_KANALLAR:
        kanal_adi = settings.KANAL_ISIMLERI.get(kanal_id, f"Kanal {kanal_id}")
        logger.info(f"\n📡 Kanal taranıyor: {kanal_adi}")
        logger.info(f"   ID: {kanal_id}")
        
        try:
            sayac = 0
            async for mesaj in client.iter_messages(kanal_id, limit=None):
                # Sadece dosya olanlar
                if not mesaj.file:
                    continue
                
                dosya_adi = mesaj.file.name
                if not dosya_adi:
                    continue
                
                dosya_adi_lower = dosya_adi.lower()
                if not (dosya_adi_lower.endswith('.pdf') or dosya_adi_lower.endswith('.epub')):
                    continue
                
                # Zaten işlenmişse atla (zorla güncelleme yoksa)
                if not zorla_modu and mesaj.text:
                    if "✍️" in mesaj.text or "Kitap adı:" in mesaj.text or "📖" in mesaj.text:
                        continue
                
                # İşle
                use_filename_only = False
                if zorla_modu:
                    text = mesaj.text or ""
                    if "http" not in text:
                        use_filename_only = True
                
                await MessageHandler.process_message(
                    mesaj,
                    zorla_guncelle=zorla_modu,
                    sadece_dosya_adi=use_filename_only
                )
                
                sayac += 1
                
                # Rate limit
                await asyncio.sleep(1)
            
            logger.info(f"   ✅ {kanal_adi}: {sayac} mesaj işlendi")
        
        except Exception as e:
            logger.error(f"   ⚠️ Hata ({kanal_adi}): {e}")
            continue
    
    logger.info(f"\n{'='*60}")
    logger.info("✅ GEÇMİŞ TARAMASI TAMAMLANDI!")
    logger.info(f"{'='*60}\n")
    
    MessageHandler.stats["islem_tipi"] = "Canlı Bekleme Modu"


# ==================== ANA FONKSİYON ====================

async def main():
    """Ana fonksiyon"""
    # Ayarları doğrula
    if not settings.validate():
        logger.error("❌ Konfigürasyon hatası! Lütfen .env dosyasını kontrol edin.")
        sys.exit(1)
    
    logger.info(f"\n{'='*60}")
    logger.info(f"🚀 sEkitap Bot Başlatılıyor...")
    logger.info(f"Sürüm: {settings.SURUM}")
    logger.info(f"{'='*60}\n")
    
    # Client'ı başlat
    await client.start()
    
    # Bot bilgileri
    me = await client.get_me()
    logger.info(f"👤 Giriş Yapıldı: {me.first_name}")
    logger.info(f"📱 Telefon: +{me.phone}")
    logger.info(f"🔗 Kullanıcı Adı: @{me.username if me.username else 'Yok'}")
    logger.info(f"\n📡 İzlenen Kanallar: {len(settings.HEDEF_KANALLAR)} adet")
    
    for kanal_id in settings.HEDEF_KANALLAR:
        kanal_adi = settings.KANAL_ISIMLERI.get(kanal_id, f"Kanal {kanal_id}")
        logger.info(f"   • {kanal_adi} ({kanal_id})")
    
    logger.info("")
    
    # Admin bilgileri
    if settings.ADMIN_ID:
        logger.info(f"👑 Admin: {settings.ADMIN_ID}")
    else:
        logger.warning("⚠️  Admin ID ayarlanmamış!")
    
    logger.info(f"\n{'='*60}")
    logger.info("🚀 BOT AKTİF!")
    logger.info(f"{'='*60}\n")
    
    # Geçmiş tarama
    if settings.GECMIS_TARAMA_AKTIF:
        logger.info("⏳ Geçmiş tarama aktif, arka planda başlatılıyor...\n")
        asyncio.create_task(gecmis_tarama(settings.ZORLA_GUNCELLEME_MODU))
    else:
        logger.info("ℹ️  Geçmiş tarama kapalı\n")
    
    logger.info("👂 Canlı mod aktif. Yeni mesajlar bekleniyor...\n")
    
    # Sürekli çalış
    await client.run_until_disconnected()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n\n👋 Bot durduruldu (Keyboard Interrupt)")
        sys.exit(0)
    except Exception as e:
        logger.error(f"\n\n❌ Kritik hata: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)