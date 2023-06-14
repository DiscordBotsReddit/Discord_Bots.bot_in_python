import os
import unicodedata

import discord
from discord import app_commands
from discord.ext import commands


class UserInfo(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super().__init__
        self.bot = bot

    def fix_unicode(self, str):
        fixed = unicodedata.normalize("NFKD", str).encode("ascii", "ignore").decode()
        return fixed


async def setup(bot):
    await bot.add_cog(UserInfo(bot))
    print(f"{__name__[5:].upper()} loaded")


async def teardown(bot):
    await bot.remove_cog(UserInfo(bot))
    print(f"{__name__[5:].upper()} unloaded")
