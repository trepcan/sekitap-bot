#!/usr/bin/env python3
"""search_book() test"""
import asyncio
from services.book_service import book_service

async def test():
    queries = [
        "Harry Potter",
        "C_S_Lewis_Narnia_Günlükleri_6_Gümüş_Sandalye.epub",
        "GIBBERISH_INVALID_QUERY_12345",
    ]
    
    for query in queries:
        print(f"\n🔍 Test: {query}")
        
        try:
            result = await book_service.search_book(query)
            
            print(f"   Tip: {type(result)}")
            print(f"   Değer: {result}")
            
            if result is None:
                print("   ❌ None döndü!")
            elif isinstance(result, tuple):
                bilgi, kaynak, basarili = result
                print(f"   ✅ Tuple: kaynak={kaynak}, basarili={basarili}")
            else:
                print(f"   ⚠️ Beklenmeyen tip: {type(result)}")
        
        except Exception as e:
            print(f"   ❌ Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test())