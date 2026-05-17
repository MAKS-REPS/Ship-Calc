import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import io
from typing import Optional

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
        app_commands.Choice(name="Wszyscy użytkownicy", value=-1)  # -1 oznacza brak limitu
    ])
    @app_commands.checks.has_permissions(administrator=True)
    async def ogloszenie(
        self, 
        interaction: discord.Interaction, 
        tytul: str, 
        tresc: str, 
        kolor: str,
        limit_osob: int,
        obraz: Optional[discord.Attachment] = None
    ):
        # Informujemy Discorda, że bot przetwarza dane (zapobiega timeoutowi interakcji)
        await interaction.response.defer(ephemeral=True)

        guild = interaction.guild
        if not guild:
            await interaction.followup.send("❌ Tej komendy można użyć tylko na serwerze Discord!", ephemeral=True)
            return

        # Mapowanie wybranego koloru embeda
        kolory_map = {
            "blue": discord.Color.blue(),
            "red": discord.Color.red(),
            "green": discord.Color.green(),
            "gold": discord.Color.gold()
        }
        wybrany_kolor = kolory_map.get(kolor, discord.Color.default())

        # Tworzenie estetycznego embeda ogłoszeniowego
        embed = discord.Embed(
            title=f"📢 {tytul}",
            description=tresc.replace("\\n", "\n"),
            color=wybrany_kolor
        )
        embed.set_footer(text=f"Ogłoszenie z serwera: {guild.name} • Maks Reps 2.0")
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        # Sprawdzanie poprawności załączonego obrazu
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

        # Lista do zbierania raportu tekstowego o użytkownikach
        lista_raportu = []
        lista_raportu.append(f"RAPORT Z WYSYŁKI OGŁOSZENIA: {tytul}")
        lista_raportu.append(f"Serwer: {guild.name}")
        lista_raportu.append("-" * 50 + "\n")

        print(f"🔮 Rozpoczynam wysyłanie ogłoszenia. Limit ustawiony na: {limit_osob if limit_osob != -1 else 'Wszyscy'}")

        for member in czlonkowie:
            if member.bot:
                continue

            # Jeśli ustawiono konkretny limit i został on osiągnięty – przerywamy wysyłanie
            if limit_osob != -1 and wyslane_do_liczba >= limit_osob:
                break

            wyslane_do_liczba += 1

            try:
                await member.send(embed=embed)
                sukcesy += 1
                lista_raportu.append(f"[SUKCES] {member.name}#{member.discriminator} (ID: {member.id}) - Wiadomość dostarczona.")
                # Anty-Spam: Bezpieczny odstęp czasowy
                await asyncio.sleep(2.5)
            except discord.Forbidden:
                bledy += 1
                lista_raportu.append(f"[BLOKADA] {member.name}#{member.discriminator} (ID: {member.id}) - Zablokowane wiadomości prywatne.")
            except Exception as e:
                bledy += 1
                lista_raportu.append(f"[BŁĄD] {member.name}#{member.discriminator} (ID: {member.id}) - Nieznany błąd: {e}")

        # Przygotowanie pliku tekstowego z raportem
        raport_tekst = "\n".join(lista_raportu)
        plik_raportu = discord.File(io.BytesIO(raport_tekst.encode('utf-8')), filename="odbiorcy.txt")

        # Generowanie końcowego embeda z podsumowaniem dla administratora
        raport_embed = discord.Embed(
            title="✅ Wysyłanie ogłoszenia zakończone!",
            description=(
                f"📊 **Statystyki wysyłki:**\n"
                f"🟢 Wysłano pomyślnie: **{sukcesy}** osób\n"
                f"🔴 Pominięto / Błędy: **{bledy}** osób\n\n"
                f"ℹ️ *Poniżej znajduje się plik tekstowy z pełną listą osób, które otrzymały lub zablokowały tę wiadomość.*"
            ),
            color=discord.Color.green()
        )
        
        # Wysyłamy odpowiedź zawierającą podsumowanie oraz załącznik z plikiem tekstowym
        await interaction.followup.send(embed=raport_embed, file=plik_raportu, ephemeral=True)

    @ogloszenie.error
    async def ogloszenie_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("❌ Nie masz uprawnień (`Administrator`) do używania tej komendy!", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Ogloszenia(bot))
