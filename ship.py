import discord
from discord import app_commands
from discord.ext import commands

# --- LOGIKA CENOWA (ZWRACA WARTOŚCI W PLN) ---
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


# --- WIDOK Z MENU ROZWIJANYM DLA KOMENDY /SHIP ---
class KalkulatorWysylkiView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.select(
        placeholder="Wybierz agenta...",
        options=[
            discord.SelectOption(
                label="Usfans", 
                value="USFans", 
                description="Kalkulator dla agenta Usfans",
                emoji=discord.PartialEmoji.from_str("<:Usfans1:1505533510990172262>")
            ),
            discord.SelectOption(
                label="Kakobuy", 
                value="Kakobuy", 
                description="Kalkulator dla agenta Kakobuy",
                emoji=discord.PartialEmoji.from_str("<:kakobuy1:1505517561846960138>")
            )
        ]
    )
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        wybrany_agent = select.values[0]
        
        # Otwieranie odpowiedniego formularza po wyborze z menu
        if wybrany_agent == "USFans":
            await interaction.response.send_modal(UsfansModal())
        elif wybrany_agent == "Kakobuy":
            await interaction.response.send_modal(KakobuyModal())


# ==================== MODAL DLA USFANS ====================
class UsfansModal(discord.ui.Modal, title="Kalkulator Wysyłki - Usfans"):
    waga = discord.ui.TextInput(label="Waga paczki (w gramach, np. 3500)", placeholder="Wpisz wagę...", required=True)
    ubezpieczenie = discord.ui.TextInput(label="Ubezpieczenie? (Wpisz: Tak lub Nie)", placeholder="Tak / Nie", default="Tak", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            waga_g = float(self.waga.value)
            ub_choice = "Tak" if self.ubezpieczenie.value.strip().lower() in ["tak", "t", "yes"] else "Nie"
            
            total, kupon, koszt_ub = przelicz_koszt("USFans", waga_g, ub_choice)

            embed = discord.Embed(
                title="<:Usfans1:1505533510990172262> Wycena wysyłki - USFans",
                color=discord.Color.blue()
            )
            embed.add_field(name="⚖️ Waga paczki", value=f"**{waga_g / 1000:.2f} kg** ({int(waga_g)} g)", inline=True)
            ub_text = f"Tak (+{koszt_ub} PLN)" if ub_choice == "Tak" else "Nie"
            embed.add_field(name="🛡️ Ubezpieczenie", value=ub_text, inline=True)
            embed.add_field(
                name="✈️ Linia: DHL Tariffless / DPD", 
                value=f"Cena baza: ~~{total} PLN~~\nCena z kuponem: **{kupon} PLN**", 
                inline=False
            )
            embed.add_field(name="Zastosowano kupon", value="🏷️ **DJPZ6T** (-40%)", inline=False)
            embed.set_footer(text="Cena ma charakter orientacyjny.")

            await interaction.response.send_message(embed=embed, ephemeral=True)
        except ValueError:
            await interaction.response.send_message("❌ Podano nieprawidłową wagę! Używaj tylko cyfr.", ephemeral=True)


# ==================== MODAL DLA KAKOBUY ====================
class KakobuyModal(discord.ui.Modal, title="Kalkulator Wysyłki - Kakobuy"):
    waga = discord.ui.TextInput(label="Waga paczki (w gramach, np. 3500)", placeholder="Wpisz wagę...", required=True)
    ubezpieczenie = discord.ui.TextInput(label="Ubezpieczenie? (Wpisz: Tak lub Nie)", placeholder="Tak / Nie", default="Tak", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            waga_g = float(self.waga.value)
            ub_choice = "Tak" if self.ubezpieczenie.value.strip().lower() in ["tak", "t", "yes"] else "Nie"
            
            total, kupon, koszt_ub = przelicz_koszt("Kakobuy", waga_g, ub_choice)

            embed = discord.Embed(
                title="<:kakobuy1:1505517561846960138> Wycena wysyłki - Kakobuy",
                color=discord.Color.red()
            )
            embed.add_field(name="⚖️ Waga paczki", value=f"**{waga_g / 1000:.2f} kg** ({int(waga_g)} g)", inline=True)
            ub_text = f"Tak (+{koszt_ub} PLN)" if ub_choice == "Tak" else "Nie"
            embed.add_field(name="🛡️ Ubezpieczenie", value=ub_text, inline=True)
            embed.add_field(
                name="✈️ Linia: DHL Tariffless / DPD", 
                value=f"Cena baza: ~~{total} PLN~~\nCena z kuponem: **{kupon} PLN**", 
                inline=False
            )
            embed.add_field(name="Zastosowano kupon", value="🏷️ **Maks20** (-20%)", inline=False)
            embed.set_footer(text="Cena ma charakter orientacyjny.")

            await interaction.response.send_message(embed=embed, ephemeral=True)
        except ValueError:
            await interaction.response.send_message("❌ Podano nieprawidłową wagę! Używaj tylko cyfr.", ephemeral=True)


# --- KLASA COG (KOMENDY BOTA) ---
class ShipCalc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Komenda interaktywna (Wybór z menu)
    @app_commands.command(name="ship", description="Otwiera kalkulator wyceny wysyłki paczek")
    async def ship(self, interaction: discord.Interaction):
        view = KalkulatorWysylkiView()
        embed = discord.Embed(
            title="📦 Kalkulator Kosztów Wysyłki",
            description="Wybierz agenta z poniższego menu, aby obliczyć szacowany koszt dostawy swojej paczki do Polski.",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, view=view)

    # Bezpośrednia komenda slash /oblicz (Wpisywanie od razu w okienkach Discorda)
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

        # Dopasowanie ikon i kolorów pod wybranego agenta
        if agent == "Kakobuy":
            embed_color = discord.Color.red()
            agent_emoji = "<:kakobuy1:1505517561846960138>"
            kod_text = "**Maks20** (-20%)"
        else:
            embed_color = discord.Color.blue()
            agent_emoji = "<:Usfans1:1505533510990172262>"
            kod_text = "**DJPZ6T** (-40%)"

        embed = discord.Embed(
            title=f"{agent_emoji} Kalkulacja Wysyłki: {agent}",
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
        
        embed.add_field(name="Zastosowano kupon", value=f"🏷️ {kod_text}", inline=False)
        
        znizka_procent = "40%" if agent == "USFans" else "20%"
        embed.set_footer(text=f"Zastosowano kupon zniżkowy: -{znizka_procent}")
        
        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(ShipCalc(bot))
