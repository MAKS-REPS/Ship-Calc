import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

# Inicjalizacja zmiennych z pliku .env
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = os.getenv('GUILD_ID')

class GłównyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # 🔗 ŁĄCZNIK: Lista modułów do załadowania
        moduly = ['ship', 'kupony']
        
        for modul in moduly:
            try:
                await self.load_extension(modul)
                print(f"✅ Pomyślnie załadowano moduł: {modul}.py")
            except Exception as e:
                print(f"❌ Błąd podczas ładowania modułu {modul}.py: {e}")

        # Synchronizacja komend slash (Globalnie lub dla konkretnego serwera)
        if GUILD_ID:
            guild = discord.Object(id=int(GUILD_ID))
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            print(f"✅ Komendy slash zsynchronizowane dla serwera: {GUILD_ID}")
        else:
            await self.tree.sync()

bot = GłównyBot()

@bot.event
async def on_ready():
    print(f"🚀 Bot działa stabilnie! Zalogowano jako {bot.user}")

if __name__ == "__main__":
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("❌ Brak TOKENU bota! Sprawdź plik .env")
