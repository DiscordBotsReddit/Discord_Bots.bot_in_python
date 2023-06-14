import sys
import unicodedata

import discord
from discord import app_commands
from discord.ext import commands


class Restart(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot

    def fix_unicode(self, str):
        fixed = unicodedata.normalize("NFKD", str).encode("ascii", "ignore").decode()
        return fixed

    @app_commands.command(name="restart", description="Restart the bot.")
    async def restart_bot(self, interaction: discord.Interaction):
        await interaction.response.send_message("Restarting!", ephemeral=True)
        sys.exit(2)

    async def cog_app_command_error(
        self, interaction: discord.Interaction, error
    ) -> None:
        await interaction.response.send_message(error, ephemeral=True, delete_after=60)


async def setup(bot):
    await bot.add_cog(Restart(bot))
    print(f"{__name__[5:].upper()} loaded")


async def teardown(bot):
    await bot.remove_cog(Restart(bot))
    print(f"{__name__[5:].upper()} unloaded")
