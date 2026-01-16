# scripts/analyze_logs.py
import re
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime

class LogAnalyzer:
    """Log dosyalarını analiz et"""
    
    def __init__(self, log_file='logs/bot.log'):
        self.log_file = Path(log_file)
    
    def analyze_errors(self, last_n_lines=1000):
        """Son hataları analiz et"""
        errors = []
        
        with open(self.log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()[-last_n_lines:]
        
        for line in lines:
            if 'ERROR' in line or 'CRITICAL' in line:
                errors.append(line.strip())
        
        return errors
    
    def count_by_level(self):
        """Log seviyelerine göre say"""
        levels = Counter()
        
        with open(self.log_file, 'r', encoding='utf-8') as f:
            for line in f:
                for level in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
                    if level in line:
                        levels[level] += 1
                        break
        
        return levels
    
    def get_user_activity(self, user_id=None):
        """Kullanıcı aktivitelerini getir"""
        activity_file = Path('logs/user_activity.log')
        activities = []
        
        if not activity_file.exists():
            return activities
        
        with open(activity_file, 'r', encoding='utf-8') as f:
            for line in f:
                if user_id is None or f"'user_id': {user_id}" in line:
                    activities.append(eval(line.split(' - ', 1)[1]))
        
        return activities
    
    def generate_report(self):
        """Genel rapor oluştur"""
        print("📈 Log Analiz Raporu")
        print("=" * 60)
        
        # Log seviyeleri
        levels = self.count_by_level()
        print("\n📊 Log Seviyeleri:")
        for level, count in levels.most_common():
            print(f"  {level}: {count}")
        
        # Son hatalar
        errors = self.analyze_errors()
        print(f"\n❌ Son {len(errors)} Hata:")
        for error in errors[-5:]:
            print(f"  {error[:100]}...")


if __name__ == '__main__':
    analyzer = LogAnalyzer()
    analyzer.generate_report()