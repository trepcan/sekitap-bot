#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Veritabanı migration scripti
guncelleme_tarihi kolonunu ekler
"""
import sqlite3
import os
from datetime import datetime

DB_FILE = "kitap_onbellek.db"

def migrate():
    """Veritabanını güncelle"""
    
    if not os.path.exists(DB_FILE):
        print(f"❌ {DB_FILE} bulunamadı!")
        return
    
    print(f"🔧 Veritabanı güncelleniyor: {DB_FILE}")
    
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Mevcut tablo yapısını kontrol et
        cursor.execute("PRAGMA table_info(kitaplar)")
        columns = [col[1] for col in cursor.fetchall()]
        
        print(f"📊 Mevcut kolonlar: {columns}")
        
        # guncelleme_tarihi kolonu var mı?
        if 'guncelleme_tarihi' in columns:
            print("✅ guncelleme_tarihi kolonu zaten var!")
            conn.close()
            return
        
        print("➕ guncelleme_tarihi kolonu ekleniyor...")
        
        # Yeni kolon ekle
        cursor.execute("""
            ALTER TABLE kitaplar 
            ADD COLUMN guncelleme_tarihi TEXT
        """)
        
        # Mevcut kayıtlar için guncelleme_tarihi = tarih yap
        cursor.execute("""
            UPDATE kitaplar 
            SET guncelleme_tarihi = tarih 
            WHERE guncelleme_tarihi IS NULL
        """)
        
        conn.commit()
        
        # Kontrol et
        cursor.execute("PRAGMA table_info(kitaplar)")
        new_columns = [col[1] for col in cursor.fetchall()]
        
        print(f"✅ Yeni kolonlar: {new_columns}")
        
        # İstatistik
        cursor.execute("SELECT COUNT(*) FROM kitaplar")
        count = cursor.fetchone()[0]
        print(f"📚 Toplam kayıt: {count}")
        
        conn.close()
        
        print("\n✅ Migration başarılı!")
        print("🚀 Artık botu çalıştırabilirsiniz: python main.py")
    
    except Exception as e:
        print(f"❌ Hata: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    migrate()