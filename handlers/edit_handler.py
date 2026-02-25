"""
Telegram Mesaj Düzenleme Handler'ı
Elle yapılan düzeltmeleri algılar
"""

import logging
from telethon import events
from handlers.message_handler import MessageHandler

logger = logging.getLogger(__name__)


async def register_edit_handlers(client):
    """
    Edit handler'ları kaydet
    
    Args:
        client: Telethon client objesi
    """
    @client.on(events.MessageEdited())
    async def on_message_edited(event):
        """
        Mesaj düzenlendiğinde tetiklenir
        Elle yapılan düzeltmeleri korur
        """
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
            logger.info(f"   Kanal ID: {message.chat_id}")
            
            # 🔴 KRITIK: Mesajı HEMEN protect et
            MessageHandler._protect_message(msg_id)
            
            # Cache'i de temizle
            MessageHandler._clear_cache_for_message(msg_id)
            
            logger.info(f"🛡️ Mesaj korundu ve cache temizlendi: {msg_id}")
            
            # Bot imzası varsa (bot tarafından yazıldığını kontrol et)
            bot_imzasi = ("✍️" in text or "📖" in text or "📂 <b>Tür:</b>" in text)
            
            if bot_imzasi:
                logger.info(f"✅ Elle düzeltilen bot mesajı: {msg_id}")
            else:
                logger.info(f"ℹ️ Normal mesaj düzeltme: {msg_id}")
                
        except Exception as e:
            logger.error(f"❌ Edit handler hatası: {e}", exc_info=True)
    
    logger.info("✅ Edit handler kaydedildi")


class EditHandler:
    """Edit handler utility class"""
    
    @staticmethod
    def is_protected(message_id: int) -> bool:
        """
        Mesaj korunuyor mu kontrol et
        
        Args:
            message_id: Mesaj ID'si
            
        Returns:
            True eğer korunuyorsa
        """
        return MessageHandler._is_protected(message_id)
    
    @staticmethod
    def protect(message_id: int):
        """
        Mesajı koru
        
        Args:
            message_id: Mesaj ID'si
        """
        MessageHandler._protect_message(message_id)
    
    @staticmethod
    def clear_cache(message_id: int):
        """
        Mesajın cache'ini temizle
        
        Args:
            message_id: Mesaj ID'si
        """
        MessageHandler._clear_cache_for_message(message_id)