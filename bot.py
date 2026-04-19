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

def get_product_image(product_id, platform):
    """Pobiera zdjęcie produktu bezpośrednio z serwerów platform (omija uufinds)"""
    if platform == "WEIDIAN":
        return f"https://pic.everguide.info/weidian/item/{product_id}/1.jpg"
    elif platform == "TAOBAO":
        # Taobao często pozwala na taki bezpośredni dostęp
        return f"https://img.alicdn.com/imgextra/i1/{product_id}.jpg"
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

class QCView(View):
    def __init__(self, links_dict, uufinds_url):
        super().__init__(timeout=None)
        # PRZYCISK LOOKUP - row=0 (Góra)
        self.add_item(Button(label="Lookup 🔗", url=uufinds_url, style=discord.ButtonStyle.link, row=0))
        
        # LINKI DO AGENTÓW - row=1 (Dół)
        order = ["Kakobuy", "USFans", "ACBuy", "Mulebuy", "RAW"]
        for label in order:
            if label in links_dict:
                self.add_item(Button(label=label, url=links_dict[label], style=discord.ButtonStyle.link, row=1))

@bot.event
async def on_ready():
    print(f'✅ Bot gotowy. Używam bezpośrednich linków do zdjęć.')

@bot.event
async def on_message(message):
    if message.author.bot or message.channel.id != ALLOWED_CHANNEL_ID:
        return

    match = re.search(r'(https?://\S+)', message.content)
    if match:
        original_url = match.group(0).rstrip(').,!]')
        product_id, usf_type, ac_type, mule_type, platform = extract_id(original_url)
        
        if product_id:
            # Link do zdjęć QC na UUFinds (Lookup)
            uufinds_url = f"https://www.uufinds.com/qcfinds?url={urllib.parse.quote(original_url)}"
            
            # Próbujemy pobrać bezpośrednie zdjęcie produktu
            img_url = get_product_image(product_id, platform)
            
            # Jeśli nie mamy bezpośredniego, dajemy logo (zabezpieczenie)
            final_img = img_url if img_url else "https://www.uufinds.com/favicon.ico"

            embed = discord.Embed(title="Zdjęcia produktu", color=0xff0000)
            embed.set_image(url=final_img)
            
            # Linki afiliacyjne
            encoded_clean = urllib.parse.quote(original_url, safe='')
            links_dict = {
                "Kakobuy": f"https://www.kakobuy.com/item/details?url={encoded_clean}&affcode={AFFILIATE_CODES['kakobuy']}",
                "USFans": f"https://www.usfans.com/product/{usf_type}/{product_id}?inviteCode={AFFILIATE_CODES['usfans']}",
                "ACBuy": f"https://m.acbuy.com/product?id={product_id}&source={ac_type}&inviteCode={AFFILIATE_CODES['acbuy']}",
                "Mulebuy": f"https://m.mulebuy.com/pages/product/product?shoptype={mule_type}&id={product_id}&inviteCode={AFFILIATE_CODES['mulebuy']}",
                "RAW": original_url
            }

            view = QCView(links_dict, uufinds_url)
            
            # Tekst nad embedem
            msg_text = f"**QC znalezione dla linku:**\n{original_url}\n\nKliknij **Lookup**, aby zobaczyć wszystkie zdjęcia."
            
            await message.reply(content=msg_text, embed=embed, view=view)

if TOKEN:
    bot.run(TOKEN)
