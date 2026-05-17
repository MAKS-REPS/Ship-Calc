import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime

# ==================== KONFIGURACJA MODUŁU ====================
CHANNEL_ID = 123456789012345678  # Tutaj wpisz ID swojego kanału tekstowego
# =============================================================

class Kupony(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.wysylaj_ogloszenie.start()

    def cog_unload(self):
        self.wysylaj_ogloszenie.cancel()

    def stworz_kupony_embed(self):
        embed = discord.Embed(
            title="📢 ODBIERZ DARMOWE KUPONY NA PIERWSZĄ PACZKĘ",
            description=(
                "<:KAKOBUY_LOGO:1505517561846960138> Jeśli nie masz jeszcze konta na kakobuy to [kliknji tu](https://ikako.vip/r/maksr3ps) "
                "i odbierz darmowe kupony na start.\n\n"
                "<a:Moneywithwings:12251546027777837740> dodatkowo wpisując kod **Maks.R3ps** otrzymasz darmowe 15$ na wysyłkę.\n\n"
                "🏷️ Po wpisaniu kodu **Maks20** dostaje sie kupon na -20%!"
            ),
            color=discord.Color.from_str("#2f3136")
        )
        return embed

    # PĘTLA CZASOWA: uruchamia się co godzinę
    @tasks.loop(hours=1.0)  
    async def wysylaj_ogloszenie(self):
        # Sprawdzanie aktualnej godziny systemowej maszyny/hostingu
        aktualna_godzina = datetime.now().hour
        
        # Warunek: wysyłaj tylko w przedziale od 8 do 22 (włącznie)
        if 8 <= aktualna_godzina <= 22:
            channel = self.bot.get_channel(CHANNEL_ID)
            if channel:
                embed = self.stworz_kupony_embed()
                await channel.send(embed=embed)
            else:
                print("⚠️ [Kupony] Nie odnaleziono kanału o podanym ID. Sprawdź konfigurację w kupony.py")
        else:
            # Informacja w konsoli bota, że post został pominięty ze względu na ciszę nocną
            print(f"⏰ Pominięto automatyczne wysyłanie ogłoszenia (aktualna godzina: {aktualna_godzina}:00, poza przedziałem 8-22).")

    @wysylaj_ogloszenie.before_loop
    async def przed_petla(self):
        await self.bot.wait_until_ready()

    # KOMENDA SLASH: /kupony (działa zawsze, niezależnie od godziny)
    @app_commands.command(name="kupony", description="Wyświetla informacje o darmowych kuponach i kodach rabatowych")
    async def kupony(self, interaction: discord.Interaction):
        embed = self.stworz_kupony_embed()
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Kupony(bot))
