"""
Asenkron yardımcı fonksiyonlar
"""
import asyncio
from typing import Callable, Any, Optional
from concurrent.futures import ThreadPoolExecutor
import logging

logger = logging.getLogger(__name__)

# Global executor
_executor: Optional[ThreadPoolExecutor] = None


def get_executor() -> ThreadPoolExecutor:
    """
    Global ThreadPoolExecutor'ı al veya oluştur
    """
    global _executor
    if _executor is None:
        _executor = ThreadPoolExecutor(max_workers=5)
    return _executor


async def run_sync(func: Callable, *args, **kwargs) -> Any:
    """
    Senkron (blocking) fonksiyonu async olarak çalıştır
    
    Args:
        func: Çalıştırılacak senkron fonksiyon
        *args: Fonksiyon argümanları
        **kwargs: Fonksiyon keyword argümanları
    
    Returns:
        Fonksiyonun dönüş değeri
    
    Examples:
        >>> result = await run_sync(some_blocking_function, arg1, arg2)
        >>> data = await run_sync(scraper.search, "Harry Potter")
    """
    try:
        loop = asyncio.get_event_loop()
        executor = get_executor()
        
        # Fonksiyonu executor'da çalıştır
        return await loop.run_in_executor(
            executor,
            lambda: func(*args, **kwargs)
        )
    
    except Exception as e:
        logger.error(f"❌ run_sync hatası: {e}")
        raise


async def run_sync_multiple(tasks: list) -> list:
    """
    Birden fazla senkron fonksiyonu paralel olarak çalıştır
    
    Args:
        tasks: [(func, args, kwargs), ...] formatında task listesi
    
    Returns:
        Sonuçların listesi
    
    Examples:
        >>> tasks = [
        ...     (scraper1.search, ("query1",), {}),
        ...     (scraper2.search, ("query2",), {}),
        ... ]
        >>> results = await run_sync_multiple(tasks)
    """
    coroutines = []
    
    for task in tasks:
        func = task[0]
        args = task[1] if len(task) > 1 else ()
        kwargs = task[2] if len(task) > 2 else {}
        
        coroutines.append(run_sync(func, *args, **kwargs))
    
    return await asyncio.gather(*coroutines, return_exceptions=True)


def cleanup_executor():
    """
    Global executor'ı temizle
    
    Not: Uygulama kapanırken çağırılmalı
    """
    global _executor
    if _executor:
        _executor.shutdown(wait=True)
        _executor = None