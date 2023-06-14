import json
import unicodedata

import discord
from discord import app_commands
from discord.ext import commands

with open("./config.json", "r") as f:
    VERSION = json.load(f)["VERSION"]


class Version(commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    def fix_unicode(self, str):
        fixed = unicodedata.normalize("NFKD", str).encode("ascii", "ignore").decode()
        return fixed

    @app_commands.command(name="version", description="Show the bot's version.")
    async def show_version(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"Current version: v{VERSION}")


async def setup(bot):
    await bot.add_cog(Version(bot))
    print(f"{__name__[5:].upper()} loaded")


async def teardown(bot):
    await bot.remove_cog(Version(bot))
    print(f"{__name__[5:].upper()} unloaded")
