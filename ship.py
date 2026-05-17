import discord
from discord import app_commands
from discord.ext import commands

# --- LOGIKA CENOWA W PLN (ZBUDOWANA NA SCREENACH) ---
def przelicz_koszt(platforma, waga_g, ubezpieczenie):
    if waga_g < 500:
        waga_g = 500
        
    if platforma == "USFans":
        # Pierwsze 500g = 71.35 PLN. Każde kolejne 500g = 25.94 PLN
        cena_baza_bez_kuponu = 71.35
        if waga_g > 500:
            dodatkowa_waga = waga_g - 500
            cena_baza_bez_kuponu += dodatkowa_waga * (25.94 / 500)
        kupon_mnoznik = 0.60  # Kupon -40% (Kod: DJPZ6T)
        
    else:  # Kakobuy
        # Pierwsze 500g = 70.41 PLN. Każde kolejne 500g = 32.14 PLN
        cena_baza_bez_kuponu = 70.41
        if waga_g > 500:
            dodatkowa_waga = waga_g - 500
            cena_baza_bez_kuponu += dodatkowa_waga * (32.14 / 500)
        kupon_mnoznik = 0.80  # Kupon -20% (Kod: Maks20)
        
    koszt_ub = 0.0
    if ubezpieczenie == "Tak":
        koszt_ub = round(cena_baza_bez_kuponu * 0.04, 2)
        
    suma_brutto = cena_baza_bez_kuponu + koszt_ub
    suma_z_kuponem = suma_brutto * kupon_mnoznik
    
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
        
        if wybrany_agent == "USFans":
            await interaction.response.send_modal(UsfansModal())
        elif wybrany_agent == "Kakobuy":
            await interaction.response.send_modal(KakobuyModal())


# ==================== MODAL DLA USFANS ====================
class UsfansModal(discord.ui.Modal, title="Kalkulator Wysyłki - Usfans"):
    waga = discord.ui.TextInput(label="Waga paczki (w gramach, np. 10000)", placeholder="Wpisz wagę...", required=True)
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
                name="✈️ Linia: DHL Line in Poland (Tax-free)", 
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
    waga = discord.ui.TextInput(label="Waga paczki (w gramach, np. 10000)", placeholder="Wpisz wagę...", required=True)
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
                name="✈️ Linia: Europe DHL Line (Express Line)", 
                value=f"Cena baza: ~~{total} PLN~~\nCena z kuponem: **{kupon} PLN**", 
                inline=False
            )
            embed.add_field(name="Zastosowano kupon", value="🏷️ **Maks20** (-20%)", inline=False)
            embed.set_footer(text="Cena ma charakter orientacyjny.")

            await interaction.response.send_message(embed=embed, ephemeral=True)
        except ValueError:
            await interaction.response.send_message("❌ Podano nieprawidłową wagę! Używaj tylko cyfr.", ephemeral=True)


# --- KLASA COG (KOMENDA BOTA) ---
class ShipCalc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ship", description="Otwiera kalkulator wyceny wysyłki paczek")
    async def ship(self, interaction: discord.Interaction):
        view = KalkulatorWysylkiView()
        embed = discord.Embed(
            title="📦 Kalkulator Kosztów Wysyłki",
            description="Wybierz agenta z poniższego menu, aby obliczyć szacowany koszt dostawy swojej paczki do Polski.",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(ShipCalc(bot))
