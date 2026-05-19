import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

# Importujemy widoki z pliku private_chat, aby zarejestrować je jako Persistent Views
try:
    from private_chat import ChatCreateView, ChatCloseView, TicketAddonsView
except ImportError:
    ChatCreateView, ChatCloseView, TicketAddonsView = None, None, None

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = os.getenv('GUILD_ID')

class GłównyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # 🔗 Rejestracja Persistent Views (Przycisków), aby działały po restarcie bota
        if ChatCreateView and ChatCloseView and TicketAddonsView:
            self.add_view(ChatCreateView())
            self.add_view(ChatCloseView())
            self.add_view(TicketAddonsView())
            print("🧠 Pomyślnie zarejestrowano trwałe widoki systemu AI.")

        # 🚀 Lista modułów poszerzona o private_chat oraz link_converter
        moduly = ['ship', 'kupony', 'dm', 'ogloszenia', 'ankiety', 'private_chat', 'link_converter']
        
        for modul in moduly:
            try:
                await self.load_extension(modul)
                print(f"✅ Pomyślnie załadowano moduł: {modul}.py")
            except Exception as e:
                print(f"❌ Błąd podczas ładowania modułu {modul}.py: {e}")

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
