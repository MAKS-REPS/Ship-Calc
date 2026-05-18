import discord
from discord import app_commands
from discord.ext import commands

class PollView(discord.ui.View):
    def __init__(self, question: str, duration_minutes: int, author: discord.Member):
        super().__init__(timeout=duration_minutes * 60)
        self.question = question
        self.author = author
        self.message = None
        self.yes_votes = set()
        self.no_votes = set()

    async def update_embed(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="📊 NOWA ANKIETA", 
            description=f"**{self.question}**", 
            color=0x3498db
        )
        embed.add_field(name="✅ Tak", value=f"`{len(self.yes_votes)}` głosów", inline=True)
        embed.add_field(name="❌ Nie", value=f"`{len(self.no_votes)}` głosów", inline=True)
        embed.set_footer(text="Głosowanie trwa... Wyniki są aktualizowane na żywo.")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Tak ✅", style=discord.ButtonStyle.green, custom_id="poll_yes")
    async def yes_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        if user_id in self.no_votes:
            self.no_votes.remove(user_id)
        self.yes_votes.add(user_id)
        await self.update_embed(interaction)

    @discord.ui.button(label="Nie ❌", style=discord.ButtonStyle.red, custom_id="poll_no")
    async def no_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        if user_id in self.yes_votes:
            self.yes_votes.remove(user_id)
        self.no_votes.add(user_id)
        await self.update_embed(interaction)

    @discord.ui.button(label="Kto zagłosował? 👀", style=discord.ButtonStyle.blurple, custom_id="poll_voters")
    async def voters_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message(
                "❌ Tylko twórca ankiety lub administrator może sprawdzić szczegóły głosowania!", 
                ephemeral=True
            )
        
        tak_lista = ", ".join([f"<@{uid}>" for uid in self.yes_votes]) if self.yes_votes else "Brak głosów"
        nie_lista = ", ".join([f"<@{uid}>" for uid in self.no_votes]) if self.no_votes else "Brak głosów"
        
        raport = (
            f"📊 **Szczegółowy raport ankiety:**\n\n"
            f"**Głosy na TAK ✅:**\n{tak_lista}\n\n"
            f"**Głosy na NIE ❌:**\n{nie_lista}"
        )
        await interaction.response.send_message(raport, ephemeral=True)

    async def on_timeout(self):
        for item in self.children:
            if item.custom_id in ["poll_yes", "poll_no"]:
                item.disabled = True
        if self.message:
            try:
                embed = self.message.embeds[0]
                embed.set_footer(text="⏰ Czas minął! Ankieta została zakończona.")
                await self.message.edit(embed=embed, view=self)
            except Exception as e:
                print(f"Nie udało się zamknąć ankiety: {e}")

# Klasa tzw. "Coga" (modułu) dla bota
class Ankiety(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="ankieta", description="Tworzy czasową ankietę z przyciskami.")
    @app_commands.describe(pytanie="Treść pytania ankietowego", minuty="Czas trwania w minutach (np. 5, 60, 1440)")
    async def ankieta(self, interaction: discord.Interaction, pytanie: str, minuty: int):
        if minuty <= 0:
            return await interaction.response.send_message("❌ Czas trwania musi być większy niż 0 minut!", ephemeral=True)

        view = PollView(question=pytanie, duration_minutes=minuty, author=interaction.user)
        
        embed = discord.Embed(
            title="📊 NOWA ANKIETA", 
            description=f"**{pytanie}**", 
            color=0x3498db
        )
        embed.add_field(name="✅ Tak", value="`0` głosów", inline=True)
        embed.add_field(name="❌ Nie", value="`0` głosów", inline=True)
        embed.set_footer(text=f"Ankieta aktywna przez: {minuty} min. | Głosowanie trwa...")
        
        await interaction.response.send_message(embed=embed, view=view)
        view.message = await interaction.original_response()

# Funkcja niezbędna, aby bot.load_extension() poprawnie załadował moduł
async def setup(bot: commands.Bot):
    await bot.add_cog(Ankiety(bot))
