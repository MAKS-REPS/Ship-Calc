import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime

# ==================== KONFIGURACJA MODUŁU ====================
CHANNEL_ID = 1457763945631715456  # ID Twojego czatu
# =============================================================

class Kupony(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ostatnia_wiadomosc_id = None  # Tu bot będzie pamiętał ID starego embeda
        self.wysylaj_ogloszenie.start()

    def cog_unload(self):
        self.wysylaj_ogloszenie.cancel()

    def stworz_kupony_embed(self):
        # Twoje własne emoji z serwera:
        kakobuy_logo = "<:emoji_9:1505530744674717819>"
        animowana_kasa = "<a:money:1505529682559238184>"
        
        embed = discord.Embed(
            title="📢 ODBIERZ DARMOWE KUPONY NA PIERWSZĄ PACZKĘ",
            description=(
                f"{kakobuy_logo} Jeśli nie masz jeszcze konta na kakobuy to [kliknji tu](https://ikako.vip/r/maksr3ps) "
                "i odbierz darmowe kupony na start.\n\n"
                f"{animowana_kasa} dodatkowo wpisując kod **Maks.R3ps** otrzymasz darmowe 15$ na wysyłkę.\n\n"
                "🏷️ Po wpisaniu kodu **Maks20** dostaje sie kupon na -20%!"
            ),
            color=discord.Color.from_str("#2f3136")
        )
        return embed

    @tasks.loop(hours=1.0)  
    async def wysylaj_ogloszenie(self):
        aktualna_godzina = datetime.now().hour
        
        # Wysyłanie automatyczne tylko w godzinach 8:00 - 22:00
        if 8 <= aktualna_godzina <= 22:
            channel = self.bot.get_channel(CHANNEL_ID)
            if channel:
                # --- USUWANIE STAREJ WIADOMOŚCI ---
                if self.ostatnia_wiadomosc_id:
                    try:
                        stara_wiadomosc = await channel.fetch_message(self.ostatnia_wiadomosc_id)
                        await stara_wiadomosc.delete()
                        print("🗑️ Pomyślnie usunięto poprzednie ogłoszenie.")
                    except discord.NotFound:
                        # Stara wiadomość mogła zostać już usunięta przez kogoś ręcznie
                        print("ℹ️ Poprzednie ogłoszenie nie zostało znalezione (prawdopodobnie już usunięte).")
                    except Exception as e:
                        print(f"⚠️ Nie udało się usunąć starej wiadomości: {e}")

                # --- WYSYŁANIE NOWEJ WIADOMOŚCI ---
                embed = self.stworz_kupony_embed()
                nowa_wiadomosc = await channel.send(embed=embed)
                
                # Zapisujemy ID nowo wysłanej wiadomości, aby usunąć ją za godzinę
                self.ostatnia_wiadomosc_id = nowa_wiadomosc.id
            else:
                print("⚠️ [Kupony] Nie odnaleziono kanału o podanym ID.")
        else:
            print(f"⏰ Pominięto automatyczne wysyłanie ogłoszenia (godzina {aktualna_godzina}:00).")

    @wysylaj_ogloszenie.before_loop
    async def przed_petla(self):
        await self.bot.wait_until_ready()

    @app_commands.command(name="kupony", description="Wyświetla informacje o darmowych kuponach i kodach rabatowych")
    async def kupony(self, interaction: discord.Interaction):
        embed = self.stworz_kupony_embed()
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Kupony(bot))
