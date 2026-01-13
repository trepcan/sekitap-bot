"""
1000Kitap.com scraper
Orijinal ad, seri, çevirmen zenginleştirmesi ile
"""
import json
import re
from typing import Optional, Dict, Any, Tuple
from urllib.parse import quote_plus
import logging
from bs4 import BeautifulSoup

from scrapers.base_scraper import BaseScraper
from utils.text_utils import metin_duzelt, turkce_baslik
from utils.helpers import tur_cevir_ve_filtrele
from config.constants import veri_kalibi

logger = logging.getLogger(__name__)


class BinKitapScraper(BaseScraper):
    """1000Kitap.com scraper"""
    
    BASE_URL = "https://1000kitap.com"
    
    def get_name(self) -> str:
        return "1000Kitap"
    
    def search(self, query: str, direct_url: str = None) -> Optional[Dict[str, Any]]:
        """
        1000Kitap'ta kitap ara
        
        Args:
            query: Arama terimi
            direct_url: Direkt kitap URL'si
        
        Returns:
            Kitap bilgileri veya None
        """
        try:
            if direct_url:
                url = direct_url
            else:
                encoded_query = quote_plus(query)
                url = f"{self.BASE_URL}/ara?q={encoded_query}&bolum=kitaplar"
            
            response = self.get_response(url)
            if not response:
                return None
            
            # 403 kontrolü
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
                    
                    if not soup:
                        return None
                else:
                    # Belki zaten detay sayfasındayız?
                    if not self._is_detail_page(soup):
                        logger.warning("⚠️ 1000Kitap'ta sonuç bulunamadı")
                        return None
            
            # Parse et
            return self._parse_book_page(soup, link)
            
        except Exception as e:
            logger.error(f"❌ 1000Kitap arama hatası: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _find_first_result(self, soup: BeautifulSoup) -> Optional[Any]:
        """İlk arama sonucunu bul"""
        # Regex ile kitap linkini bul
        all_links = soup.find_all('a', href=True)
        for a in all_links:
            href = a['href']
            # /kitap/kitap-adi--12345 formatı
            if re.search(r'/kitap/[\w-]+--\d+$', href):
                return a
        
        # Alternatif selector
        return soup.select_one('.kn-content-item a')
    
    def _is_detail_page(self, soup: BeautifulSoup) -> bool:
        """Detay sayfasında mıyız?"""
        script_tag = soup.find("script", id="__NEXT_DATA__")
        if not script_tag:
            return False
        
        try:
            json_data = json.loads(script_tag.string)
            props = json_data.get("props", {}).get("pageProps", {})
            
            # Yeni JSON yapısı
            if props.get("book"):
                return True
            
            # Eski JSON yapısı
            if props.get("response", {}).get("_sonuc", {}).get("kitap"):
                return True
        except:
            pass
        
        return False
    
    def _extract_series_from_title(self, text: str) -> Tuple[str, Optional[str]]:
        """
        Başlık veya orijinal addan seri bilgisini ayır
        
        Örnekler:
            "Dune (Dune #1)" -> ("Dune", "Dune #1")
            "Harry Potter (Harry Potter #1)" -> ("Harry Potter", "Harry Potter #1")
            "Foundation and Empire" -> ("Foundation and Empire", None)
        
        Args:
            text: Başlık veya orijinal ad
        
        Returns:
            (temiz_baslik, seri_bilgisi)
        """
        if not text:
            return text, None
        
        # Parantez içinde seri formatını ara: (Seri Adı #X)
        pattern = r'\s*\(([^)]+#\d+)\)\s*$'
        match = re.search(pattern, text)
        
        if match:
            seri = match.group(1).strip()
            temiz_baslik = re.sub(pattern, '', text).strip()
            return temiz_baslik, seri
        
        return text, None
    
    def _parse_book_page(self, soup: BeautifulSoup, url: str) -> Optional[Dict[str, Any]]:
        """
        Kitap detay sayfasını parse et
        Hem yeni hem eski JSON yapılarını destekler
        """
        data = veri_kalibi()
        data["link"] = url
        
        try:
            # Script tag içindeki JSON'u bul
            script_tag = soup.find('script', id='__NEXT_DATA__')
            if not script_tag:
                logger.warning("⚠️ __NEXT_DATA__ script bulunamadı")
                return None
            
            json_data = json.loads(script_tag.string)
            props = json_data.get('props', {}).get('pageProps', {})
            
            # 1️⃣ Yeni JSON yapısı dene (props.book)
            kitap_json = props.get('book')
            
            if kitap_json:
                logger.debug("ℹ️ Yeni JSON yapısı kullanılıyor")
                self._parse_new_format(kitap_json, data)
            else:
                # 2️⃣ Eski JSON yapısı dene (props.response._sonuc.kitap)
                logger.debug("ℹ️ Eski JSON yapısı deneniyor")
                response = props.get('response', {})
                sonuc = response.get('_sonuc', {})
                kitap_json = sonuc.get('kitap')
                
                if kitap_json:
                    logger.debug("ℹ️ Eski JSON yapısı kullanılıyor")
                    self._parse_old_format(sonuc, data)
                else:
                    logger.warning("⚠️ JSON'da kitap verisi bulunamadı")
                    return None
            
            # HTML'den eksik bilgileri tamamla
            self._parse_html_fallback(soup, data)
            
            logger.info("✅ 1000Kitap parse başarılı")
            return data
        
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON parse hatası: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Parse hatası: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _parse_new_format(self, kitap_json: Dict, data: Dict[str, Any]):
        """
        Yeni JSON formatını parse et
        Format: props.pageProps.book
        """
        # Başlık
        if kitap_json.get('name'):
            data["baslik"] = metin_duzelt(kitap_json['name'])
            logger.info(f"📖 Başlık: {data['baslik']}")
        
        # Yazar
        if kitap_json.get('yazarlar') and len(kitap_json['yazarlar']) > 0:
            yazarlar = []
            for yazar in kitap_json['yazarlar']:
                if yazar.get('name'):
                    yazarlar.append(metin_duzelt(yazar['name']))
            
            if yazarlar:
                data["yazar"] = ", ".join(yazarlar)
                logger.info(f"✍️ Yazar: {data['yazar']}")
        
        # Çevirmen
        if kitap_json.get('cevirmenler') and len(kitap_json['cevirmenler']) > 0:
            cevirmenler = []
            for cevirmen in kitap_json['cevirmenler']:
                if cevirmen.get('name'):
                    cevirmenler.append(metin_duzelt(cevirmen['name']))
            
            if cevirmenler:
                data["cevirmen"] = ", ".join(cevirmenler)
                logger.info(f"🔤 Çevirmen: {data['cevirmen']}")
        
        # Baskı bilgileri
        baski_bilgileri = kitap_json.get('baskiBilgileri', {})
        
        # ➕ Orijinal ad (seri bilgisini ayır)
        if baski_bilgileri.get('orijinalAdi'):
            original_raw = metin_duzelt(baski_bilgileri['orijinalAdi'])
            
            # Seri bilgisini ayır
            original_clean, seri_from_title = self._extract_series_from_title(original_raw)
            
            # Başlıkla aynı değilse ekle
            if original_clean and original_clean != data.get('baslik'):
                data["orijinal_ad"] = original_clean
                logger.info(f"🌍 Orijinal Ad: {data['orijinal_ad']}")
            
            # Seri bilgisi varsa ve henüz yoksa ekle
            if seri_from_title and not data.get("seri"):
                data["seri"] = seri_from_title
                logger.info(f"📚 Seri (Orijinal Ad'dan): {data['seri']}")
        
        # ➕ Seri (doğrudan alan)
        if baski_bilgileri.get('seriAdi') and not data.get("seri"):
            seri_adi = metin_duzelt(baski_bilgileri['seriAdi'])
            seri_no = baski_bilgileri.get('seriNo', '')
            
            if seri_no:
                data["seri"] = f"{seri_adi} #{seri_no}"
            else:
                data["seri"] = seri_adi
            
            logger.info(f"📚 Seri: {data['seri']}")
        
        # Yayınevi
        if baski_bilgileri.get('yayinEvi'):
            data["yayinevi"] = turkce_baslik(metin_duzelt(baski_bilgileri['yayinEvi']))
        
        # Sayfa sayısı
        if baski_bilgileri.get('sayfaSayisi'):
            data["sayfa"] = str(baski_bilgileri['sayfaSayisi'])
        
        # ISBN
        if baski_bilgileri.get('isbn'):
            data["isbn"] = baski_bilgileri['isbn'].replace('-', '')
        
        # Tarih
        if baski_bilgileri.get('basimTarihi'):
            data["tarih"] = str(baski_bilgileri['basimTarihi'])
        elif baski_bilgileri.get('baskiYili'):
            data["tarih"] = str(baski_bilgileri['baskiYili'])
        
        # Puan ve oy sayısı
        if kitap_json.get('rate'):
            try:
                puan = float(kitap_json['rate'])
                # 10'luk sistemse 5'e dönüştür
                if puan > 5:
                    puan = puan / 2
                data["puan"] = f"{puan:.1f}"
            except:
                data["puan"] = str(kitap_json['rate'])
        
        if kitap_json.get('rateCount'):
            data["oy_sayisi"] = str(kitap_json['rateCount'])
        
        # Açıklama
        if kitap_json.get('excerpt'):
            data["aciklama"] = metin_duzelt(kitap_json['excerpt'])
    
    def _parse_old_format(self, sonuc: Dict, data: Dict[str, Any]):
        """
        Eski JSON formatını parse et
        Format: props.pageProps.response._sonuc
        """
        kitap = sonuc.get("kitap", {})
        
        # Temel bilgiler
        if kitap.get("adi"):
            data["baslik"] = metin_duzelt(kitap["adi"])
            logger.info(f"📖 Başlık: {data['baslik']}")
        
        if kitap.get("isbn"):
            data["isbn"] = str(kitap["isbn"]).replace("-", "")
        
        # Yazarlar ve çevirmenler
        yazarlar = kitap.get("yazarlar", [])
        yazar_listesi = []
        cevirmen_listesi = []
        
        for y in yazarlar:
            ad = metin_duzelt(y.get("adi", ""))
            if not ad:
                continue
            
            tur = y.get("kitapYazarTurBaslik", "").lower()
            if "çevirmen" in tur:
                cevirmen_listesi.append(ad)
            else:
                yazar_listesi.append(ad)
        
        if yazar_listesi:
            data["yazar"] = ", ".join(yazar_listesi)
            logger.info(f"✍️ Yazar: {data['yazar']}")
        
        if cevirmen_listesi:
            data["cevirmen"] = ", ".join(cevirmen_listesi)
            logger.info(f"🔤 Çevirmen: {data['cevirmen']}")
        
        # ➕ Seri (eski format - doğrudan alan)
        if kitap.get("seriAdi"):
            seri_adi = metin_duzelt(kitap["seriAdi"])
            seri_no = kitap.get("seriNo", "")
            
            if seri_no:
                data["seri"] = f"{seri_adi} #{seri_no}"
            else:
                data["seri"] = seri_adi
            
            logger.info(f"📚 Seri: {data['seri']}")
        
        # Puan ve oy
        try:
            oy_sayisi = kitap.get("oySayisi")
            if oy_sayisi:
                data["oy_sayisi"] = str(oy_sayisi)
                
                # En az 100 oy varsa puanı ekle
                if int(oy_sayisi) >= 100:
                    raw_puan = kitap.get("puan")
                    if raw_puan:
                        puan_val = float(raw_puan)
                        # 10'luk sistemse 5'e dönüştür
                        if puan_val > 5:
                            puan_val /= 2
                        data["puan"] = f"{puan_val:.1f}"
        except:
            pass
        
        # Gönderilerden detaylı bilgi
        gonderiler = sonuc.get("gonderiler", [])
        for gonderi in gonderiler:
            if gonderi.get("renderTuru") == "kitapHakkinda":
                # Açıklama
                bilgi = gonderi.get("bilgi", "")
                if not bilgi or len(bilgi) < 5:
                    parse_list = gonderi.get("bilgiParse", {}).get("parse", [])
                    if parse_list:
                        bilgi = "\n\n".join([str(p) for p in parse_list if isinstance(p, str)])
                
                if bilgi:
                    data["aciklama"] = metin_duzelt(bilgi)
                
                # Baskı bilgileri
                hakkinda = gonderi.get("hakkinda", {})
                baski = hakkinda.get("baskiBilgileri", {})
                
                if baski:
                    if baski.get("yayinevi"):
                        data["yayinevi"] = turkce_baslik(metin_duzelt(baski["yayinevi"]))
                    
                    if baski.get("sayfaSayisi"):
                        data["sayfa"] = str(baski["sayfaSayisi"])
                    
                    tarih = baski.get("baskiYazi") or baski.get("baskiYili")
                    if tarih:
                        data["tarih"] = metin_duzelt(str(tarih))
                    
                    # ➕ Orijinal ad (eski format - seri bilgisini ayır)
                    if baski.get("orijinalAdi"):
                        original_raw = metin_duzelt(baski["orijinalAdi"])
                        
                        # Seri bilgisini ayır
                        original_clean, seri_from_title = self._extract_series_from_title(original_raw)
                        
                        # Başlıkla aynı değilse ekle
                        if original_clean and original_clean != data.get("baslik"):
                            data["orijinal_ad"] = original_clean
                            logger.info(f"🌍 Orijinal Ad: {data['orijinal_ad']}")
                        
                        # Seri bilgisi varsa ve henüz yoksa ekle
                        if seri_from_title and not data.get("seri"):
                            data["seri"] = seri_from_title
                            logger.info(f"📚 Seri (Orijinal Ad'dan): {data['seri']}")
                
                # Türler
                try:
                    kidDizi = hakkinda.get("kidDizi", [])
                    if kidDizi:
                        tur_names = [metin_duzelt(k.get("adi", "")) for k in kidDizi if k.get("adi")]
                        if tur_names:
                            data["turu"] = tur_cevir_ve_filtrele(tur_names)
                except:
                    pass
                
                break
    
    def _parse_html_fallback(self, soup: BeautifulSoup, data: Dict[str, Any]):
        """
        HTML'den eksik bilgileri tamamla (fallback)
        """
        try:
            # Açıklama
            if not data.get("aciklama"):
                desc_div = soup.select_one('.text-alt')
                if not desc_div:
                    desc_div = soup.select_one('div[property="description"]')
                
                if desc_div:
                    data["aciklama"] = metin_duzelt(desc_div.text)
            
            # Detay bilgileri
            dr_elements = soup.select('div.dr')
            tur_listesi = []
            
            for el in dr_elements:
                label_span = el.select_one('span.text-silik-v2')
                if not label_span:
                    continue
                
                label = label_span.text.strip()
                
                # Değer span'ini bul
                val_span = el.find_next_sibling('div')
                if val_span:
                    val_span = val_span.select_one('span.text-14')
                
                if not val_span:
                    parent = el.find_parent('div', class_='flex-row')
                    if parent:
                        val_div = parent.select_one('div.flex-1')
                        if val_div:
                            val_span = val_div.select_one('span.text-14')
                
                if val_span:
                    val = metin_duzelt(val_span.text)
                    
                    if "Sayfa Sayısı" in label and not data.get("sayfa"):
                        data["sayfa"] = val
                    elif "Basım Tarihi" in label and not data.get("tarih"):
                        data["tarih"] = val
                    elif "Yayınevi" in label and not data.get("yayinevi"):
                        data["yayinevi"] = turkce_baslik(val)
                    elif "Orijinal Adı" in label and not data.get("orijinal_ad"):
                        # ➕ HTML'den gelen orijinal addan da seri ayır
                        original_clean, seri_from_html = self._extract_series_from_title(val)
                        
                        if original_clean != data.get("baslik"):
                            data["orijinal_ad"] = original_clean
                            logger.info(f"🌍 Orijinal Ad (HTML): {original_clean}")
                        
                        if seri_from_html and not data.get("seri"):
                            data["seri"] = seri_from_html
                            logger.info(f"📚 Seri (HTML): {seri_from_html}")
                    elif "ISBN" in label and not data.get("isbn"):
                        data["isbn"] = val.replace("-", "")
                
                # Türler
                if "Türler" in el.text:
                    parent = el.find_parent('div', class_='flex-row')
                    if parent:
                        links = parent.select('a[role="link"] span.text-mavi')
                        for l in links:
                            tur_listesi.append(metin_duzelt(l.text))
            
            # Tür listesi varsa ve henüz yoksa ekle
            if tur_listesi and not data.get("turu"):
                data["turu"] = tur_cevir_ve_filtrele(tur_listesi)
        
        except Exception as e:
            logger.debug(f"HTML fallback hatası (göz ardı edilebilir): {e}")