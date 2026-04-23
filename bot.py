import discord
from discord import app_commands
from discord.ext import commands
import os
import re
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = os.getenv('GUILD_ID')

class RepsMasterBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True 
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        guild = discord.Object(id=int(GUILD_ID))
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)

bot = RepsMasterBot()

# --- LOGIKA QC & LINKÓW ---
def extract_product_url(text):
    # Szuka linków Weidian, Taobao, 1688, Tmall
    pattern = r'(https?://(?:item\.taobao\.com|weidian\.com|detail\.1688\.com)[^\s]+)'
    match = re.search(pattern, text)
    return match.group(0) if match else None

# --- LOGIKA KALKULATORA ---
def calculate_shipping(agent, weight, insurance):
    rates = {
        "Kakobuy": {"base": 68, "per_g": 0.054, "discount": 0.85},
        "USFans": {"base": 75, "per_g": 0.059, "discount": 0.88}
    }
    r = rates[agent]
    base_price = r["base"] + (weight * r["per_g"])
    ins_cost = round(base_price * 0.04, 2) if insurance == "Tak" else 0
    total = base_price + ins_cost
    return round(total, 2), round(total * r["discount"], 2), ins_cost

# --- KOMENDA OBLICZ ---
@bot.tree.command(name="oblicz", description="Kalkulator shipu + QC")
@app_commands.describe(agent="Wybierz agenta", waga="Waga w gramach", link="Opcjonalnie: Link do przedmiotu (Weidian/Taobao)")
@app_commands.choices(agent=[
    app_commands.Choice(name="Kakobuy", value="Kakobuy"),
    app_commands.Choice(name="USFans", value="USFans"),
])
async def oblicz(interaction: discord.Interaction, agent: str, waga: int, link: str = None):
    await interaction.response.defer()
    
    total, discounted, ins_price = calculate_shipping(agent, waga, "Nie")
    
    embed = discord.Embed(title=f"📦 Wyceń przesyłkę: {agent}", color=0x00ff00)
    embed.add_field(name="⚖️ Waga", value=f"{waga}g", inline=True)
    embed.add_field(name="💰 Cena szacowana", value=f"~~{total} PLN~~\n**{discounted} PLN** (z kuponem)", inline=False)
    
    view = discord.ui.View()
    
    # Jeśli użytkownik podał link, dodajemy przycisk QC
    if link:
        clean_url = extract_product_url(link)
        if clean_url:
            # Link do UUFinds (najlepsza baza QC)
            qc_url = f"https://www.uufinds.com/qc?url={clean_url}"
            view.add_item(discord.ui.Button(label="🔍 Zobacz zdjęcia QC", url=qc_url, style=discord.ButtonStyle.link))
            # Przycisk zakupu u agenta
            buy_url = f"https://www.{agent.lower()}.com/index/item/index?url={clean_url}"
            view.add_item(discord.ui.Button(label=f"🛒 Kup na {agent}", url=buy_url, style=discord.ButtonStyle.link))

    await interaction.followup.send(embed=embed, view=view)

@bot.event
async def on_ready():
    print(f"✅ Bot {bot.user} gotowy!")

bot.run(TOKEN)
