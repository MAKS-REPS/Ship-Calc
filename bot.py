import discord
from discord.ext import commands
from discord.ui import Button, View
import re
import urllib.parse
import os
import requests

# --- KONFIGURACJA ---
TOKEN = os.getenv('DISCORD_TOKEN')
ALLOWED_CHANNEL_ID = 1457766095531278529 

AFFILIATE_CODES = {
    "usfans": "DJPZ6T",
    "acbuy": "KV2WLD",
    "kakobuy": "maksr3ps",
    "mulebuy": "201154557"
}

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

def scrape_uufinds_images(original_url):
    """Próbuje wyciągnąć zdjęcia używając różnych metod udawania przeglądarki"""
    images = []
    try:
        # 1. Przygotowanie linku wyszukiwania
        encoded_url = urllib.parse.quote(original_url, safe='')
        search_url = f"https://www.uufinds.com/qcfinds?url={encoded_url}"
        
        # 2. Bardzo dokładne nagłówki udające prawdziwego człowieka na iPhone/Chrome
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'pl-PL,pl;q=0.9',
            'Referer': 'https://www.uufinds.com/',
            'Connection': 'keep-alive'
        }
        
        # Pobieramy stronę
        session = requests.Session()
        response = session.get(search_url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            html = response.text
            # Metoda "Brute Force": szukamy wszystkiego co wygląda jak link do zdjęcia QC w kodzie źródłowym
            # Szukamy linków zaczynających się od https:// i zawierających 'storage' lub 'qc' oraz kończących się na jpg/png/webp
            raw_links = re.findall(r'https?://[^\s"\'<>]+(?:storage|qc|product)[^\s"\'<>]+(?:\.jpg|\.png|\.webp|\.jpeg)', html, re.IGNORECASE)
            
            for link in raw_links:
                # Czyszczenie linku z ewentualnych śmieci po regexie
                clean_link = link.split('\\')[0].split('"')[0].split("'")[0]
                if clean_link not in images and "favicon" not in clean_link:
                    images.append(clean_link)

            # Jeśli regex nic nie znalazł, próbujemy standardowo przez tagi img (na wszelki wypadek)
            if not images:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(html, 'html.parser')
                for img in soup.find_all('img'):
                    src = img.get('src') or img.get('data-src') or img.get('lazy-src')
                    if src:
                        if src.startswith('//'): src = 'https:' + src
                        if any(x in src.lower() for x in ['qc', 'storage', 'product']):
                            if src not in images: images.append(src)
                            
    except Exception as e:
        print(f"Błąd scrapowania: {e}")
        
    return images

def extract_id(url):
    url = url.lower()
    if "taobao.com" in url or "tmall.com" in url:
        m = re.search(r'id=(\d+)', url)
        if m: return m.group(1), "1", "TB", "TAOBAO", f"https://item.taobao.com/item.htm?id={m.group(1)}"
    if "weidian.com" in url:
        m = re.search(r'(?:itemid|item_id|itemID=)(\d+)', url)
        if not m: m = re.search(r'itemid=(\d+)', url)
        if m: return m.group(1), "1", "WD", "WEIDIAN", f"https://weidian.com/item.html?itemID={m.group(1)}"
    if "1688.com" in url:
        m = re.search(r'(?:offer/|id=)(\d+)', url)
        if m: return m.group(1), "2", "1688", "ALI_1688", f"https://detail.1688.com/offer/{m.group(1)}.html"
    return None, None, None, None, None

class QCView(View):
    def __init__(self, links_dict, uufinds_url):
        super().__init__(timeout=None)
        self.add_item(Button(label="Lookup 🔗", url=uufinds_url, style=discord.ButtonStyle.link, row=0))
        order = ["Kakobuy", "USFans", "ACBuy", "Mulebuy", "RAW"]
        for label in order:
            if label in links_dict:
                self.add_item(Button(label=label, url=links_dict[label], style=discord.ButtonStyle.link, row=1))

@bot.event
async def on_ready():
    print(f'✅ Bot QC READY | Tryb Brute-Force Scraper')

@bot.event
async def on_message(message):
    if message.author.bot or message.channel.id != ALLOWED_CHANNEL_ID:
        return

    match = re.search(r'(https?://\S+)', message.content)
    if match:
        original_url = match.group(0).rstrip(').,!]')
        product_id, usf_type, ac_type, mule_type, clean_url = extract_id(original_url)
        
        if product_id:
            uufinds_url = f"https://www.uufinds.com/qcfinds?url={urllib.parse.quote(original_url)}"
            images = scrape_uufinds_images(original_url)
            
            # Tworzenie Embedu
            embed = discord.Embed(title="Zdjęcia produktu", color=0x2b2d31)
            
            if images:
                embed.set_image(url=images[0])
                msg_content = f"**Znaleziono {len(images)} zdjęć QC.**"
            else:
                # Jeśli bot nadal nic nie widzi, dajemy logo UUFinds, żeby embed nie był pusty
                embed.set_image(url="https://www.uufinds.com/favicon.ico")
                msg_content = "❌ Bot nie mógł pobrać zdjęć automatycznie (zabezpieczenie strony). Kliknij **Lookup**, aby je zobaczyć."

            links_dict = {
                "Kakobuy": f"https://www.kakobuy.com/item/details?url={urllib.parse.quote(clean_url, safe='')}&affcode={AFFILIATE_CODES['kakobuy']}",
                "USFans": f"https://www.usfans.com/product/{usf_type}/{product_id}?inviteCode={AFFILIATE_CODES['usfans']}",
                "ACBuy": f"https://m.acbuy.com/product?id={product_id}&source={ac_type}&inviteCode={AFFILIATE_CODES['acbuy']}",
                "Mulebuy": f"https://m.mulebuy.com/pages/product/product?shoptype={mule_type}&id={product_id}&inviteCode={AFFILIATE_CODES['mulebuy']}",
                "RAW": clean_url
            }

            view = QCView(links_dict, uufinds_url)
            await message.reply(content=msg_content, embed=embed, view=view)

if TOKEN:
    bot.run(TOKEN)
