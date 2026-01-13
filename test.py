#!/usr/bin/env python3
"""Seri ayrıştırma testi"""
import logging
from scrapers.binkitap import BinKitapScraper

logging.basicConfig(level=logging.INFO)

scraper = BinKitapScraper()

test_books = [
    "Harry Potter Felsefe Taşı",
    "Dune Frank Herbert",
    "Foundation Isaac Asimov",
]

for book in test_books:
    print("\n" + "=" * 60)
    print(f"TEST: {book}")
    print("=" * 60)
    
    result = scraper.search(book)
    
    if result:
        print(f"✅ Başlık: {result.get('baslik')}")
        print(f"✍️ Yazar: {result.get('yazar')}")
        
        if result.get('orijinal_ad'):
            print(f"🌍 Orijinal Ad: {result.get('orijinal_ad')} ✅")
        
        if result.get('seri'):
            print(f"📚 Seri: {result.get('seri')} ✅")
        else:
            print("⚠️ Seri yok")
        
        if result.get('cevirmen'):
            print(f"🔤 Çevirmen: {result.get('cevirmen')}")
    else:
        print("❌ Bulunamadı")