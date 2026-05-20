import discord
from discord.ext import commands, tasks
import asyncio

class PromoEmbedCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.CHANNEL_ID = 1493148055242018886
        self.promo_loop.start()

    def cog_unload(self):
        self.promo_loop.cancel()

    @tasks.loop(minutes=1) # Tutaj możesz zmienić na 10, jeśli wolisz
    async def promo_loop(self):
        channel = self.bot.get_channel(self.CHANNEL_ID)
        if not channel:
            return

        # 1. Usuwamy WSZYSTKIE poprzednie wiadomości bota na tym kanale
        # Dzięki temu bot nigdy się nie pogubi, nawet po restarcie
        async for message in channel.history(limit=20):
            if message.author == self.bot.user:
                try:
                    await message.delete()
                except:
                    pass

        # 2. Tworzymy nowy embed
        embed = discord.Embed(
            title="KAKOBUY x MaksReps",
            description="Najszybszy i najlepszy agent\n\n"
                        "<a:animatedwhitearrow:1505987572499746836> Najlepszy support\n"
                        "<a:animatedwhitearrow:1505987572499746836> Szybki i bezpieczny\n\n"
                        "💰 KUPONY\n"
                        "Kod `Maks.R3ps` — 15$ USD zniżki na shipa i kupony\n\n"
                        "» **ZAREJESTRUJ SIĘ**\n"
                        "[Kliknij tutaj](https://ikako.vip/r/maksr3ps)",
            color=0xFFFFFF
        )
        embed.set_footer(text="Wysłane przez: Maks Reps System • Made By Maks.R3ps")

        # 3. Wysyłamy nową wiadomość
        await channel.send(embed=embed)

    @promo_loop.before_loop
    async def before_promo(self):
        await self.bot.wait_until_ready()

async def setup(bot: commands.Bot):
    await bot.add_cog(PromoEmbedCog(bot))
