import json
import re
from typing import Optional, Dict, Any
from urllib.parse import quote_plus
import logging

from scrapers.base_scraper import BaseScraper
from parsers.data_parser import DataParser
from utils.text_utils import metin_duzelt, turkce_baslik, baslik_teknik_temizle
from utils.helpers import tur_cevir_ve_filtrele
from config.constants import veri_kalibi

logger = logging.getLogger(__name__)


class BinKitapScraper(BaseScraper):
    """1000Kitap.com scraper"""
    
    BASE_URL = "https://1000kitap.com"
    
    def get_name(self) -> str:
        return "1000Kitap"
    
    def search(self, query: str, direct_url: str = None) -> Optional[Dict[str, Any]]:
        """1000Kitap'ta arama yap"""
        try:
            if direct_url:
                url = direct_url
            else:
                encoded_query = quote_plus(query)
                url = f"{self.BASE_URL}/ara?q={encoded_query}&bolum=kitaplar"
            
            response = self.get_response(url)
            if not response:
                return None
            
            if response.status_code == 403 or "blocked" in response.text.lower():
                logger.warning("⚠️ 1000Kitap erişim engellendi")
                return None
            
            response.encoding = 'utf-8'
            soup = self.parse_html(response)
            if not soup:
                return None
            
            link = url
            
            # Direkt URL değilse, arama sonucunda ilk kitabı bul
            if not direct_url:
                sonuc_link = self._find_first_result(soup)
                if sonuc_link:
                    link = sonuc_link['href']
                    if not link.startswith("http"):
                        link = self.BASE_URL + link
                    
                    # Detay sayfasını çek
                    response = self.get_response(link)
                    if not response:
                        return None
                    response.encoding = 'utf-8'
                    soup = self.parse_html(response)
                else:
                    # Belki zaten detay sayfasındayız?
                    if not self._is_detail_page(soup):
                        return None
            
            return self._parse_detail_page(soup, link)
            
        except Exception as e:
            logger.error(f"❌ 1000Kitap arama hatası: {e}")
            return None
    
    def _find_first_result(self, soup) -> Optional[Any]:
        """İlk arama sonucunu bul"""
        # Regex ile kitap linkini bul
        all_links = soup.find_all('a', href=True)
        for a in all_links:
            href = a['href']
            if re.search(r'/kitap/[\w-]+--\d+$', href):
                return a
        
        # Alternatif selector
        return soup.select_one('.kn-content-item a')
    
    def _is_detail_page(self, soup) -> bool:
        """Detay sayfasında mıyız?"""
        script_tag = soup.find("script", id="__NEXT_DATA__")
        if script_tag:
            try:
                jd = json.loads(script_tag.string)
                if jd.get("props", {}).get("pageProps", {}).get("response", {}).get("_sonuc", {}).get("kitap"):
                    return True
            except:
                pass
        return False
    
    def _parse_detail_page(self, soup, link: str) -> Optional[Dict[str, Any]]:
        """Detay sayfasını parse et"""
        data = veri_kalibi()
        data["link"] = link
        
        try:
            # JSON verilerini parse et
            self._parse_json(soup, data)
            
            # HTML'den eksik verileri tamamla
            if not data["aciklama"]:
                self._extract_description(soup, data)
            
            if not data["baslik"] or not data["sayfa"]:
                self._extract_details(soup, data)
            
            # Başlığı temizle
            if data["baslik"]:
                data["baslik"] = baslik_teknik_temizle(data["baslik"])
            
            # Meta tag'lerden ek bilgi
            DataParser.extract_meta_tags(soup, data)
            DataParser.extract_json_ld(soup, data)
            
            return data if data["baslik"] else None
            
        except Exception as e:
            logger.error(f"❌ Parse hatası: {e}")
            return None
    
    def _parse_json(self, soup, data: Dict[str, Any]):
        """__NEXT_DATA__ JSON'unu parse et"""
        try:
            script_tag = soup.find("script", id="__NEXT_DATA__")
            if not script_tag:
                return
            
            json_data = json.loads(script_tag.string)
            sonuc = json_data.get("props", {}).get("pageProps", {}).get("response", {}).get("_sonuc", {})
            kitap = sonuc.get("kitap", {})
            
            if not kitap:
                return
            
            # Temel bilgiler
            data["baslik"] = metin_duzelt(kitap.get("adi"))
            data["isbn"] = str(kitap.get("isbn", "")).replace("-", "")
            
            # Yazarlar ve çevirmenler
            yazarlar = kitap.get("yazarlar", [])
            yazar_listesi = []
            cevirmen_listesi = []
            
            for y in yazarlar:
                ad = metin_duzelt(y.get("adi"))
                tur = y.get("kitapYazarTurBaslik", "").lower()
                if "çevirmen" in tur:
                    cevirmen_listesi.append(ad)
                else:
                    yazar_listesi.append(ad)
            
            if yazar_listesi:
                data["yazar"] = ", ".join(yazar_listesi)
            if cevirmen_listesi:
                data["cevirmen"] = ", ".join(cevirmen_listesi)
            
            # Puan ve oy
            try:
                oy_sayisi = kitap.get("oySayisi")
                if oy_sayisi:
                    data["oy_sayisi"] = str(oy_sayisi)
                    if int(oy_sayisi) >= 100:
                        raw_puan = kitap.get("puan")
                        if raw_puan:
                            puan_val = float(raw_puan)
                            if puan_val > 5:
                                puan_val /= 2
                            data["puan"] = f"{puan_val:.1f}"
            except:
                pass
            
            # Gönderilerden detaylı bilgi
            gonderiler = sonuc.get("gonderiler", [])
            for gonderi in gonderiler:
                if gonderi.get("renderTuru") == "kitapHakkinda":
                    bilgi = gonderi.get("bilgi", "")
                    if not bilgi or len(bilgi) < 5:
                        parse_list = gonderi.get("bilgiParse", {}).get("parse", [])
                        if parse_list:
                            bilgi = "\n\n".join([str(p) for p in parse_list if isinstance(p, str)])
                    data["aciklama"] = metin_duzelt(bilgi)
                    
                    # Baskı bilgileri
                    hakkinda = gonderi.get("hakkinda", {})
                    baski = hakkinda.get("baskiBilgileri", {})
                    if baski:
                        data["yayinevi"] = turkce_baslik(metin_duzelt(baski.get("yayinevi", "")))
                        data["sayfa"] = str(baski.get("sayfaSayisi", ""))
                        data["tarih"] = metin_duzelt(baski.get("baskiYazi", "") or baski.get("baskiYili", ""))
                        data["orijinal_ad"] = metin_duzelt(baski.get("orijinalAdi", ""))
                    
                    # Türler
                    try:
                        kidDizi = hakkinda.get("kidDizi", [])
                        if kidDizi:
                            tur_names = [metin_duzelt(k.get("adi", "")) for k in kidDizi]
                            data["turu"] = tur_cevir_ve_filtrele(tur_names)
                    except:
                        pass
                    break
                    
        except Exception as e:
            logger.error(f"⚠️ JSON parse hatası: {e}")
    
    def _extract_description(self, soup, data: Dict[str, Any]):
        """HTML'den açıklama çıkar"""
        desc_div = soup.select_one('.text-alt')
        if not desc_div:
            desc_div = soup.select_one('div[property="description"]')
        if desc_div:
            data["aciklama"] = metin_duzelt(desc_div.text)
    
    def _extract_details(self, soup, data: Dict[str, Any]):
        """HTML'den detay bilgileri çıkar"""
        dr_elements = soup.select('div.dr')
        tur_listesi = []
        
        for el in dr_elements:
            label_span = el.select_one('span.text-silik-v2')
            if label_span:
                label = label_span.text.strip()
                val_span = el.find_next_sibling('div').select_one('span.text-14') if el.find_next_sibling('div') else None
                
                if not val_span:
                    parent = el.find_parent('div', class_='flex-row')
                    if parent:
                        val_div = parent.select_one('div.flex-1')
                        if val_div:
                            val_span = val_div.select_one('span.text-14')
                
                if val_span:
                    val = metin_duzelt(val_span.text)
                    if "Sayfa Sayısı" in label:
                        data["sayfa"] = val
                    elif "Basım Tarihi" in label:
                        data["tarih"] = val
                    elif "Yayınevi" in label:
                        data["yayinevi"] = turkce_baslik(val)
                    elif "Orijinal Adı" in label:
                        data["orijinal_ad"] = val
                    elif "ISBN" in label:
                        data["isbn"] = val
            
            # Türler
            if "Türler" in el.text:
                parent = el.find_parent('div', class_='flex-row')
                if parent:
                    links = parent.select('a[role="link"] span.text-mavi')
                    for l in links:
                        tur_listesi.append(metin_duzelt(l.text))
        
        if tur_listesi and not data["turu"]:
            data["turu"] = tur_cevir_ve_filtrele(tur_listesi)