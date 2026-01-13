#!/usr/bin/env python3
"""
BookService test scripti
"""
import asyncio
import logging
from services.book_service import book_service

# Logging ayarları
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


async def test_search():
    """Arama testi"""
    print("\n" + "=" * 70)
    print("🧪 KİTAP ARAMA SERVİSİ TEST")
    print("=" * 70)
    
    test_cases = [
        "Stephen King Karanlığı Seversin",
    ]
    
    for test_query in test_cases:
        print("\n" + "-" * 70)
        print(f"📚 Test: {test_query}")
        print("-" * 70)
        
        result, source, _ = await book_service.search_book(test_query)
        
        if result:
            print(f"\n✅ Kaynak: {source}")
            print(f"📖 Başlık: {result.get('baslik')}")
            print(f"✍️ Yazar: {result.get('yazar')}")
            
            if result.get('orijinal_ad'):
                print(f"🌍 Orijinal Ad: {result.get('orijinal_ad')}")
            else:
                print("⚠️ Orijinal ad yok")
            
            if result.get('cevirmen'):
                print(f"🔤 Çevirmen: {result.get('cevirmen')}")
            
            if result.get('puan'):
                print(f"⭐ Puan: {result.get('puan')} ({result.get('oy_sayisi')} oy)")
            
            if result.get('turu'):
                print(f"🏷️ Tür: {result.get('turu')}")
            
            if result.get('seri'):
                print(f"📚 Seri: {result.get('seri')}")
            
            if result.get('guncellendi'):
                print("\n✨ Veri zenginleştirildi!")
        else:
            print("❌ Sonuç bulunamadı")
        
        # Rate limiting
        await asyncio.sleep(2)


async def test_url():
    """URL ile arama testi"""
    print("\n" + "=" * 70)
    print("🧪 URL İLE ARAMA TEST")
    print("=" * 70)
    
    test_urls = [
        "https://www.kitapyurdu.com/kitap/1984/1234",
        "https://1000kitap.com/kitap/suc-ve-ceza--123",
    ]
    
    for url in test_urls:
        print(f"\n🔗 Test URL: {url}")
        
        result, source, _ = await book_service.search_book(url)
        
        if result:
            print(f"✅ Kaynak: {source}")
            print(f"📖 Başlık: {result.get('baslik')}")
        else:
            print("❌ Sonuç bulunamadı")
        
        await asyncio.sleep(2)


if __name__ == '__main__':
    asyncio.run(test_search())
    # asyncio.run(test_url())