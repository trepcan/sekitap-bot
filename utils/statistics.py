"""
Bot İstatistik Yöneticisi
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any


class BotStatistics:
    """Bot istatistiklerini yönet"""
    
    def __init__(self, stats_file: str = 'logs/stats.json'):
        self.stats_file = Path(stats_file)
        self.stats_file.parent.mkdir(exist_ok=True)
        
        self.stats = {
            # Genel
            "surum": "9.5",
            "baslangic_zamani": datetime.now().isoformat(),
            "son_islem_zamani": None,
            "islem_tipi": "Başlatılıyor",
            
            # Mesaj İstatistikleri
            "toplam_mesaj": 0,
            "toplam_duzenleme": 0,
            "basarili": 0,
            "basarisiz": 0,
            
            # Geçmiş Tarama
            "gecmis_tarama_sayac": 0,
            "gecmis_tarama_hata": 0,
            "son_tarama_zamani": None,
            "son_tarama_islem_sayisi": 0,
            
            # Performans
            "toplam_api_cagrisi": 0,
            "basarili_api": 0,
            "basarisiz_api": 0,
        }
        
        self._load_stats()
    
    def _load_stats(self):
        """Stats dosyasından yükle"""
        if self.stats_file.exists():
            try:
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    # Sadece mevcut anahtarları güncelle
                    for key in self.stats.keys():
                        if key in loaded:
                            self.stats[key] = loaded[key]
            except Exception as e:
                print(f"⚠️ Stats yüklenemedi: {e}")
    
    def _save_stats(self):
        """Stats'ı dosyaya kaydet"""
        try:
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.stats, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Stats kaydedilemedi: {e}")
    
    def increment(self, key: str, amount: int = 1):
        """Sayacı artır"""
        if key not in self.stats:
            self.stats[key] = 0
        self.stats[key] += amount
        self._save_stats()
    
    def set(self, key: str, value: Any):
        """Değer ata"""
        self.stats[key] = value
        self._save_stats()
    
    def get(self, key: str, default=None):
        """Değer al"""
        return self.stats.get(key, default)
    
    def get_all(self) -> Dict:
        """Tüm stats'ı al"""
        return self.stats.copy()
    
    def reset(self):
        """Sayaçları sıfırla (zamanlama bilgilerini koru)"""
        baslangic = self.stats.get("baslangic_zamani")
        surum = self.stats.get("surum")
        
        self.stats = {
            "surum": surum,
            "baslangic_zamani": baslangic,
            "son_islem_zamani": None,
            "islem_tipi": "Sıfırlandı",
            "toplam_mesaj": 0,
            "toplam_duzenleme": 0,
            "basarili": 0,
            "basarisiz": 0,
            "gecmis_tarama_sayac": 0,
            "gecmis_tarama_hata": 0,
            "son_tarama_zamani": None,
            "son_tarama_islem_sayisi": 0,
            "toplam_api_cagrisi": 0,
            "basarili_api": 0,
            "basarisiz_api": 0,
        }
        self._save_stats()
    
    def get_report(self) -> str:
        """Detaylı rapor oluştur"""
        try:
            baslangic = datetime.fromisoformat(
                self.stats.get("baslangic_zamani", datetime.now().isoformat())
            )
            uptime = datetime.now() - baslangic
            uptime_str = f"{uptime.days} gün, {uptime.seconds//3600} saat"
        except:
            uptime_str = "Bilinmiyor"
        
        # Başarı oranı
        toplam = self.stats.get('basarili', 0) + self.stats.get('basarisiz', 0)
        if toplam > 0:
            basari_orani = (self.stats.get('basarili', 0) / toplam) * 100
        else:
            basari_orani = 0
        
        # API başarı oranı
        toplam_api = self.stats.get('basarili_api', 0) + self.stats.get('basarisiz_api', 0)
        if toplam_api > 0:
            api_basari = (self.stats.get('basarili_api', 0) / toplam_api) * 100
        else:
            api_basari = 0
        
        report = f"""📊 sEkitap Bot İstatistikleri
{'='*40}

⏱️  Çalışma Süresi: {uptime_str}
🔧 Sürüm: {self.stats.get('surum', 'N/A')}
📍 Mod: {self.stats.get('islem_tipi', 'N/A')}

📨 MESAJ İSTATİSTİKLERİ:
   • Toplam Mesaj: {self.stats.get('toplam_mesaj', 0)}
   • Düzenleme: {self.stats.get('toplam_duzenleme', 0)}
   • Başarılı: {self.stats.get('basarili', 0)}
   • Başarısız: {self.stats.get('basarisiz', 0)}
   • Başarı Oranı: {basari_orani:.1f}%

🔍 GEÇMİŞ TARAMA:
   • İşlenen: {self.stats.get('gecmis_tarama_sayac', 0)}
   • Hata: {self.stats.get('gecmis_tarama_hata', 0)}
   • Son İşlem: {self.stats.get('son_tarama_islem_sayisi', 0)}

🌐 API İSTATİSTİKLERİ:
   • Toplam Çağrı: {self.stats.get('toplam_api_cagrisi', 0)}
   • Başarılı: {self.stats.get('basarili_api', 0)}
   • Başarısız: {self.stats.get('basarisiz_api', 0)}
   • Başarı Oranı: {api_basari:.1f}%
"""
        
        if self.stats.get('son_islem_zamani'):
            try:
                son_islem = datetime.fromisoformat(self.stats['son_islem_zamani'])
                report += f"\n🕐 Son İşlem: {son_islem.strftime('%Y-%m-%d %H:%M:%S')}"
            except:
                pass
        
        if self.stats.get('son_tarama_zamani'):
            try:
                son_tarama = datetime.fromisoformat(self.stats['son_tarama_zamani'])
                report += f"\n🔍 Son Tarama: {son_tarama.strftime('%Y-%m-%d %H:%M:%S')}"
            except:
                pass
        
        return report


# Global instance
bot_stats = BotStatistics()