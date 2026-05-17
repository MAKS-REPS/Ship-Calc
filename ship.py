import discord
from discord import app_commands
from discord.ext import commands

# --- POPRAWIONA LOGIKA CENOWA ---
def przelicz_koszt(platforma, waga_g, ubezpieczenie):
    stawki = {
        "Kakobuy": {
            "baza": 60.0, 
            "gram": 0.054, 
            "kupon": 0.80  # -20%
        },
        "USFans": {
            "baza": 0.0,    
            "gram": 0.05,   
            "kupon": 0.60   # -40%
        }
    }
    
    s = stawki[platforma]
    cena_podstawowa = s["baza"] + (waga_g * s["gram"])
    
    koszt_ub = 0.0
    if ubezpieczenie == "Tak":
        koszt_ub = round(cena_podstawowa * 0.04, 2)
        
    suma_brutto = cena_podstawowa + koszt_ub
    suma_z_kuponem = suma_brutto * s["kupon"]
    
    return round(suma_brutto, 2), round(suma_z_kuponem, 2), koszt_ub


# --- KLASA COG (MODUŁ KALKULATORA) ---
class ShipCalc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Wewnątrz Cog zamiast @bot.tree.command używamy @app_commands.command()
    # Pierwszym argumentem funkcji w klasie musi być zawsze 'self'
    @app_commands.command(name="oblicz", description="Szacunkowy koszt wysyłki USFans / Kakobuy")
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
    async def oblicz(self, interaction: discord.Interaction, agent: str, waga: int, pudelka: str, ubezpieczenie: str):
        await interaction.response.defer()

        total, kupon, koszt_ub = przelicz_koszt(agent, waga, ubezpieczenie)

        embed_color = 0x2ecc71 if agent == "Kakobuy" else 0x3498db
        
        embed = discord.Embed(
            title=f"🚢 Kalkulacja Wysyłki: {agent}",
            color=embed_color
        )
        
        embed.add_field(name="⚖️ Waga", value=f"**{waga} g**", inline=True)
        embed.add_field(name="📦 Pudełka", value=pudelka, inline=True)
        
        ub_text = f"Tak (+{koszt_ub} PLN)" if ubezpieczenie == "Tak" else "Nie"
        embed.add_field(name="🛡️ Ubezpieczenie", value=ub_text, inline=True)
        
        embed.add_field(
            name="✈️ Linia: DHL Tariffless / DPD", 
            value=f"Cena baza: ~~{total} PLN~~\nCena z kuponem: **{kupon} PLN**", 
            inline=False
        )
        
        znizka_procent = "40%" if agent == "USFans" else "20%"
        embed.set_footer(text=f"Zastosowano kupon zniżkowy: -{znizka_procent}")
        
        await interaction.followup.send(embed=embed)


# Specjalna funkcja setup, której discord.py wymaga do załadowania pliku jako rozszerzenia
async def setup(bot):
    await bot.add_cog(ShipCalc(bot))
