import discord
from discord import app_commands
from discord.ext import commands

class PollView(discord.ui.View):
    def __init__(self, question: str = None, author_id: int = None):
        # Timeout = None sprawia, że przycisk nie wygasa samoczynnie (będziemy go ręcznie blokować)
        super().__init__(timeout=None)
        self.question = question
        self.author_id = author_id
        # Słowniki przechowujące głosy (używamy setów do unikalności)
        self.yes_votes = set()
        self.no_votes = set()

    async def update_embed(self, interaction: discord.Interaction):
        embed = interaction.message.embeds[0]
        embed.set_field_at(0, name="✅ Tak", value=f"`{len(self.yes_votes)}` głosów", inline=True)
        embed.set_field_at(1, name="❌ Nie", value=f"`{len(self.no_votes)}` głosów", inline=True)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Tak ✅", style=discord.ButtonStyle.green, custom_id="poll_yes_persistent")
    async def yes_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        if user_id in self.no_votes: self.no_votes.remove(user_id)
        self.yes_votes.add(user_id)
        await self.update_embed(interaction)

    @discord.ui.button(label="Nie ❌", style=discord.ButtonStyle.red, custom_id="poll_no_persistent")
    async def no_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        if user_id in self.yes_votes: self.yes_votes.remove(user_id)
        self.no_votes.add(user_id)
        await self.update_embed(interaction)

    @discord.ui.button(label="Kto zagłosował? 👀", style=discord.ButtonStyle.blurple, custom_id="poll_voters_persistent")
    async def voters_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ Tylko twórca ankiety!", ephemeral=True)
        
        tak_lista = ", ".join([f"<@{uid}>" for uid in self.yes_votes]) or "Brak"
        nie_lista = ", ".join([f"<@{uid}>" for uid in self.no_votes]) or "Brak"
        await interaction.response.send_message(f"✅ TAK: {tak_lista}\n❌ NIE: {nie_lista}", ephemeral=True)

class Ankiety(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="ankieta", description="Tworzy ankietę")
    async def ankieta(self, interaction: discord.Interaction, pytanie: str, godziny: int):
        view = PollView(question=pytanie, author_id=interaction.user.id)
        
        embed = discord.Embed(title="📊 ANKIETA", description=f"**{pytanie}**", color=0x3498db)
        embed.add_field(name="✅ Tak", value="`0` głosów", inline=True)
        embed.add_field(name="❌ Nie", value="`0` głosów", inline=True)
        embed.set_footer(text=f"Ankieta trwa {godziny} godzin.")
        
        await interaction.response.send_message(embed=embed, view=view)
        
        # Zaplanowanie zadania, które zablokuje przyciski po X godzinach
        import asyncio
        await asyncio.sleep(godziny * 3600)
        
        for item in view.children:
            item.disabled = True
        embed.set_footer(text="⏰ Czas minął! Ankieta zakończona.")
        await interaction.edit_original_response(embed=embed, view=view)

async def setup(bot: commands.Bot):
    await bot.add_cog(Ankiety(bot))
