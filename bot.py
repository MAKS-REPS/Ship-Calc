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
ALLOWED_CHANNEL_ID = 1457766095531278529  # Twój nowy kanał

AFFILIATE_CODES = {
    "usfans": "DJPZ6T",
    "acbuy": "KV2WLD",
    "kakobuy": "maksr3ps"
}

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

def get_uufinds_qc(product_id):
    """Pobiera zdjęcie QC z UUFinds."""
    try:
        search_url = f"https://www.uufinds.com/qcfinds?id={product_id}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(search_url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Szukanie obrazka w galerii QC
            img_tag = soup.find('img', {'src': re.compile(r'qc|storage')})
            if img_tag:
                return img_tag['src']
    except Exception as e:
        print(f"Błąd pobierania zdjęcia: {e}")
    return None

def extract_id(url):
    url = url.lower()
    # Taobao / Tmall
    if "taobao.com" in url or "tmall.com" in url:
        m = re.search(r'id=(\d+)', url)
        if m: return m.group(1), "1", "TB", f"https://item.taobao.com/item.htm?id={m.group(1)}"
    # Weidian
    if "weidian.com" in url:
        m = re.search(r'(?:itemid|item_id|itemID=)(\d+)', url)
        if not m: m = re.search(r'itemid=(\d+)', url)
        if m: return m.group(1), "1", "WD", f"https://weidian.com/item.html?itemID={m.group(1)}"
    # 1688
    if "1688.com" in url:
        m = re.search(r'(?:offer/|id=)(\d+)', url)
        if m: return m.group(1), "2", "1688", f"https://detail.1688.com/offer/{m.group(1)}.html"
    return None, None, None, None

class LinkButtons(View):
    """Tworzy rządek przycisków pod wiadomością."""
    def __init__(self, links):
        super().__init__()
        for label, url in links.items():
            self.add_item(Button(label=label, url=url, style=discord.ButtonStyle.link))

@bot.event
async def on_ready():
    print(f'✅ Bot aktywny!')
    print(f'📺 Kanał: {ALLOWED_CHANNEL_ID}')
    print(f'🔴 Kolor: Czerwony')

@bot.event
async def on_message(message):
    if message.author.bot: return
    if message.channel.id != ALLOWED_CHANNEL_ID: return

    # Wykrywanie linków
    targets = ["taobao.com", "weidian.com", "1688.com", "tmall.com"]
    if any(x in message.content.lower() for x in targets):
        match = re.search(r'(https?://\S+)', message.content)
        if match:
            url = match.group(0).rstrip(').,!]')
            product_id, usf_type, ac_type, clean_url = extract_id(url)
            
            if product_id:
                encoded_url = urllib.parse.quote(clean_url, safe='')
                
                # Przygotowanie linków dla przycisków
                links = {
                    "USFans": f"https://www.usfans.com/product/{usf_type}/{product_id}?inviteCode={AFFILIATE_CODES['usfans']}",
                    "Kakobuy": f"https://www.kakobuy.com/item/details?url={encoded_url}&affcode={AFFILIATE_CODES['kakobuy']}",
                    "ACBuy": f"https://m.acbuy.com/product?id={product_id}&source={ac_type}&inviteCode={AFFILIATE_CODES['acbuy']}",
                    "MuleBuy": f"https://mulebuy.com/product/?shop_type={ac_type.lower()}&id={product_id}",
                    "Weidian Raw": clean_url
                }

                # Próba pobrania zdjęcia QC
                qc_image = get_uufinds_qc(product_id)

                embed = discord.Embed(
                    title="Kakobuy QC Set (QC Finder)",
                    description=f"Pobrano zdjęcia dla produktu ID: **{product_id}**\n\n[Zobacz wszystkie zdjęcia na UUFinds](https://www.uufinds.com/qcfinds?id={product_id})",
                    color=0xff0000  # Czysty czerwony
                )
                
                if qc_image:
                    embed.set_image(url=qc_image)
                
                embed.set_footer(text=f"Wygenerowano dla {message.author.display_name}", icon_url=message.author.display_avatar.url)

                await message.reply(embed=embed, view=LinkButtons(links))

if TOKEN:
    bot.run(TOKEN)
