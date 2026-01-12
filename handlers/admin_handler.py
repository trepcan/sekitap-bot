"""
Admin komutları
"""
import os
import logging
from datetime import datetime

from config.settings import settings
from database.db_manager import db

logger = logging.getLogger(__name__)


class AdminHandler:
    """Admin komut işleyici"""
    
    @staticmethod
    async def admin_help(event, client):
        """Admin yardım menüsü"""
        # Admin kontrolü
        if settings.ADMIN_ID and event.sender_id != settings.ADMIN_ID:
            return
        
        msg = "🛠 **Admin Komutları**\n\n"
        msg += "**Genel:**\n"
        msg += "• `/durum` - Bot istatistikleri ve performans bilgileri\n"
        msg += "• `/ping` - Bağlantı testi ve gecikme ölçümü\n\n"
        msg += "**Veritabanı:**\n"
        msg += "• `/dbbilgi` - Veritabanı istatistikleri\n"
        msg += "• `/sonkayitlar` - Son eklenen 5 kitap\n\n"
        msg += "**Bakım:**\n"
        msg += "• `/logtemizle` - Log dosyasını temizle\n\n"
        msg += f"📌 **Versiyon:** {settings.SURUM}"
        
        await event.reply(msg)
    
    @staticmethod
    async def durum(event, client):
        """Bot durum bilgileri"""
        if settings.ADMIN_ID and event.sender_id != settings.ADMIN_ID:
            return
        
        from handlers.message_handler import MessageHandler
        stats = MessageHandler.stats
        
        # Süre hesaplama
        uptime = datetime.now() - stats["son_islem_zamani"]
        sure_str = f"{uptime.seconds // 60} dakika önce"
        
        # Başarı oranı
        toplam = stats["toplam_taranan"]
        basari_orani = 0
        if toplam > 0:
            basari_orani = (stats["bulunan"] / toplam) * 100
        
        msg = f"🤖 **Bot Durum Raporu**\n\n"
        msg += f"📊 **İstatistikler:**\n"
        msg += f"• Toplam Taranan: {stats['toplam_taranan']}\n"
        msg += f"• Bulunan: {stats['bulunan']} ✅\n"
        msg += f"• Bulunamayan: {stats['bulunamayan']} ❌\n"
        msg += f"• Başarı Oranı: {basari_orani:.1f}%\n\n"
        msg += f"🔄 **Durum:**\n"
        msg += f"• Mod: {stats['islem_tipi']}\n"
        msg += f"• Son İşlem: {sure_str}\n"
        msg += f"• Şu An: {stats['su_an_islenen'][:50]}...\n\n"
        msg += f"⚙️ **Konfigürasyon:**\n"
        msg += f"• Kanal Sayısı: {len(settings.HEDEF_KANALLAR)}\n"
        msg += f"• Cache TTL: {settings.CACHE_TTL} saat\n"
        msg += f"• Versiyon: {settings.SURUM}"
        
        await event.reply(msg)
    
    @staticmethod
    async def ping(event, client):
        """Ping testi"""
        start = datetime.now()
        msg = await event.reply("🏓 Pong!")
        
        # Gecikmeyi hesapla
        delta = (datetime.now() - start).total_seconds() * 1000
        
        await msg.edit(f"🏓 Pong!\n⏱ Gecikme: {delta:.1f}ms")
    
    @staticmethod
    async def dbbilgi(event, client):
        """Veritabanı bilgileri"""
        if settings.ADMIN_ID and event.sender_id != settings.ADMIN_ID:
            return
        
        bilgi = db.istatistikler()
        await event.reply(bilgi)
    
    @staticmethod
    async def sonkayitlar(event, client):
        """Son kayıtlar"""
        if settings.ADMIN_ID and event.sender_id != settings.ADMIN_ID:
            return
        
        kayitlar = db.son_kayitlar(limit=5)
        await event.reply(kayitlar)
    
    @staticmethod
    async def logtemizle(event, client):
        """Log dosyasını temizle"""
        if settings.ADMIN_ID and event.sender_id != settings.ADMIN_ID:
            return
        
        try:
            log_files = ['bot.log', 'log.txt']
            temizlenen = []
            
            for log_file in log_files:
                if os.path.exists(log_file):
                    os.remove(log_file)
                    temizlenen.append(log_file)
            
            if temizlenen:
                await event.reply(f"✅ Log dosyaları temizlendi:\n• " + "\n• ".join(temizlenen))
            else:
                await event.reply("ℹ️ Temizlenecek log dosyası bulunamadı")
        
        except Exception as e:
            await event.reply(f"❌ Hata: {e}")