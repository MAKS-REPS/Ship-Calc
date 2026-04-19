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

def get_uufinds_qc(product_id):
    """Automatycznie sprawdza zdjęcia na uufinds.com dla danego ID"""
    try:
        # Bot 'wchodzi' na stronę wyszukiwania konkretnego ID
        search_url = f"https://www.uufinds.com/qcfinds?id={product_id}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'
        }
        response = requests.get(search_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Szuka pierwszego zdjęcia QC w galerii na stronie
            img_tag = soup.find('img', {'src': re.compile(r'qc|storage|thumb')})
            if img_tag:
                return img_tag['src']
    except Exception as e:
        print(f"Błąd scrapowania UUFinds: {e}")
    return None

def extract_id(url):
    url = url.lower()
    # Taobao / Tmall
    if "taobao.com" in url or "tmall.com" in url:
        m = re.search(r'id=(\d+)', url)
        if m: return m.group(1), "1", "TB", "TAOBAO", f"https://item.taobao.com/item.htm?id={m.group(1)}"
    # Weidian
    if "weidian.com" in url:
        m = re.search(r'(?:itemid|item_id|itemID=)(\d+)', url)
        if not m: m = re.search(r'itemid=(\d+)', url)
        if m: return m.group(1), "1", "WD", "WEIDIAN", f"https://weidian.com/item.html?itemID={m.group(1)}"
    # 1688
    if "1688.com" in url:
        m = re.search(r'(?:offer/|id=)(\d+)', url)
        if m: return m.group(1), "2", "1688", "ALI_1688", f"https://detail.1688.com/offer/{m.group(1)}.html"
    return None, None, None, None, None

class LinkButtons(View):
    def __init__(self, links_data):
        super().__init__()
        # Ustalone etykiety przycisków
        labels = ["Kakobuy", "USFans", "Mulebuy", "ACBuy", "Raw"]
        for label in labels:
            if label in links_data:
                self.add_item(Button(label=label, url=links_data[label], style=discord.ButtonStyle.link))

@bot.event
async def on_ready():
    print(f'✅ QC Finder Bot gotowy!')

@bot.event
async def on_message(message):
    if message.author.bot or message.channel.id != ALLOWED_CHANNEL_ID:
        return

    targets = ["taobao.com", "weidian.com", "1688.com", "tmall.com"]
    if any(x in message.content.lower() for x in targets):
        match = re.search(r'(https?://\S+)', message.content)
        if match:
            url = match.group(0).rstrip(').,!]')
            product_id, usf_type, ac_type, mule_type, clean_url = extract_id(url)
            
            if product_id:
                encoded_url = urllib.parse.quote(clean_url, safe='')
                uufinds_url = f"https://www.uufinds.com/qcfinds?id={product_id}"
                
                # Przygotowanie słownika linków
                links_dict = {
                    "Kakobuy": f"https://www.kakobuy.com/item/details?url={encoded_url}&affcode={AFFILIATE_CODES['kakobuy']}",
                    "USFans": f"https://www.usfans.com/product/{usf_type}/{product_id}?inviteCode={AFFILIATE_CODES['usfans']}",
                    "Mulebuy": f"https://m.mulebuy.com/pages/product/product?shoptype={mule_type}&id={product_id}&inviteCode={AFFILIATE_CODES['mulebuy']}",
                    "ACBuy": f"https://m.acbuy.com/product?id={product_id}&source={ac_type}&inviteCode={AFFILIATE_CODES['acbuy']}",
                    "Raw": clean_url
                }

                # Automatyczne pobieranie zdjęcia do embeda
                image_preview = get_uufinds_qc(product_id)

                embed = discord.Embed(
                    title="QC FINDER",
                    description=(
                        f"Zdjęcia dla twojego itemu o id: **{product_id}**\n"
                        f"Są w linku poniżej:\n\n"
                        f"🔗 [KLIKNIJ TUTAJ ABY ZOBACZYĆ QC]({uufinds_url})"
                    ),
                    color=0xff0000 
                )
                
                if image_preview:
                    embed.set_image(url=image_preview)
                else:
                    embed.set_footer(text="Brak bezpośredniego podglądu zdjęcia (sprawdź link powyżej)")

                await message.reply(embed=embed, view=LinkButtons(links_dict))

if TOKEN:
    bot.run(TOKEN)
