import discord
from discord.ext import commands
from discord.ui import Button, View
import re
import urllib.parse
import os
import requests
from bs4 import BeautifulSoup

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
    """Wchodzi na uufinds z Twoim linkiem i wyciąga wszystkie zdjęcia QC"""
    images = []
    try:
        search_url = f"https://www.uufinds.com/qcfinds?url={urllib.parse.quote(original_url)}"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'}
        
        response = requests.get(search_url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            img_tags = soup.find_all('img', {'src': re.compile(r'storage|qc')})
            for img in img_tags:
                src = img['src']
                if src.startswith('//'): src = 'https:' + src
                if src not in images:
                    images.append(src)
    except Exception as e:
        print(f"Błąd scrapowania: {e}")
    return images

def extract_id(url):
    """Wyciąga ID, żeby zrobić reflink"""
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
        
        # --- RZĄD 1 (row=0): Tylko przycisk Lookup ---
        self.add_item(Button(label="Lookup 🔗", url=uufinds_url, style=discord.ButtonStyle.link, row=0))

        # --- RZĄD 2 (row=1): Twoje Reflinki ---
        order = ["Kakobuy", "USFans", "ACBuy", "Mulebuy", "RAW"]
        for label in order:
            if label in links_dict:
                self.add_item(Button(label=label, url=links_dict[label], style=discord.ButtonStyle.link, row=1))

@bot.event
async def on_ready():
    print(f'✅ Bot gotowy! Tryb prosty: Lookup + Linki aktywne na kanale {ALLOWED_CHANNEL_ID}')

@bot.event
async def on_message(message):
    if message.author.bot or message.channel.id != ALLOWED_CHANNEL_ID:
        return

    match = re.search(r'(https?://\S+)', message.content)
    if match:
        original_url = match.group(0).rstrip(').,!]')
        product_id, usf_type, ac_type, mule_type, clean_url = extract_id(original_url)
        
        if product_id:
            # Automatyczny link do wyszukiwarki UUFinds (Lookup)
            uufinds_url = f"https://www.uufinds.com/qcfinds?url={urllib.parse.quote(original_url)}"
            
            # Pobieramy zdjęcia (tylko po to, żeby wyświetlić pierwsze w Embedzie i policzyć ile ich jest)
            images = scrape_uufinds_images(original_url)
            
            if not images:
                images = ["https://www.uufinds.com/favicon.ico"]
                msg_content = "❌ Nie znalazłem ukrytych zdjęć, ale możesz sprawdzić to ręcznie pod przyciskiem **Lookup**."
            else:
                msg_content = f"**Znaleziono {len(images)} zdjęć QC.**"

            # Przygotowanie linków
            encoded_clean = urllib.parse.quote(clean_url, safe='')
            links_dict = {
                "Kakobuy": f"https://www.kakobuy.com/item/details?url={encoded_clean}&affcode={AFFILIATE_CODES['kakobuy']}",
                "USFans": f"https://www.usfans.com/product/{usf_type}/{product_id}?inviteCode={AFFILIATE_CODES['usfans']}",
                "ACBuy": f"https://m.acbuy.com/product?id={product_id}&source={ac_type}&inviteCode={AFFILIATE_CODES['acbuy']}",
                "Mulebuy": f"https://m.mulebuy.com/pages/product/product?shoptype={mule_type}&id={product_id}&inviteCode={AFFILIATE_CODES['mulebuy']}",
                "RAW": clean_url
            }

            # Tworzenie Embedu
            embed = discord.Embed(
                title="Zdjęcia produktu",
                color=0x2b2d31
            )
            embed.set_image(url=images[0]) # Wyświetla tylko pierwsze zdjęcie jako podgląd
            
            # Odpalenie interfejsu z przyciskami (View)
            view = QCView(links_dict, uufinds_url)
            
            await message.reply(content=msg_content, embed=embed, view=view)

if TOKEN:
    bot.run(TOKEN)
