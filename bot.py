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

def get_direct_qc_links(original_url):
    """Wchodzi na UUFinds i wyciąga linki do konkretnych zdjęć w galerii"""
    photo_urls = []
    try:
        # Kodowanie linku, aby UUFinds go przyjął
        search_url = f"https://www.uufinds.com/qcfinds?url={urllib.parse.quote(original_url)}"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'}
        
        response = requests.get(search_url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Szukamy wszystkich obrazków w sekcji galerii (zwykle mają 'storage' lub 'qc' w nazwie)
            imgs = soup.find_all('img', {'src': re.compile(r'storage|qc')})
            for img in imgs:
                src = img['src']
                if src.startswith('//'): src = 'https:' + src
                if src not in photo_urls:
                    photo_urls.append(src)
    except Exception as e:
        print(f"Błąd pobierania zdjęć: {e}")
    return photo_urls

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

class LinkButtons(View):
    def __init__(self, links):
        super().__init__()
        # USFans, Kakobuy, LitBuy (możesz podmienić pod ACBuy), MuleBuy, Weidian Raw
        order = [("USFans", "usfans"), ("Kakobuy", "kakobuy"), ("ACBuy", "acbuy"), ("Mulebuy", "mulebuy"), ("Raw", "raw")]
        for label, key in order:
            if label in links:
                self.add_item(Button(label=label, url=links[label], style=discord.ButtonStyle.link))

@bot.event
async def on_ready():
    print(f'✅ Bot gotowy! Scraper zdjęć aktywny.')

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
            
            # Pobieranie listy zdjęć bezpośrednio ze strony
            photos = get_direct_qc_links(original_url)
            
            # Tworzenie tekstu "Zdjęcie 1, Zdjęcie 2..."
            photo_links_text = ""
            if photos:
                for i, p_url in enumerate(photos[:8], 1): # max 8 linków
                    photo_links_text += f"[Zdjęcie {i}]({p_url})\n"
            else:
                photo_links_text = "*Nie znaleziono bezpośrednich zdjęć w galerii.*"

            # Przyciski
            encoded_clean = urllib.parse.quote(clean_url, safe='')
            links_dict = {
                "USFans": f"https://www.usfans.com/product/{usf_type}/{product_id}?inviteCode={AFFILIATE_CODES['usfans']}",
                "Kakobuy": f"https://www.kakobuy.com/item/details?url={encoded_clean}&affcode={AFFILIATE_CODES['kakobuy']}",
                "Mulebuy": f"https://m.mulebuy.com/pages/product/product?shoptype={mule_type}&id={product_id}&inviteCode={AFFILIATE_CODES['mulebuy']}",
                "ACBuy": f"https://m.acbuy.com/product?id={product_id}&source={ac_type}&inviteCode={AFFILIATE_CODES['acbuy']}",
                "Raw": clean_url
            }

            embed = discord.Embed(
                title="QC FINDER",
                description=(
                    f"Zdjęcia dla twojego itemu o linku:\n**{original_url}**\n\n"
                    f"{photo_links_text}\n"
                    f"Sa w linku poniżej\n\n"
                    f"🔗 [KLIKNIJ TUTAJ ABY ZOBACZYĆ QC]({uufinds_url})"
                ),
                color=0xff0000
            )
            
            if photos:
                embed.set_image(url=photos[0]) # Pokazuje pierwsze zdjęcie jako główne
            
            embed.set_footer(text=f"Created By {message.author.display_name}")

            await message.reply(embed=embed, view=LinkButtons(links_dict))

if TOKEN:
    bot.run(TOKEN)
