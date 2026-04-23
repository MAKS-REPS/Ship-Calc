import discord
from discord import app_commands
from discord.ext import commands
import os
from dotenv import load_dotenv

# Ładowanie zmiennych (Railway sam je podstawi)
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = os.getenv('GUILD_ID')

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        if GUILD_ID:
            guild = discord.Object(id=int(GUILD_ID))
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            print(f"✅ Komendy slash zsynchronizowane dla serwera: {GUILD_ID}")
        else:
            await self.tree.sync()
            print("✅ Komendy slash zsynchronizowane globalnie")

bot = MyBot()

# --- LOGIKA OBLICZEŃ ---
def przelicz_ceny(platforma, waga, ubezpieczenie):
    # Przykładowe stawki (Baza + cena za 100g). Edytuj te wartości wg kalkulatorów USFans/Kakobuy.
    stawki = {
        "Kakobuy": {"start": 72.0, "per_100g": 5.8, "kupon_mnoznik": 0.90},
        "USFans": {"start": 78.0, "per_100g": 6.2, "kupon_mnoznik": 0.88}
    }
    
    p = stawki[platforma]
    cena_bazowa = p["start"] + ((waga / 100) * p["per_100g"])
    
    # Dodatek za ubezpieczenie (np. 4%)
    koszt_ub = round(cena_bazowa * 0.04, 2) if ubezpieczenie == "Tak" else 0.0
    
    total = cena_bazowa + koszt_ub
    total_z_kuponem = total * p["kupon_mnoznik"]
    
    return round(total, 2), round(total_z_kuponem, 2), koszt_ub

# --- KOMENDA SLASH ---
@bot.tree.command(name="oblicz", description="Kalkulator wysyłki Kakobuy/USFans + QC")
@app_commands.describe(
    platforma="Wybierz agenta",
    waga="Waga w gramach (np. 4500)",
    ubezpieczenie="Czy dodać ubezpieczenie paczki?",
    link="Opcjonalnie: Link do produktu (Weidian/Taobao/1688)"
)
@app_commands.choices(platforma=[
    app_commands.Choice(name="Kakobuy", value="Kakobuy"),
    app_commands.Choice(name="USFans", value="USFans"),
])
@app_commands.choices(ubezpieczenie=[
    app_commands.Choice(name="Tak (Zalecane)", value="Tak"),
    app_commands.Choice(name="Nie", value="Nie"),
])
async def oblicz(interaction: discord.Interaction, platforma: str, waga: int, ubezpieczenie: str, link: str = None):
    # Zapobiega błędom "Aplikacja nie reaguje"
    await interaction.response.defer()

    cena_b, cena_k, koszt_ub = przelicz_ceny(platforma, waga, ubezpieczenie)

    # Budowanie Embed (wygląd jak na zdjęciu)
    embed = discord.Embed(
        title=f"📦 Kalkulacja dla {platforma}",
        color=0x2ecc71 if platforma == "Kakobuy" else 0x3498db,
        description=f"Szacunkowy koszt wysyłki dla paczki **{waga}g**."
    )
    
    embed.add_field(name="⚖️ Waga", value=f"{waga} g", inline=True)
    embed.add_field(name="🛡️ Ubezpieczenie", value=f"{ubezpieczenie} (+{koszt_ub} PLN)" if ubezpieczenie == "Tak" else "Brak", inline=True)
    
    # Przykładowy kurier DHL
    embed.add_field(
        name="🚀 DHL (Tax-Free)", 
        value=f"Cena standardowa: ~~{cena_b} PLN~~\nCena z kuponem: **{cena_k} PLN**", 
        inline=False
    )

    # Przycisk View (Przycisk do QC i Zakupu)
    view = discord.ui.View()
    if link:
        # Link do QC przez UUFinds (automatyczny)
        qc_url = f"https://www.uufinds.com/qc?url={link}"
        # Link do zakupu przez wybranego agenta
        agent_url = f"https://www.{platforma.lower()}.com/index/item/index?url={link}"
        
        view.add_item(discord.ui.Button(label="🔍 Zobacz QC", url=qc_url, style=discord.ButtonStyle.link))
        view.add_item(discord.ui.Button(label=f"🛒 Kup na {platforma}", url=agent_url, style=discord.ButtonStyle.link))

    await interaction.followup.send(embed=embed, view=view)

@bot.event
async def on_ready():
    print(f"🚀 Bot zalogowany jako {bot.user}")

# Uruchomienie bota
if __name__ == "__main__":
    if not TOKEN:
        print("❌ BŁĄD: Brak tokena DISCORD_TOKEN w zmiennych środowiskowych!")
    else:
        bot.run(TOKEN)
