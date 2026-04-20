import discord
from discord import app_commands
import requests
from bs4 import BeautifulSoup
import os

# --- KONFIGURACJA ---
TOKEN = os.getenv('DISCORD_TOKEN')
ALLOWED_CHANNEL_ID = 1495575003004010636

class TrackingBot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()
        print(f"Bot zalogowany i gotowy!")

client = TrackingBot()

def scrape_fujexp_direct(tracking_number):
    """Próbuje wyciągnąć dane bezpośrednio z tabeli na stronie IP"""
    url = f"http://106.55.5.75:8082/trackIndex.htm?trackNumber={tracking_number}"
    
    # Udajemy najnowszą przeglądarkę Chrome, żeby serwer nas nie odrzucił
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Referer': 'http://106.55.5.75:8082/'
    }
    
    try:
        # Chińskie serwery są wolne, dajemy mu 20 sekund na odpowiedź
        response = requests.get(url, headers=headers, timeout=20)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Szukamy wszystkich wierszy (tr) i komórek (td)
            rows = soup.find_all('tr')
            updates = []
            
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 2:
                    time = cols[0].get_text(strip=True)
                    desc = cols[1].get_text(strip=True)
                    
                    # Sprawdzamy czy to nie są nagłówki tabeli
                    if "Time" not in time and "Status" not in desc:
                        if time and desc:
                            updates.append(f"📅 **{time}**\n📝 {desc}")
            
            return updates
    except Exception as e:
        print(f"Błąd podczas wyciągania danych: {e}")
    return None

@client.tree.command(name="track", description="Wyciągnij dane bezpośrednio z serwera Fujexp")
async def track(interaction: discord.Interaction, numer: str):
    if interaction.channel_id != ALLOWED_CHANNEL_ID:
        await interaction.response.send_message("❌ Zły kanał!", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)
    
    updates = scrape_fujexp_direct(numer)
    
    if not updates:
        await interaction.followup.send(
            "❌ Nie udało się wyciągnąć danych. Możliwe przyczyny:\n"
            "1. Numer jest jeszcze nieaktywny.\n"
            "2. Chiński serwer zablokował połączenie z Railway.\n"
            "3. Strona zmieniła wygląd.", 
            ephemeral=True
        )
        return

    # Embed podsumowujący
    embed = discord.Embed(title=f"📦 Śledzenie: {numer}", color=0x00ff00)
    embed.add_field(name="Ostatnia aktualizacja", value=updates[0], inline=False)
    await interaction.followup.send(embed=embed, ephemeral=True)

    # Pełna lista na DM
    history = discord.Embed(title="🛤️ Pełna historia", description="\n\n".join(updates[:15]))
    try:
        await interaction.user.send(embed=history)
    except:
        pass

client.run(TOKEN)
