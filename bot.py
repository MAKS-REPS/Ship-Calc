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

def get_uufinds_preview_image(product_id):
    """Próbuje pobrać zdjęcie podglądowe do embeda"""
    try:
        search_url = f"https://www.uufinds.com/qcfinds?id={product_id}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(search_url, headers=headers, timeout=5)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            img_tag = soup.find('img', {'src': re.compile(r'qc|storage')})
            if img_tag:
                return img_tag['src']
    except:
        pass
    return None

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
    def __init__(self, links_data):
        super().__init__()
        # Kolejność: Kakobuy, USFans, Mulebuy, ACBuy, Raw
        order = ["Kakobuy", "USFans", "Mulebuy", "ACBuy", "Raw"]
        for label in order:
            if label in links_data:
                self.add_item(Button(label=label, url=links_data[label], style=discord.ButtonStyle.link))

@bot.event
async def on_ready():
    print(f'✅ Bot gotowy | Kanał: {ALLOWED_CHANNEL_ID}')

@bot.event
async def on_message(message):
    if message.author.bot or message.channel.id != ALLOWED_CHANNEL_ID:
        return

    # Szukanie linku w wiadomości
    match = re.search(r'(https?://\S+)', message.content)
    if match:
        original_url = match.group(0).rstrip(').,!]')
        product_id, usf_type, ac_type, mule_type, clean_url = extract_id(original_url)
        
        if product_id:
            # Zakoduj oryginalny link, żeby bezpiecznie wstawić go w URL uufinds
            encoded_original_link = urllib.parse.quote(original_url, safe='')
            
            # AUTOMATYCZNY LINK DO QC NA UUFINDS (Wkleja Twój link w ich wyszukiwarkę)
            uufinds_qc_link = f"https://www.uufinds.com/qcfinds?url={encoded_original_link}"
            
            # Linki do przycisków
            encoded_clean = urllib.parse.quote(clean_url, safe='')
            links_dict = {
                "Kakobuy": f"https://www.kakobuy.com/item/details?url={encoded_clean}&affcode={AFFILIATE_CODES['kakobuy']}",
                "USFans": f"https://www.usfans.com/product/{usf_type}/{product_id}?inviteCode={AFFILIATE_CODES['usfans']}",
                "Mulebuy": f"https://m.mulebuy.com/pages/product/product?shoptype={mule_type}&id={product_id}&inviteCode={AFFILIATE_CODES['mulebuy']}",
                "ACBuy": f"https://m.acbuy.com/product?id={product_id}&source={ac_type}&inviteCode={AFFILIATE_CODES['acbuy']}",
                "Raw": clean_url
            }

            # Pobieranie miniatury zdjęcia
            preview_img = get_uufinds_preview_image(product_id)

            embed = discord.Embed(
                title="QC FINDER",
                description=(
                    f"Zdjęcia dla twojego itemu o id: **{product_id}**\n"
                    f"Są w linku poniżej:\n\n"
                    f"🔗 [KLIKNIJ TUTAJ ABY ZOBACZYĆ QC]({uufinds_qc_link})"
                ),
                color=0xff0000
            )
            
            if preview_img:
                embed.set_image(url=preview_img)
            
            embed.set_footer(text=f"Wysłane przez {message.author.display_name}")

            await message.reply(embed=embed, view=LinkButtons(links_dict))

if TOKEN:
    bot.run(TOKEN)
