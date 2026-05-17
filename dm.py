import discord
from discord.ext import commands
import asyncio

# ==================== KONFIGURACJA LINKÓW ====================
DISCORD_LINK = "https://discord.gg/xayYadg6TJ"
SPREADSHEET_LINK = "https://docs.google.com/spreadsheets/d/1j0UHW-WgdYwKvHOwscJrY9lIO_4MmyYxCgN_fgXz_iQ/edit?gid=518648393#gid=518648393"
USFANS_LINK = "https://www.usfans.com/register?ref=DJPZ6T"
KAKOBUY_LINK = "https://ikako.vip/r/maksr3ps"
# =============================================================


# ==================== WIDOKI PRZYCISKÓW ====================

class WelcomeUsfansDMView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(label="Dołącz do Discorda", url=DISCORD_LINK, style=discord.ButtonStyle.link))
        self.add_item(discord.ui.Button(label="Zarejestruj się w USFans", url=USFANS_LINK, style=discord.ButtonStyle.link))
        self.add_item(discord.ui.Button(label="Otwórz Spreadsheet (5000+)", url=SPREADSHEET_LINK, style=discord.ButtonStyle.link))


class WelcomeKakobuyDMView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(label="Dołącz do Discorda", url=DISCORD_LINK, style=discord.ButtonStyle.link))
        self.add_item(discord.ui.Button(label="Zarejestruj się w Kakobuy", url=KAKOBUY_LINK, style=discord.ButtonStyle.link))
        self.add_item(discord.ui.Button(label="Otwórz Spreadsheet (5000+)", url=SPREADSHEET_LINK, style=discord.ButtonStyle.link))


# ==================== GŁÓWNA KLASA MODUŁU DM ====================

class WelcomeDMs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Wykrywa dołączenie nowej osoby na serwer i wysyła obie wersje wiadomości prywatnych."""
        
        # --- 1. GENEROWANIE I WYSYŁANIE EMBO-A USFANS ---
        embed_usfans = discord.Embed(
            title="Witaj na serwerze Maks.R3ps! (1/2)",
            description=(
                f"💎 **Link do discorda**\n"
                f"➡️ [Kliknij tutaj, aby dołączyć]({DISCORD_LINK})\n\n"
                f"💸 **Odbierz darmowy kupon na -40% na start w USFans**\n"
                f"➡️ [Zarejestruj się i odbierz zniżkę]({USFANS_LINK})\n\n"
                f"📰 **Spreadsheet z ponad 5000+ itemkami:**\n"
                f"➡️ [Przeglądaj arkusz z przedmiotami]({SPREADSHEET_LINK})"
            ),
            color=discord.Color.blue()
        )
        embed_usfans.set_footer(text="Maks Reps 2.0 • USFans")

        try:
            await member.send(embed=embed_usfans, view=WelcomeUsfansDMView())
            print(f"✅ Pomyślnie wysłano DM (USFans) do {member.name}.")
        except discord.Forbidden:
            print(f"❌ Nie udało się wysłać DM do {member.name} (Zablokowane wiadomości prywatne).")
            return  # Jeśli ma zablokowany DM, przerywamy wysyłanie drugiego embeda
        except Exception as e:
            print(f"⚠️ Błąd przy wysyłaniu DM (USFans) do {member.name}: {e}")

        # Krótka sekunda przerwy, aby Discord nie uznał bota za spamera
        await asyncio.sleep(1.5)

        # --- 2. GENEROWANIE I WYSYŁANIE EMBO-A KAKOBUY ---
        embed_kakobuy = discord.Embed(
            title="Witaj na serwerze Maks.R3ps! (2/2)",
            description=(
                f"💎 **Link do discorda**\n"
                f"➡️ [Kliknij tutaj, aby dołączyć]({DISCORD_LINK})\n\n"
                f"💸 **Odbierz darmowe bonusy na start w Kakobuy**\n"
                f"➡️ [Zarejestruj się przez ten link]({KAKOBUY_LINK})\n\n"
                f"🏷️ Po wpisaniu kodu **Maks20** dostaje się kupon na **-20%** na wysyłkę!\n"
                f"💰 Dodatkowo wpisując kod **Maks.R3ps** otrzymasz darmowe **15$** na paczkę!\n\n"
                f"📰 **Spreadsheet z ponad 5000+ itemkami:**\n"
                f"➡️ [Przeglądaj arkusz z przedmiotami]({SPREADSHEET_LINK})"
            ),
            color=discord.Color.red()
        )
        embed_kakobuy.set_footer(text="Maks Reps 2.0 • Kakobuy")

        try:
            await member.send(embed=embed_kakobuy, view=WelcomeKakobuyDMView())
            print(f"✅ Pomyślnie wysłano DM (Kakobuy) do {member.name}.")
        except Exception as e:
            print(f"⚠️ Błąd przy wysyłaniu DM (Kakobuy) do {member.name}: {e}")


async def setup(bot):
    await bot.add_cog(WelcomeDMs(bot))
