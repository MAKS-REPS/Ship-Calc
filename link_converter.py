import discord
from discord.ext import commands
import re
from urllib.parse import urlparse, parse_qs, unquote

class LinkConverterCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Twoje kody afiliacyjne
        self.AFF_KAKOBUY = "maksr3ps"
        self.AFF_USFANS = "DJPZ6T"

    def extract_product_info(self, url: str):
        """
        Analizuje link i wyciąga ID produktu oraz typ platformy (weidian, 1688, taobao, kakobuy itp.)
        """
        url_lower = url.lower()
        product_id = None
        platform_type = None

        # 1. Jeśli to jest zagnieżdżony link w Kakobuy, najpierw go dekodujemy
        if "kakobuy.com" in url_lower and "url=" in url_lower:
            parsed = urlparse(url)
            query_params = parse_qs(parsed.query)
            nested_url = query_params.get('url', [None])[0]
            if nested_url:
                return self.extract_product_info(unquote(nested_url))

        # 2. Obsługa WEIDIAN
        if "weidian.com" in url_lower:
            platform_type = "Weidian"
            parsed = urlparse(url)
            query_params = parse_qs(parsed.query)
            if 'itemid' in query_params:
                product_id = query_params['itemid'][0]
            elif 'id' in query_params:
                product_id = query_params['id'][0]
            else:
                match = re.search(r'(?:itemid|id)=(\d+)', url, re.IGNORECASE)
                if match:
                    product_id = match.group(1)

        # 3. Obsługa 1688
        elif "1688.com" in url_lower:
            platform_type = "1688"
            match = re.search(r'offer/(\d+)\.html', url, re.IGNORECASE)
            if match:
                product_id = match.group(1)
            else:
                parsed = urlparse(url)
                query_params = parse_qs(parsed.query)
                if 'id' in query_params:
                    product_id = query_params['id'][0]

        # 4. Obsługa TAOBAO
        elif "taobao.com" in url_lower:
            platform_type = "Taobao"
            parsed = urlparse(url)
            query_params = parse_qs(parsed.query)
            if 'id' in query_params:
                product_id = query_params['id'][0]
            else:
                match = re.search(r'id=(\d+)', url, re.IGNORECASE)
                if match:
                    product_id = match.group(1)

        # 5. Obsługa czystego KAKOBUY
        elif "kakobuy.com" in url_lower:
            platform_type = "Kakobuy"
            parsed = urlparse(url)
            query_params = parse_qs(parsed.query)
            if 'id' in query_params:
                product_id = query_params['id'][0]
            else:
                match = re.search(r'(?:id|itemid)=(\d+)', url, re.IGNORECASE)
                if match:
                    product_id = match.group(1)

        return platform_type, product_id

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        url_match = re.search(r'(https?://[^\s]+)', message.content)
        if not url_match:
            return

        raw_url = url_match.group(1)
        platform, product_id = self.extract_product_info(raw_url)

        if not platform or not product_id:
            return

        # Słownik dopasowujący odpowiednie emoji do platformy źródłowej
        emoji_dict = {
            "Weidian": "<:weidian:1496931587047030825>",
            "Taobao": "<:taobao:1496931560371388466>",
            "1688": "<:1688:1496931547541012601>"
        }

        # Dynamiczne budowanie linków źródłowych oraz przypisywanie nazw/emoji
        if platform == "1688":
            clean_source_url = f"https://detail.1688.com/offer/{product_id}.html"
            source_display_name = "1688"
            source_emoji = emoji_dict["1688"]
        elif platform == "Taobao":
            clean_source_url = f"https://item.taobao.com/item.htm?id={product_id}"
            source_display_name = "Taobao"
            source_emoji = emoji_dict["Taobao"]
        else:
            # Dla Weidian lub domyślnego Kakobuy (traktowanego jako Weidian w strukturze agenta)
            clean_source_url = f"https://weidian.com/item.html?itemID={product_id}"
            source_display_name = "Weidian"
            source_emoji = emoji_dict["Weidian"]

        # Generowanie linków afiliacyjnych
        kakobuy_aff_url = f"https://www.kakobuy.com/item/details?url={clean_source_url}&affcode={self.AFF_KAKOBUY}"
        usfans_aff_url = f"https://www.usfans.com/item/details?url={clean_source_url}&affcode={self.AFF_USFANS}"

        # Tworzenie Embedu
        embed = discord.Embed(
            description=f"🔗 **Link przekonwertowany — {source_display_name}**\n\n"
                        f"**ID produktu:** `{product_id}`\n"
                        f"**Czysty link:** [kliknij tutaj]({clean_source_url})",
            color=0x2b2d31
        )

        # Budowanie widoku z przyciskami (URL Buttons) i Twoimi customowymi emoji
        view = discord.ui.View()
        
        view.add_item(discord.ui.Button(
            label="KakoBuy", 
            url=kakobuy_aff_url, 
            style=discord.ButtonStyle.link, 
            emoji="<:kakobuy1:1505517561846960138>"
        ))
        view.add_item(discord.ui.Button(
            label="Usfans", 
            url=usfans_aff_url, 
            style=discord.ButtonStyle.link, 
            emoji="<:Usfans1:1505533510990172262>"
        ))
        view.add_item(discord.ui.Button(
            label=source_display_name, 
            url=clean_source_url, 
            style=discord.ButtonStyle.link, 
            emoji=source_emoji
        ))

        await message.reply(embed=embed, view=view)

async def setup(bot: commands.Bot):
    await bot.add_cog(LinkConverterCog(bot))
