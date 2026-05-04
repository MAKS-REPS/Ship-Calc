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
        # Synchronizacja komend slash dla Twojego serwera
        if GUILD_ID:
            guild = discord.Object(id=int(GUILD_ID))
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            print(f"✅ Komendy zsynchronizowane dla serwera: {GUILD_ID}")
        else:
            await self.tree.sync()

bot = ShipCalcBot()

# --- POPRAWIONA LOGIKA CENOWA ---
def przelicz_koszt(platforma, waga_g, ubezpieczenie):
    """
    USFans: 10kg (10000g) = 500 PLN baza -> 300 PLN po kuponie -40%
    Stawka: 0.05 PLN za gram
    """
    stawki = {
        "Kakobuy": {
            "baza": 60.0, 
            "gram": 0.054, 
            "kupon": 0.80  # -20%
        },
        "USFans": {
            "baza": 0.0,    
            "gram": 0.05,   # 10000g * 0.05 = 500 PLN
            "kupon": 0.60   # ZMIENIONO z 0.70 na 0.60 (-40%)
        }
    }
    
    s = stawki[platforma]
    
    # Cena na podstawie wagi
    cena_podstawowa = s["baza"] + (waga_g * s["gram"])
    
    # Obliczanie ubezpieczenia (opcjonalne 4% od ceny bazowej)
    koszt_ub = 0.0
    if ubezpieczenie == "Tak":
        koszt_ub = round(cena_podstawowa * 0.04, 2)
        
    suma_brutto = cena_podstawowa + koszt_ub
    suma_z_kuponem = suma_brutto * s["kupon"]
    
    return round(suma_brutto, 2), round(suma_z_kuponem, 2), koszt_ub

# --- KOMENDA SLASH ---
@bot.tree.command(name="oblicz", description="Szacunkowy koszt wysyłki USFans / Kakobuy")
@app_commands.describe(
    agent="Wybierz platformę (USFans lub Kakobuy)",
    waga="Waga paczki w gramach (np. 10000 dla 10kg)",
    pudelka="Czy zachować oryginalne pudełka?",
    ubezpieczenie="Czy ubezpieczyć paczkę?"
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
    # Zapobiega błędom "Application did not respond"
    await interaction.response.defer()

    total, kupon, koszt_ub = przelicz_koszt(agent, waga, ubezpieczenie)

    # Wybór koloru (Zielony dla Kakobuy, Niebieski dla USFans)
    embed_color = 0x2ecc71 if agent == "Kakobuy" else 0x3498db
    
    embed = discord.Embed(
        title=f"🚢 Kalkulacja Wysyłki: {agent}",
        color=embed_color
    )
    
    embed.add_field(name="⚖️ Waga", value=f"**{waga} g**", inline=True)
    embed.add_field(name="📦 Pudełka", value=pudelka, inline=True)
    
    ub_text = f"Tak (+{koszt_ub} PLN)" if ubezpieczenie == "Tak" else "Nie"
    embed.add_field(name="🛡️ Ubezpieczenie", value=ub_text, inline=True)
    
    # DHL/DPD Section
    embed.add_field(
        name="✈️ Linia: DHL Tariffless / DPD", 
        value=f"Cena bazowa: ~~{total} PLN~~\nCena z kuponem: **{kupon} PLN**", 
        inline=False
    )
    
    # Dynamiczny stopka zależnie od agenta
    znizka_procent = "40%" if agent == "USFans" else "20%" # ZMIENIONO z 30% na 40%
    embed.set_footer(text=f"Zastosowano kupon zniżkowy: -{znizka_procent}")
    
    await interaction.followup.send(embed=embed)

@bot.event
async def on_ready():
    print(f"✅ Kalkulator gotowy! Zalogowano jako {bot.user}")

if __name__ == "__main__":
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("❌ Brak TOKENU bota! Sprawdź zmienne na Railway.")
