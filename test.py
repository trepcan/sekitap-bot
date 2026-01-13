#!/usr/bin/env python3
"""Seri çeviri debug testi"""
from utils.series_utils import translate_series_name, normalize_series_name

test_series = [
    "Dune #1",
    "Foundation #2",
    "The Lord of the Rings #1",
    "Harry Potter #3",
    "The Witcher #5",
    "A Song of Ice and Fire #1",
    "Unknown Series #1",
]

print("🌍 Seri Çeviri Testi (Debug)\n")

for series in test_series:
    # Seri adını ayır
    import re
    match = re.match(r'^(.+?)\s*#(\d+)$', series)
    
    if match:
        series_name = match.group(1).strip()
        series_number = match.group(2)
        
        # Normalize et
        normalized = normalize_series_name(series_name)
        
        print(f"📖 Orijinal: {series}")
        print(f"   ├─ İsim: {series_name}")
        print(f"   ├─ Normalize: '{normalized}'")
        
        # Çevir
        translated = translate_series_name(series)
        
        if series != translated:
            print(f"   └─ ✅ Çeviri: {translated}")
        else:
            print(f"   └─ ⚠️ Çeviri yok")
        
        print()