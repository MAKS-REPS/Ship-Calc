import discord
from discord.ext import commands, tasks
from discord import app_commands

# ==================== KONFIGURACJA MODUŁU ====================
CHANNEL_ID = 1457763945631715456  # Tutaj wpisz ID kanału, na który bot ma sam wysyłać wiadomości co godzinę
# =============================================================

class Kupony(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Uruchomienie automatycznej pętli czasowej przy starcie modułu
        self.wysylaj_ogloszenie.start()

    def cog_unload(self):
        # Bezpieczne zatrzymanie pętli przy przeładowaniu modułu
        self.wysylaj_ogloszenie.cancel()

    # Funkcja generująca identyczny wygląd embedu dla pętli i komendy
    def stworz_kupony_embed(self):
        embed = discord.Embed(
            title="📢 ODBIERZ DARMOWE KUPONY NA PIERWSZĄ PACZKĘ",
            description=(
                "<:KAKOBUY_LOGO:1465816795356336421> Jeśli nie masz jeszcze konta na kakobuy to [kliknji tu](https://ikako.vip/r/maksr3ps) "
                "i odbierz darmowe kupony na start.\n\n"
                "<a:Moneywithwings:12251546027777837740> dodatkowo wpisując kod **Maks.R3ps** otrzymasz darmowe 15$ na wysyłkę.\n\n"
                "🏷️ Po wpisaniu kodu **Maks20** dostaje sie kupon na -20%!"
            ),
            color=discord.Color.from_str("#2f3136")
        )
        return embed

    # PĘTLA CZASOWA: wysyła embed automatycznie (domyślnie co 1 godzinę)
    @tasks.loop(hours=1.0)  
    async def wysylaj_ogloszenie(self):
        channel = self.bot.get_channel(CHANNEL_ID)
        if channel:
            embed = self.stworz_kupony_embed()
            await channel.send(embed=embed)
        else:
            print("⚠️ [Kupony] Nie odnaleziono kanału o podanym ID. Sprawdź konfigurację w kupony.py")

    @wysylaj_ogloszenie.before_loop
    async def przed_petla(self):
        # Czekamy, aż bot w pełni połączy się z Discordem przed uruchomieniem wysyłania
        await self.bot.wait_until_ready()

    # KOMENDA SLASH: /kupony
    @app_commands.command(name="kupony", description="Wyświetla informacje o darmowych kuponach i kodach rabatowych")
    async def kupony(self, interaction: discord.Interaction):
        embed = self.stworz_kupony_embed()
        await interaction.response.send_message(embed=embed)


# Rejestracja Coga w głównym bocie
async def setup(bot):
    await bot.add_cog(Kupony(bot))
