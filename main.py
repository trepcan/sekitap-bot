"""
sEkitap Bot - Ana Uygulama
Modüler Mimari v9.5 - Stats Entegrasyonlu
"""
import asyncio
import sys
from datetime import datetime
from telethon import TelegramClient, events
from telethon.errors import MessageNotModifiedError

from config.settings import settings
from handlers.message_handler import MessageHandler
from handlers.edit_handler import register_edit_handlers
from handlers.admin_handler import AdminHandler
from utils.logger import logger
from utils.statistics import bot_stats

# Telethon client
client = TelegramClient('user_oturumu', settings.API_ID, settings.API_HASH)


# ==================== MESAJ İŞLEYİCİLERİ ====================

@client.on(events.NewMessage(chats=settings.HEDEF_KANALLAR))
async def yeni_mesaj_handler(event):
    """Yeni mesaj geldiğinde"""
    try:
        bot_stats.set("islem_tipi", "Canlı Mod")
        bot_stats.increment("toplam_mesaj")
        bot_stats.set("son_islem_zamani", datetime.now().isoformat())
        
        logger.info(f"🔔 Yeni Mesaj (Kanal ID: {event.chat_id})")
        await MessageHandler.process_message(event.message)
        
        bot_stats.increment("basarili")
        
    except Exception as e:
        logger.error(f"❌ Yeni mesaj işleme hatası: {e}", exc_info=True)
        bot_stats.increment("basarisiz")


@client.on(events.MessageEdited(chats=settings.HEDEF_KANALLAR))
async def duzenlenen_mesaj_handler(event):
    """Mesaj düzenlendiğinde"""
    try:
        message = event.message
        
        # Dosya kontrolü
        if not message.file or not message.file.name:
            return
        
        dosya_adi = message.file.name.lower()
        if not (dosya_adi.endswith('.pdf') or dosya_adi.endswith('.epub')):
            return
        
        msg_id = message.id
        text = message.raw_text or ""
        
        logger.info(f"📝 Mesaj düzenlendi: {msg_id}")
        logger.info(f"   Dosya: {message.file.name}")
        logger.info(f"   Kanal ID: {event.chat_id}")
        
        # Link var mı kontrol et
        has_link = "http" in text
        
        if has_link:
            logger.info(f"🔗 Link bulundu, işleniyor: {msg_id}")
            # Link varsa HEMEN işle, protect etme!
            await MessageHandler.process_message(message, zorla_guncelle=True)
            bot_stats.increment("basarili")
            return
        
        # Link yoksa, elle düzenleme olarak protect et
        bot_imzasi = ("✍️" in text or "📖" in text or "📂 <b>Tür:</b>" in text)
        
        if bot_imzasi:
            # Bot tarafından yazılan mesaj elle düzeltilmiş
            logger.info(f"🛡️ Elle düzeltilen bot mesajı korunuyor: {msg_id}")
            MessageHandler._protect_message(msg_id)
            MessageHandler._clear_cache_for_message(msg_id)
            logger.info(f"🛡️ Mesaj korundu ve cache temizlendi: {msg_id}")
        else:
            # Normal mesaj
            logger.info(f"ℹ️ Normal mesaj düzeltme: {msg_id}")
        
        bot_stats.set("islem_tipi", "Canlı Mod (Düzenleme)")
        bot_stats.increment("toplam_duzenleme")
        bot_stats.increment("basarili")
        
    except Exception as e:
        logger.error(f"❌ Düzenleme işleme hatası: {e}", exc_info=True)
        bot_stats.increment("basarisiz")

# ==================== ADMIN KOMUTLARI ====================

@client.on(events.NewMessage(pattern='/admin'))
async def admin_help_handler(event):
    """Admin yardım komutu"""
    if not await _admin_check(event):
        return
    await AdminHandler.admin_help(event, client)


@client.on(events.NewMessage(pattern='/durum'))
async def durum_handler(event):
    """Durum komutu"""
    if not await _admin_check(event):
        return
    await AdminHandler.durum(event, client)


@client.on(events.NewMessage(pattern='/ping'))
async def ping_handler(event):
    """Ping komutu"""
    if not await _admin_check(event):
        return
    await AdminHandler.ping(event, client)


@client.on(events.NewMessage(pattern='/dbbilgi'))
async def dbbilgi_handler(event):
    """Veritabanı bilgi komutu"""
    if not await _admin_check(event):
        return
    await AdminHandler.dbbilgi(event, client)


@client.on(events.NewMessage(pattern='/sonkayitlar'))
async def sonkayitlar_handler(event):
    """Son kayıtlar komutu"""
    if not await _admin_check(event):
        return
    await AdminHandler.sonkayitlar(event, client)


@client.on(events.NewMessage(pattern='/logtemizle'))
async def logtemizle_handler(event):
    """Log temizleme komutu"""
    if not await _admin_check(event):
        return
    await AdminHandler.logtemizle(event, client)


@client.on(events.NewMessage(pattern='/stats'))
async def stats_handler(event):
    """İstatistik komutu"""
    if not await _admin_check(event):
        return
    
    try:
        report = bot_stats.get_report()
        await event.respond(report)
        logger.info("📊 Stats raporu gönderildi")
    except Exception as e:
        logger.error(f"Stats raporu hatası: {e}", exc_info=True)
        await event.respond("❌ Stats raporu oluşturulamadı!")


@client.on(events.NewMessage(pattern='/statsreset'))
async def stats_reset_handler(event):
    """İstatistikleri sıfırla"""
    if not await _admin_check(event):
        return
    
    try:
        bot_stats.reset()
        await event.respond("✅ İstatistikler sıfırlandı!")
        logger.info("📊 Stats sıfırlandı")
    except Exception as e:
        logger.error(f"Stats sıfırlama hatası: {e}", exc_info=True)
        await event.respond("❌ Sıfırlama başarısız!")


async def _admin_check(event) -> bool:
    """Admin yetkisi kontrol et"""
    if event.sender_id != settings.ADMIN_ID:
        await event.respond("⛔ Bu komutu kullanma yetkiniz yok!")
        logger.warning(f"⚠️ Yetkisiz komut denemesi: {event.sender_id}")
        return False
    return True


# ==================== GEÇMİŞ TARAMA ====================

async def gecmis_tarama(zorla_guncelle: bool = False):
    """
    Geçmiş mesajları tara
    Protect kontrol ile - elle yapılan düzeltmeleri koruyor
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"⏳ GEÇMİŞ TARAMA BAŞLATILIYOR...")
    logger.info(f"   Sürüm: {settings.SURUM}")
    logger.info(f"   Zorla Güncelleme: {'Açık' if zorla_guncelle else 'Kapalı'}")
    logger.info(f"{'='*60}\n")
    
    bot_stats.set("islem_tipi", "Geçmiş Taraması")
    tarama_baslangic = datetime.now()
    
    # Biraz bekle (bot tam açılsın)
    await asyncio.sleep(2)
    
    toplam_islem = 0
    
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
                
                # 🔴 KRITIK: Korunan mesajları atla
                if MessageHandler._is_protected(mesaj.id):
                    logger.debug(f"   🛡️ Korunan mesaj atlanıyor: {mesaj.id}")
                    continue
                
                # Zaten işlenmişse atla (zorla güncelleme yoksa)
                if not zorla_guncelle and mesaj.text:
                    if "✍️" in mesaj.text or "Kitap adı:" in mesaj.text or "📖" in mesaj.text:
                        continue
                
                # İşle
                use_filename_only = False
                if zorla_guncelle:
                    text = mesaj.text or ""
                    if "http" not in text:
                        use_filename_only = True
                
                try:
                    await MessageHandler.process_message(
                        mesaj,
                        zorla_guncelle=zorla_guncelle,
                        sadece_dosya_adi=use_filename_only
                    )
                    sayac += 1
                    toplam_islem += 1
                    bot_stats.increment("gecmis_tarama_sayac")
                    
                except Exception as e:
                    logger.error(f"   ⚠️ Mesaj işleme hatası: {e}")
                    bot_stats.increment("gecmis_tarama_hata")
                
                # Rate limit
                await asyncio.sleep(1)
            
            logger.info(f"   ✅ {kanal_adi}: {sayac} mesaj işlendi")
        
        except Exception as e:
            logger.error(f"   ⚠️ Kanal hatası ({kanal_adi}): {e}", exc_info=True)
            continue
    
    tarama_suresi = (datetime.now() - tarama_baslangic).total_seconds()
    
    logger.info(f"\n{'='*60}")
    logger.info("✅ GEÇMİŞ TARAMASI TAMAMLANDI!")
    logger.info(f"   📊 Toplam İşlem: {toplam_islem}")
    logger.info(f"   ⏱️  Süre: {tarama_suresi:.1f} saniye")
    logger.info(f"{'='*60}\n")
    
    bot_stats.set("islem_tipi", "Canlı Bekleme Modu")
    bot_stats.set("son_tarama_zamani", datetime.now().isoformat())
    bot_stats.set("son_tarama_islem_sayisi", toplam_islem)


# ==================== ANA FONKSİYON ====================

async def main():
    """Ana fonksiyon"""
    # Ayarları doğrula
    if not settings.validate():
        logger.error("❌ Konfigürasyon hatası! Lütfen .env dosyasını kontrol edin.")
        sys.exit(1)
    
    logger.info(f"\n{'='*60}")
    logger.info(f"🚀 sEkitap Bot Başlatılıyor...")
    logger.info(f"   Sürüm: {settings.SURUM}")
    logger.info(f"   Başlatma: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"{'='*60}\n")
    
    # Stats'ı başlat
    bot_stats.set("baslangic_zamani", datetime.now().isoformat())
    bot_stats.set("surum", settings.SURUM)
    
    # Client'ı başlat
    try:
        await client.start()
    except Exception as e:
        logger.error(f"❌ Client başlatma hatası: {e}", exc_info=True)
        sys.exit(1)
    
    # Bot bilgileri
    try:
        me = await client.get_me()
        logger.info(f"👤 Giriş Yapıldı: {me.first_name}")
        logger.info(f"📱 Telefon: +{me.phone}")
        if me.username:
            logger.info(f"🔗 Kullanıcı Adı: @{me.username}")
        logger.info("")
    except Exception as e:
        logger.error(f"⚠️ Kullanıcı bilgileri alınamadı: {e}")
    
    # Kanal bilgileri
    logger.info(f"📡 İzlenen Kanallar: {len(settings.HEDEF_KANALLAR)} adet")
    for kanal_id in settings.HEDEF_KANALLAR:
        kanal_adi = settings.KANAL_ISIMLERI.get(kanal_id, f"Kanal {kanal_id}")
        logger.info(f"   • {kanal_adi} ({kanal_id})")
    logger.info("")
    
    # Admin bilgileri
    if settings.ADMIN_ID:
        logger.info(f"👑 Admin ID: {settings.ADMIN_ID}")
    else:
        logger.warning("⚠️ Admin ID ayarlanmamış!")
    
    logger.info(f"\n{'='*60}")
    logger.info("🚀 BOT AKTİF!")
    logger.info(f"{'='*60}\n")
    
    # Geçmiş tarama
    if settings.GECMIS_TARAMA_AKTIF:
        logger.info("⏳ Geçmiş tarama aktif, arka planda başlatılıyor...\n")
        asyncio.create_task(gecmis_tarama(settings.ZORLA_GUNCELLEME_MODU))
    else:
        logger.info("ℹ️ Geçmiş tarama kapalı\n")
    
    logger.info("👂 Canlı mod aktif. Yeni mesajlar bekleniyor...")
    logger.info("💡 Admin komutları için /admin yazın\n")
    
    # İlk stats
    logger.info(f"📊 İstatistikler başlatıldı")
    logger.info(f"   Stats dosyası: logs/stats.json\n")
    
    # Edit handler'ı kaydet
    await register_edit_handlers(client)
    
    # Sürekli çalış
    await client.run_until_disconnected()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n\n👋 Bot durduruldu (Keyboard Interrupt)")
        logger.info(f"📊 Son Stats:\n{bot_stats.get_report()}")
        sys.exit(0)
    except Exception as e:
        logger.error(f"\n\n❌ Kritik hata: {e}", exc_info=True)
        sys.exit(1)