import discord
from discord import app_commands
import requests
from bs4 import BeautifulSoup
import os

# --- KONFIGURACJA ---
TOKEN = os.getenv('DISCORD_TOKEN')
ALLOWED_CHANNEL_ID = 1495575003004010636  # ID Twojego kanału

class TrackingBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()
        print(f"Bot zalogowany jako {self.user} i gotowy do pracy!")

client = TrackingBot()

def scrape_fujexp(tracking_number):
    """Pobiera dane bezpośrednio z chińskiego portalu bez API"""
    url = f"http://106.55.5.75:8082/trackIndex.htm?trackNumber={tracking_number}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Szukamy wierszy w tabeli (Struktura oparta na Twoim screenie)
            rows = soup.find_all('tr') 
            
            updates = []
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 2:
                    time = cols[0].text.strip()
                    status = cols[1].text.strip()
                    if time and status: # Pomijamy puste wiersze
                        updates.append(f"📅 **{time}**\n📝 {status}")
            return updates
    except Exception as e:
        print(f"Błąd scrapingu: {e}")
    return None

@client.tree.command(name="track", description="Śledź paczkę (tylko na wybranym kanale)")
@app_commands.describe(numer="Wprowadź numer śledzenia")
async def track(interaction: discord.Interaction, numer: str):
    # SPRAWDZENIE KANAŁU
    if interaction.channel_id != ALLOWED_CHANNEL_ID:
        await interaction.response.send_message(
            f"❌ Ta komenda może być używana tylko na kanale <#{ALLOWED_CHANNEL_ID}>!", 
            ephemeral=True
        )
        return

    # Informujemy o pracy (ephemeral - tylko dla użytkownika)
    await interaction.response.defer(ephemeral=True)
    
    updates = scrape_fujexp(numer)
    
    if not updates:
        await interaction.followup.send("❌ Nie znaleziono danych dla tego numeru lub błąd serwera.", ephemeral=True)
        return

    # 1. Embed podsumowujący (Widoczny tylko dla Ciebie na kanale)
    summary_embed = discord.Embed(title="📦 Status Przesyłki", color=0x2b2d31)
    summary_embed.add_field(name="Numer", value=f"`{numer}`", inline=True)
    summary_embed.add_field(name="Ostatni Status", value=updates[0], inline=False)
    summary_embed.set_footer(text="Pełna historia została wysłana na Twoje DM.")
    
    await interaction.followup.send(embed=summary_embed, ephemeral=True)

    # 2. Pełna historia na DM
    history_embed = discord.Embed(
        title=f"🛤️ Pełna Historia: {numer}",
        description="Oto wszystkie etapy Twojej paczki:",
        color=0x5865f2
    )
    
    full_history = "\n\n".join(updates[:20]) # Limit 20 statusów
    history_embed.description = full_history

    try:
        await interaction.user.send(embed=history_embed)
    except discord.Forbidden:
        await interaction.followup.send("⚠️ Masz zablokowane wiadomości prywatne (DM)!", ephemeral=True)

client.run(TOKEN)
