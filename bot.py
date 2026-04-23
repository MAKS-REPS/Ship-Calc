import discord
from discord import app_commands
from discord.ext import commands
import os
from dotenv import load_dotenv

# Wczytywanie zmiennych (dla lokalnego testowania, Railway użyje własnych Variables)
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = os.getenv('GUILD_ID')

class RepsBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Synchronizacja komend na Twoim serwerze
        if GUILD_ID:
            guild = discord.Object(id=int(GUILD_ID))
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            print(f"✅ Zsynchronizowano komendy dla serwera: {GUILD_ID}")
        else:
            await self.tree.sync()
            print("✅ Zsynchronizowano komendy globalnie")

bot = RepsBot()

# --- KALKULATOR LOGIKA ---
def oblicz_logistyke(platforma, waga, ubezpieczenie):
    # Stawki (Możesz tu edytować ceny za gram pod aktualne kursy)
    stawki = {
        "Kakobuy": {"baza": 65, "gram": 0.052, "znizka": 0.85},
        "USFans": {"baza": 72, "gram": 0.058, "znizka": 0.88}
    }
    
    s = stawki[platforma]
    cena_podstawowa = s["baza"] + (waga * s["gram"])
    
    koszt_ub = 0
    if ubezpieczenie == "Tak":
        koszt_ub = round(cena_podstawowa * 0.045, 2) # ok. 4.5% ubezpieczenia
        
    suma_total = cena_podstawowa + koszt_ub
    suma_kupon = suma_total * s["znizka"]
    
    return round(suma_total, 2), round(suma_kupon, 2), koszt_ub

@bot.tree.command(name="oblicz", description="Oblicz wagę i koszt wysyłki (Kakobuy/USFans)")
@app_commands.describe(
    platforma="Wybierz agenta",
    waga="Waga w gramach (np. 3500)",
    pudelka="Czy zachować pudełka?",
    ubezpieczenie="Czy ubezpieczyć paczkę?"
)
@app_commands.choices(platforma=[
    app_commands.Choice(name="Kakobuy", value="Kakobuy"),
    app_commands.Choice(name="USFans", value="USFans"),
])
@app_commands.choices(pudelka=[
    app_commands.Choice(name="Tak (Standardowe)", value="Tak"),
    app_commands.Choice(name="Nie (Lekka paczka)", value="Nie"),
])
@app_commands.choices(ubezpieczenie=[
    app_commands.Choice(name="Tak (Zalecane)", value="Tak"),
    app_commands.Choice(name="Nie", value="Nie"),
])
async def oblicz(interaction: discord.Interaction, platforma: str, waga: int, pudelka: str, ubezpieczenie: str):
    
    total, kupon, koszt_ub = oblicz_logistyke(platforma, waga, ubezpieczenie)
    
    # Budowanie estetycznego embeda
    embed = discord.Embed(color=0x2ecc71, description="")
    embed.set_author(name=f"Inteligentny Kalkulator Wysyłki {platforma}", icon_url=bot.user.display_avatar.url)
    
    embed.add_field(name="⚖️ Waga", value=f"**{waga} g**", inline=False)
    embed.add_field(name="📦 Pudełka", value=pudelka, inline=False)
    
    ubezpieczenie_str = f"Tak (+{koszt_ub} PLN)" if ubezpieczenie == "Tak" else "Nie"
    embed.add_field(name="🛡️ Ubezpieczenie", value=ubezpieczenie_str, inline=False)
    
    # Linie kurierskie
    dhl_baza = total
    dhl_kupon = kupon
    
    embed.add_field(name="**DHL**", value=f"Baza: {dhl_baza} PLN\nZ kuponem {platforma}: **{dhl_kupon} PLN**", inline=False)
    embed.add_field(name="**DPD**", value=f"Baza: {round(dhl_baza*0.92, 2)} PLN\nZ kuponem {platforma}: **{round(dhl_kupon*0.92, 2)} PLN**", inline=False)
    
    embed.set_footer(text="Ceny mogą się różnić zależnie od wymiarów paczki.")
    
    await interaction.response.send_message(embed=embed)

@bot.event
async def on_ready():
    print(f"🚀 Bot online jako {bot.user}")

bot.run(TOKEN)
