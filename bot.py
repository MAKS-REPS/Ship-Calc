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

def get_kakobuy_qc_images(product_id):
    """Pobiera zdjęcia bezpośrednio z zasobów Kakobuy"""
    images = []
    try:
        # Kakobuy często trzyma zdjęcia pod tym adresem dla Weidiana/Taobao
        api_url = f"https://www.kakobuy.com/api/item/qc-photos?id={product_id}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        # Próbujemy pobrać dane z ich wewnętrznego systemu
        r = requests.get(api_url, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            # Zakładając, że Kakobuy zwraca listę w formacie JSON
            if 'data' in data and 'list' in data['data']:
                for item in data['data']['list']:
                    images.append(item['url'])
                    
        # Jeśli API nie zadziała, szukamy na ich stronie podglądu przez regex
        if not images:
            web_url = f"https://www.kakobuy.com/item/details?id={product_id}"
            r = requests.get(web_url, headers=headers, timeout=10)
            raw_links = re.findall(r'https?://[^\s"\'<>]+(?:qc|storage)[^\s"\'<>]+(?:\.jpg|\.png)', r.text, re.IGNORECASE)
            images = list(set(raw_links))
            
    except:
        pass
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
        # Przycisk Lookup na samej górze
        self.add_item(Button(label="Lookup 🔗", url=uufinds_url, style=discord.ButtonStyle.link, row=0))
        
        # Linki sklepów pod spodem
        order = ["Kakobuy", "USFans", "ACBuy", "Mulebuy", "RAW"]
        for label in order:
            if label in links_dict:
                self.add_item(Button(label=label, url=links_dict[label], style=discord.ButtonStyle.link, row=1))

@bot.event
async def on_ready():
    print(f'✅ Bot QC (Kakobuy Mode) gotowy!')

@bot.event
async def on_message(message):
    if message.author.bot or message.channel.id != ALLOWED_CHANNEL_ID:
        return

    match = re.search(r'(https?://\S+)', message.content)
    if match:
        original_url = match.group(0).rstrip(').,!]')
        product_id, usf_type, ac_type, mule_type, clean_url = extract_id(original_url)
        
        if product_id:
            # Link do galerii (zawsze przydatny)
            uufinds_url = f"https://www.uufinds.com/qcfinds?url={urllib.parse.quote(original_url)}"
            
            # POBIERANIE ZDJĘĆ Z KAKOBUY
            images = get_kakobuy_qc_images(product_id)
            
            embed = discord.Embed(title="Zdjęcia produktu", color=0x2b2d31)
            
            if images:
                embed.set_image(url=images[0])
                msg_content = f"**Znaleziono {len(images)} zdjęć QC w bazie Kakobuy.**"
            else:
                # Jeśli Kakobuy nie ma zdjęć, bot nie wyświetli pustej ramki
                embed.set_image(url="https://www.uufinds.com/favicon.ico")
                msg_content = "❌ Brak zdjęć w szybkim podglądzie. Sprawdź pełną galerię klikając **Lookup**."

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
