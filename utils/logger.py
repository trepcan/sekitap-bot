# utils/logger.py
import logging
import sys
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path
from datetime import datetime

class ColoredFormatter(logging.Formatter):
    """Console için renkli log formatter"""
    
    # ANSI renk kodları
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record):
        # Rengi ekle
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        record.levelname = f"{color}{record.levelname}{self.COLORS['RESET']}"
        return super().format(record)


class BotLogger:
    """Telegram Bot için özel logger sınıfı"""
    
    def __init__(self, name: str = 'sekitap_bot', log_dir: str = 'logs'):
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Ana logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Handler'ları temizle (duplicate önlemek için)
        if self.logger.handlers:
            self.logger.handlers.clear()
        
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Tüm handler'ları kur"""
        
        # 1. Console Handler (Renkli)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = ColoredFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # 2. Genel Log Dosyası (Rotating)
        general_handler = RotatingFileHandler(
            self.log_dir / 'bot.log',
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding='utf-8'
        )
        general_handler.setLevel(logging.DEBUG)
        general_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - '
            '%(filename)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        general_handler.setFormatter(general_formatter)
        self.logger.addHandler(general_handler)
        
        # 3. Error Log Dosyası (Sadece ERROR ve üstü)
        error_handler = RotatingFileHandler(
            self.log_dir / 'error.log',
            maxBytes=5 * 1024 * 1024,  # 5 MB
            backupCount=3,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(general_formatter)
        self.logger.addHandler(error_handler)
        
        # 4. Günlük Log Dosyaları (Her gün yeni dosya)
        daily_handler = TimedRotatingFileHandler(
            self.log_dir / 'daily.log',
            when='midnight',
            interval=1,
            backupCount=30,  # 30 gün sakla
            encoding='utf-8'
        )
        daily_handler.setLevel(logging.INFO)
        daily_handler.setFormatter(general_formatter)
        # Dosya adına tarih ekle
        daily_handler.suffix = '%Y-%m-%d'
        self.logger.addHandler(daily_handler)
        
        # 5. User Activity Log (Özel)
        self.activity_logger = logging.getLogger(f'{self.name}.activity')
        self.activity_logger.setLevel(logging.INFO)
        activity_handler = RotatingFileHandler(
            self.log_dir / 'user_activity.log',
            maxBytes=20 * 1024 * 1024,  # 20 MB
            backupCount=10,
            encoding='utf-8'
        )
        activity_formatter = logging.Formatter(
            '%(asctime)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        activity_handler.setFormatter(activity_formatter)
        self.activity_logger.addHandler(activity_handler)
    
    def get_logger(self):
        """Ana logger'ı döndür"""
        return self.logger
    
    def log_user_activity(self, user_id: int, username: str, 
                         action: str, details: dict = None):
        """Kullanıcı aktivitelerini logla"""
        log_data = {
            'user_id': user_id,
            'username': username,
            'action': action,
            'timestamp': datetime.now().isoformat()
        }
        if details:
            log_data.update(details)
        
        self.activity_logger.info(str(log_data))


# Global logger instance
bot_logger = BotLogger()
logger = bot_logger.get_logger()
logger = bot_logger.get_logger()