# utils/decorators.py
import functools
import time
import traceback
from telegram import Update
from telegram.ext import ContextTypes
from utils.logger import logger, bot_logger

def log_function_call(func):
    """Fonksiyon çağrılarını logla"""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        logger.debug(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
        start_time = time.time()
        
        try:
            result = await func(*args, **kwargs)
            elapsed = time.time() - start_time
            logger.debug(f"{func.__name__} completed in {elapsed:.3f}s")
            return result
        except Exception as e:
            logger.error(f"{func.__name__} failed: {e}", exc_info=True)
            raise
    
    return wrapper


def log_handler(func):
    """Telegram handler'ları için özel decorator"""
    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Kullanıcı bilgilerini al
        user = update.effective_user
        chat_id = update.effective_chat.id if update.effective_chat else None
        message_text = update.message.text if update.message else None
        
        # Log mesajı hazırla
        log_msg = (
            f"Handler: {func.__name__} | "
            f"User: {user.username or user.id} ({user.id}) | "
            f"Chat: {chat_id}"
        )
        
        if message_text:
            log_msg += f" | Message: {message_text[:100]}"
        
        logger.info(log_msg)
        
        # Kullanıcı aktivitesini logla
        bot_logger.log_user_activity(
            user_id=user.id,
            username=user.username or f"user_{user.id}",
            action=func.__name__,
            details={
                'chat_id': chat_id,
                'message': message_text[:200] if message_text else None
            }
        )
        
        start_time = time.time()
        
        try:
            result = await func(update, context)
            elapsed = time.time() - start_time
            logger.info(f"{func.__name__} completed in {elapsed:.3f}s")
            return result
            
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(
                f"Error in {func.__name__} after {elapsed:.3f}s: {e}\n"
                f"User: {user.id} ({user.username})\n"
                f"Traceback: {traceback.format_exc()}"
            )
            
            # Kullanıcıya hata mesajı gönder
            try:
                await update.message.reply_text(
                    "❌ Üzgünüm, bir hata oluştu. "
                    "Lütfen daha sonra tekrar deneyin."
                )
            except:
                pass
            
            raise
    
    return wrapper


def log_errors(func):
    """Hataları yakala ve logla"""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(
                f"Unhandled error in {func.__name__}: {e}\n"
                f"Traceback:\n{traceback.format_exc()}"
            )
            raise
    
    return wrapper