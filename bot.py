import discord
from discord import app_commands
from discord.ext import commands
import os
from dotenv import load_dotenv

# Inicjalizacja zmiennych
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = os.getenv('GUILD_ID')

class ShipCalcBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Synchronizacja komend slash
        if GUILD_ID:
            guild = discord.Object(id=int(GUILD_ID))
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
        else:
            await self.tree.sync()

bot = ShipCalcBot()

# --- DANE DO OBLICZEŃ ---
# Możesz tutaj zmieniać stawki w dowolnym momencie
def przelicz_koszt(platforma, waga_g, ubezpieczenie):
    # Stawki przykładowe (PLN)
    # baza = stała opłata za paczkę
    # co_100g = koszt za każde rozpoczęte 100g
    # kupon = % ceny (0.85 to zniżka 15%)
    stawki = {
        "Kakobuy": {"baza": 65.0, "co_100g": 5.4, "kupon": 0.85},
        "USFans": {"baza": 70.0, "co_100g": 5.9, "kupon": 0.88}
    }
    
    s = stawki[platforma]
    waga_kg = waga_g / 100
    cena_podstawowa = s["baza"] + (waga_kg * s["co_100g"])
    
    koszt_ub = 0.0
    if ubezpieczenie == "Tak":
        koszt_ub = round(cena_podstawowa * 0.04, 2) # 4% ubezpieczenia
        
    suma = cena_podstawowa + koszt_ub
    suma_kupon = suma * s["kupon"]
    
    return round(suma, 2), round(suma_kupon, 2), koszt_ub

# --- KOMENDA OBLICZ ---
@bot.tree.command(name="oblicz", description="Kalkulator kosztów wysyłki USFans / Kakobuy")
@app_commands.describe(
    agent="Wybierz platformę (USFans lub Kakobuy)",
    waga="Wpisz wagę paczki w gramach (np. 5500)",
    pudelka="Czy zachować oryginalne pudełka butów?",
    ubezpieczenie="Czy dodać ubezpieczenie paczki?"
)
@app_commands.choices(agent=[
    app_commands.Choice(name="Kakobuy", value="Kakobuy"),
    app_commands.Choice(name="USFans", value="USFans"),
])
@app_commands.choices(pudelka=[
    app_commands.Choice(name="Tak (Standard)", value="Tak"),
    app_commands.Choice(name="Nie (Usuń pudełka - lżejsza paczka)", value="Nie"),
])
@app_commands.choices(ubezpieczenie=[
    app_commands.Choice(name="Tak (Zalecane)", value="Tak"),
    app_commands.Choice(name="Nie", value="Nie"),
])
async def oblicz(interaction: discord.Interaction, agent: str, waga: int, pudelka: str, ubezpieczenie: str):
    await interaction.response.defer() # Zapobiega błędom ładowania

    total, kupon, koszt_ub = przelicz_koszt(agent, waga, ubezpieczenie)

    # Tworzenie Embed
    embed = discord.Embed(
        title=f"🚢 Kalkulator Przesyłki: {agent}",
        color=0x2ecc71 if agent == "Kakobuy" else 0x3498db
    )
    
    embed.add_field(name="⚖️ Waga", value=f"**{waga} g**", inline=True)
    embed.add_field(name="📦 Pudełka", value=pudelka, inline=True)
    
    ub_text = f"Tak (+{koszt_ub} PLN)" if ubezpieczenie == "Tak" else "Nie"
    embed.add_field(name="🛡️ Ubezpieczenie", value=ub_text, inline=True)
    
    # DHL Tariffless (Najpopularniejsza linia)
    embed.add_field(
        name="✈️ DHL Tariffless / DPD", 
        value=f"Cena bazowa: ~~{total} PLN~~\nCena z kuponem: **{kupon} PLN**", 
        inline=False
    )
    
    embed.set_footer(text="Cena szacunkowa. Pamiętaj o doliczeniu kosztu wolumetrycznego.")
    
    await interaction.followup.send(embed=embed)

@bot.event
async def on_ready():
    print(f"✅ Kalkulator gotowy! Zalogowano jako {bot.user}")

if __name__ == "__main__":
    bot.run(TOKEN)
