"""Temel scraper"""
import requests
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from bs4 import BeautifulSoup
from config.constants import HEADERS
from config.settings import settings

try:
    import cloudscraper
    HAS_SCRAPER = True
except ImportError:
    HAS_SCRAPER = False

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        if HAS_SCRAPER:
            self.scraper = cloudscraper.create_scraper(
                browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True}
            )
        else:
            self.scraper = None
        self.timeout = settings.REQUEST_TIMEOUT
    
    def get_response(self, url: str, use_scraper: bool = True) -> Optional[requests.Response]:
        try:
            if use_scraper and self.scraper:
                response = self.scraper.get(url, timeout=self.timeout)
            else:
                response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response
        except Exception as e:
            logger.error(f"❌ HTTP hatası: {e}")
            return None
    
    def parse_html(self, response: requests.Response) -> Optional[BeautifulSoup]:
        try:
            return BeautifulSoup(response.content, 'html.parser')
        except:
            return None
    
    @abstractmethod
    def search(self, query: str, direct_url: str = None) -> Optional[Dict[str, Any]]:
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        pass
