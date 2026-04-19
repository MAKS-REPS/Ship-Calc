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

def get_qc_images_from_uufinds(product_id):
    """Pobiera listę wszystkich zdjęć QC ze strony UUFinds"""
    images = []
    try:
        url = f"https://www.uufinds.com/qcfinds?id={product_id}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            img_tags = soup.find_all('img', {'src': re.compile(r'storage|qc')})
            for img in img_tags:
                src = img['src']
                if src.startswith('//'): src = 'https:' + src
                if src not in images:
                    images.append(src)
    except: pass
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
    """Widok z przyciskami Następne/Poprzednie i linkami afiliacyjnymi"""
    def __init__(self, images, links_dict, uufinds_url, current_index=0):
        super().__init__(timeout=None)
        self.images = images
        self.links_dict = links_dict
        self.uufinds_url = uufinds_url
        self.index = current_index

        # Górny rząd: Nawigacja
        prev_btn = Button(label="Poprzednie", style=discord.ButtonStyle.primary, disabled=(self.index == 0))
        prev_btn.callback = self.prev_callback
        self.add_item(prev_btn)

        lookup_btn = Button(label="Lookup 🔗", url=self.uufinds_url, style=discord.ButtonStyle.link)
        self.add_item(lookup_btn)

        next_btn = Button(label="Następne", style=discord.ButtonStyle.primary, disabled=(self.index == len(self.images) - 1))
        next_btn.callback = self.next_callback
        self.add_item(next_btn)

        # Dolny rząd: Linki (zgodnie z prośbą)
        # Kakobuy, USFans, ACBuy, Mulebuy, RAW
        order = ["Kakobuy", "USFans", "ACBuy", "Mulebuy", "RAW"]
        for label in order:
            if label in self.links_dict:
                self.add_item(Button(label=label, url=self.links_dict[label], style=discord.ButtonStyle.link))

    async def update_view(self, interaction):
        embed = interaction.message.embeds[0]
        embed.set_image(url=self.images[self.index])
        embed.set_footer(text=f"{self.index + 1}/{len(self.images)}")
        
        # Tworzymy nowy widok, żeby odświeżyć stan przycisków (disabled)
        new_view = QCView(self.images, self.links_dict, self.uufinds_url, self.index)
        await interaction.response.edit_message(embed=embed, view=new_view)

    async def prev_callback(self, interaction):
        self.index -= 1
        await self.update_view(interaction)

    async def next_callback(self, interaction):
        self.index += 1
        await self.update_view(interaction)

@bot.event
async def on_ready():
    print(f'✅ Bot QC Ready! Tryb: Galeria + Pagination')

@bot.event
async def on_message(message):
    if message.author.bot or message.channel.id != ALLOWED_CHANNEL_ID:
        return

    match = re.search(r'(https?://\S+)', message.content)
    if match:
        original_url = match.group(0).rstrip(').,!]')
        product_id, usf_type, ac_type, mule_type, clean_url = extract_id(original_url)
        
        if product_id:
            # 1. Przygotuj link do galerii UUFinds
            uufinds_url = f"https://www.uufinds.com/qcfinds?url={urllib.parse.quote(original_url)}"
            
            # 2. Pobierz wszystkie zdjęcia
            images = get_qc_images_from_uufinds(product_id)
            if not images:
                await message.reply("❌ Nie znaleziono zdjęć QC dla tego linku.")
                return

            # 3. Przygotuj linki afiliacyjne
            encoded_clean = urllib.parse.quote(clean_url, safe='')
            links_dict = {
                "Kakobuy": f"https://www.kakobuy.com/item/details?url={encoded_clean}&affcode={AFFILIATE_CODES['kakobuy']}",
                "USFans": f"https://www.usfans.com/product/{usf_type}/{product_id}?inviteCode={AFFILIATE_CODES['usfans']}",
                "ACBuy": f"https://m.acbuy.com/product?id={product_id}&source={ac_type}&inviteCode={AFFILIATE_CODES['acbuy']}",
                "Mulebuy": f"https://m.mulebuy.com/pages/product/product?shoptype={mule_type}&id={product_id}&inviteCode={AFFILIATE_CODES['mulebuy']}",
                "RAW": clean_url
            }

            # 4. Wyślij embeda z pierwszym zdjęciem i nawigacją
            embed = discord.Embed(title="Zdjęcia produktu", color=0x2f3136)
            embed.set_image(url=images[0])
            embed.set_footer(text=f"1/{len(images)}")
            
            view = QCView(images, links_dict, uufinds_url)
            await message.reply(embed=embed, view=view)

if TOKEN:
    bot.run(TOKEN)
