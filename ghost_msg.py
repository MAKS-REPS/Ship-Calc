import discord
from discord import app_commands
from discord.ext import commands, tasks
import asyncio

class GhostMessageCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.active_loops = {} # Przechowuje aktywne pętle dla kanałów

    def get_seconds(self, time_str: str):
        # Konwersja czasu na sekundy
        if time_str == "10m": return 600
        if time_str == "30m": return 1800
        if time_str == "1h": return 3600
        if time_str == "24h": return 86400
        return 600

    @app_commands.command(name="ghost_loop", description="Ustawia automatyczne wysyłanie i usuwanie wiadomości.")
    @app_commands.choices(interval=[
        app_commands.Choice(name="10 minut", value="10m"),
        app_commands.Choice(name="30 minut", value="30m"),
        app_commands.Choice(name="1 godzina", value="1h"),
        app_commands.Choice(name="24 godziny", value="24h"),
    ])
    @app_commands.checks.has_permissions(administrator=True)
    async def ghost_loop(self, interaction: discord.Interaction, tresc: str, interval: str):
        channel_id = interaction.channel.id
        
        if channel_id in self.active_loops:
            return await interaction.response.send_message("❌ Na tym kanale już działa pętla! Najpierw użyj /stop_ghost.", ephemeral=True)

        seconds = self.get_seconds(interval)
        
        # Tworzymy zadanie w tle
        async def loop_task():
            while True:
                msg = await interaction.channel.send(tresc)
                await asyncio.sleep(2) # Wiadomość wisi 2 sekundy, żeby Discord ją zarejestrował
                await msg.delete()
                await asyncio.sleep(seconds - 2)

        task = asyncio.create_task(loop_task())
        self.active_loops[channel_id] = task
        
        await interaction.response.send_message(f"✅ Uruchomiono pętlę na tym kanale! Treść: '{tresc}', interwał: {interval}.", ephemeral=True)

    @app_commands.command(name="stop_ghost", description="Zatrzymuje automatyczne wysyłanie na tym kanale.")
    @app_commands.checks.has_permissions(administrator=True)
    async def stop_ghost(self, interaction: discord.Interaction):
        channel_id = interaction.channel.id
        
        if channel_id in self.active_loops:
            self.active_loops[channel_id].cancel()
            del self.active_loops[channel_id]
            await interaction.response.send_message("✅ Pętla została zatrzymana.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Nie ma aktywnej pętli na tym kanale.", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(GhostMessageCog(bot))
