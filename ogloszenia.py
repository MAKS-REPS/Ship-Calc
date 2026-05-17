import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from typing import Optional, List

# ==================== KONFIGURACJA UPRAWNIEŃ ====================
OWNER_ROLE_ID = 1457769309735485450  # ID Twojej roli Owner
# ================================================================

# --- STRONICOWANY WIDOK Z PRZYCISKAMI LEWO/PRAWO ---
class PaginacjaRaportuView(discord.ui.View):
    def __init__(self, wpisy_raportu: List[str], tytul_ogloszenia: str):
        super().__init__(timeout=300) # Widok wygaśnie po 5 minutach bezczynności
        self.wpisy_raportu = wpisy_raportu
        self.tytul_ogloszenia = tytul_ogloszenia
        
        self.wpisy_na_strone = 15
        self.aktualna_strona = 0
        
        # Obliczanie całkowitej liczby stron
        self.maks_stron = (len(wpisy_raportu) - 1) // self.wpisy_na_strone + 1
        
        # Aktualizacja stanu przycisków na starcie
        self.odswiez_przyciski()

    def pobierz_embed_strony(self) -> discord.Embed:
        """Generuje embed dla bieżącej strony raportu."""
        start_index = self.aktualna_strona * self.wpisy_na_strone
        end_index = start_index + self.wpisy_na_strone
        wpisy_na_stronie = self.wpisy_raportu[start_index:end_index]
        
        tekst_strony = "```diff\n" + "\n".join(wpisy_na_stronie) + "\n```"
        
        embed = discord.Embed(
            title=f"📋 Szczegółowa lista odbiorców",
            description=f"Dotyczy ogłoszenia: **{self.tytul_ogloszenia}**\n\n{tekst_strony}",
            color=discord.Color.from_str("#2f3136")
        )
        embed.set_footer(text=f"Strona {self.aktualna_strona + 1} z {self.maks_stron}")
        return embed

    def odswiez_przyciski(self):
        """Włącza/wyłącza przyciski w zależności od numeru strony."""
        # Przycisk "W lewo" wyłączony na pierwszej stronie
        self.poprzednia_strona.disabled = self.aktualna_strona == 0
        # Przycisk "W prawo" wyłączony na ostatniej stronie
        self.nastepna_strona.disabled = self.aktualna_strona == self.maks_stron - 1

    @discord.ui.button(label="Poprzednia", style=discord.ButtonStyle.primary, emoji="⬅️", custom_id="prev_page")
    async def poprzednia_strona(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.aktualna_strona > 0:
            self.aktualna_strona -= 1
            self.odswiez_przyciski()
            await interaction.response.edit_message(embed=self.pobierz_embed_strony(), view=self)

    @discord.ui.button(label="Następna", style=discord.ButtonStyle.primary, emoji="➡️", custom_id="next_page")
    async def nastepna_strona(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.aktualna_strona < self.maks_stron - 1:
            self.aktualna_strona += 1
            self.odswiez_przyciski()
            await interaction.response.edit_message(embed=self.pobierz_embed_strony(), view=self)


# --- PRZYCISK STARTOWY (POJAWIAJĄCY SIĘ POD PODSUMOWANIEM) ---
class RaportOdbiorcowView(discord.ui.View):
    def __init__(self, wpisy_raportu: List[str], tytul_ogloszenia: str):
        super().__init__(timeout=None)
        self.wpisy_raportu = wpisy_raportu
        self.tytul_ogloszenia = tytul_ogloszenia

    @discord.ui.button(label="Pokaż listę odbiorców", style=discord.ButtonStyle.secondary, emoji="📄")
    async def pokaz_odbiorcow(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.wpisy_raportu:
            await interaction.response.send_message("📋 Brak danych o odbiorcach.", ephemeral=True)
            return

        # Tworzymy system stron i wysyłamy pierwszą stronę
        paginacja = PaginacjaRaportuView(self.wpisy_raportu, self.tytul_ogloszenia)
        await interaction.response.send_message(embed=paginacja.pobierz_embed_strony(), view=paginacja, ephemeral=True)


# --- GŁÓWNA KLASA MODUŁU ---
class Ogloszenia(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ogloszenie", description="Wysyła masową wiadomość DM do określonej liczby członków serwera")
    @app_commands.describe(
        tytul="Tytuł Twojego ogłoszenia (pogrubiony nagłówek)",
        tresc="Treść ogłoszenia (użyj \n aby zrobić nową linię)",
        kolor="Kolor paska bocznego (Wybierz z listy)",
        limit_osob="Do ilu osób maksymalnie wysłać to ogłoszenie?",
        obraz="Opcjonalnie: Przeciągnij tutaj zdjęcie, które ma znaleźć się w ogłoszeniu"
    )
    @app_commands.choices(kolor=[
        app_commands.Choice(name="Niebieski (Neutralny)", value="blue"),
        app_commands.Choice(name="Czerwony (Ważne/Promocja)", value="red"),
        app_commands.Choice(name="Zielony (Sukces/Nowość)", value="green"),
        app_commands.Choice(name="Złoty/Żółty (Premium)", value="gold")
    ])
    @app_commands.choices(limit_osob=[
        app_commands.Choice(name="5 osób", value=5),
        app_commands.Choice(name="10 osób", value=10),
        app_commands.Choice(name="50 osób", value=50),
        app_commands.Choice(name="100 osób", value=100),
        app_commands.Choice(name="Wszyscy użytkownicy", value=-1)
    ])
    async def ogloszenie(
        self, 
        interaction: discord.Interaction, 
        tytul: str, 
        tresc: str, 
        kolor: str,
        limit_osob: int,
        obraz: Optional[discord.Attachment] = None
    ):
        if not interaction.guild:
            await interaction.response.send_message("❌ Tej komendy można użyć tylko na serwerze!", ephemeral=True)
            return
            
        ranga_owner = interaction.user.get_role(OWNER_ROLE_ID)
        if not ranga_owner:
            await interaction.response.send_message("❌ Nie masz uprawnień! Tylko osoba z rangą <@&1457769309735485450> może tego użyć.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        guild = interaction.guild

        kolory_map = {
            "blue": discord.Color.blue(),
            "red": discord.Color.red(),
            "green": discord.Color.green(),
            "gold": discord.Color.gold()
        }
        wybrany_kolor = kolory_map.get(kolor, discord.Color.default())

        embed = discord.Embed(
            title=f"📢 {tytul}",
            description=tresc.replace("\\n", "\n"),
            color=wybrany_kolor
        )
        embed.set_footer(text=f"Ogłoszenie z serwera: {guild.name} • Maks Reps 2.0")
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        if obraz:
            if obraz.content_type and obraz.content_type.startswith("image/"):
                embed.set_image(url=obraz.url)
            else:
                await interaction.followup.send("⚠️ Przesłany plik nie jest prawidłowym obrazem! Ogłoszenie zostało zatrzymane.", ephemeral=True)
                return

        czlonkowie = guild.members
        sukcesy = 0
        bledy = 0
        wyslane_do_liczba = 0

        wpisy_raportu = []

        print(f"🔮 Rozpoczynam wysyłanie ogłoszenia. Limit ustawiony na: {limit_osob if limit_osob != -1 else 'Wszyscy'}")

        for member in czlonkowie:
            if member.bot:
                continue

            if limit_osob != -1 and wyslane_do_liczba >= limit_osob:
                break

            wyslane_do_liczba += 1

            try:
                await member.send(embed=embed)
                sukcesy += 1
                wpisy_raportu.append(f"+ [DOSTARCZONO]  {member.name}")
                await asyncio.sleep(2.5)
            except discord.Forbidden:
                bledy += 1
                wpisy_raportu.append(f"- [BLOKADA DM]   {member.name}")
            except Exception as e:
                bledy += 1
                wpisy_raportu.append(f"- [BŁĄD SYSTEMU] {member.name}")

        raport_embed = discord.Embed(
            title="✅ Wysyłanie ogłoszenia zakończone!",
            description=(
                f"📊 **Podsumowanie wysyłki:**\n"
                f"📈 Stan realizacji dla wybranych odbiorców:\n\n"
                f"🟢 Wysłano pomyślnie: **{sukcesy}** osób\n"
                f"🔴 Nie dostarczono: **{bledy}** osób\n\n"
                f"📥 *Kliknij przycisk poniżej, aby wyświetlić interaktywną listę.*"
            ),
            color=discord.Color.green()
        )
        
        view_przycisku = RaportOdbiorcowView(wpisy_raportu, tytul)
        await interaction.followup.send(embed=raport_embed, view=view_przycisku, ephemeral=True)


async def setup(bot):
    await bot.add_cog(Ogloszenia(bot))
