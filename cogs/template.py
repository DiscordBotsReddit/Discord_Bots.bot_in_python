import json
import os
import unicodedata

import discord
from discord import app_commands
from discord.ext import commands
from sqlalchemy import BigInteger, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

with open("./config.json", "r") as f:
    config = json.load(f)

engine = create_engine(config["DATABASE"])


class TEMPLATE(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def fix_unicode(self, str):
        fixed = unicodedata.normalize("NFKD", str).encode("ascii", "ignore").decode()
        return fixed


async def setup(bot: commands.Bot):
    await bot.add_cog(TEMPLATE(bot))
    print(f"{__name__[5:].upper()} loaded")


async def teardown(bot: commands.Bot):
    await bot.remove_cog(TEMPLATE(bot))
    print(f"{__name__[5:].upper()} unloaded")
