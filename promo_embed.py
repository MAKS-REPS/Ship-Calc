import discord
from discord.ext import commands, tasks
import asyncio

class PromoEmbedCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.CHANNEL_ID = 1493148055242018886
        self.last_message = None  # Przechowuje ostatnią wiadomość bota
        self.promo_loop.start()

    def cog_unload(self):
        self.promo_loop.cancel()

    @tasks.loop(minutes=5)
    async def promo_loop(self):
        channel = self.bot.get_channel(self.CHANNEL_ID)
        if not channel:
            return

        # 1. Usuwamy poprzednią wiadomość, jeśli istnieje
        if self.last_message:
            try:
                await self.last_message.delete()
            except discord.NotFound:
                pass # Wiadomość już nie istnieje
            except Exception as e:
                print(f"Błąd podczas usuwania starego embedu: {e}")

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

        # 3. Wysyłamy i zapisujemy referencję do nowej wiadomości
        try:
            self.last_message = await channel.send(embed=embed)
        except Exception as e:
            print(f"Błąd podczas wysyłania nowego embedu: {e}")

    @promo_loop.before_loop
    async def before_promo(self):
        await self.bot.wait_until_ready()
        # Opcjonalnie: czyścimy kanał ze starych śmieci przy starcie bota (zakomentuj jeśli nie chcesz)
        # channel = self.bot.get_channel(self.CHANNEL_ID)
        # if channel: await channel.purge(limit=10)

async def setup(bot: commands.Bot):
    await bot.add_cog(PromoEmbedCog(bot))
