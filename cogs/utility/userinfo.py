import datetime
import os
import unicodedata
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands


def format_date(date_to_fmt):
    return (
        datetime.date.isoformat(date_to_fmt).replace("/T/", " ").replace(r"/\.\d+/", "")
    )


class UserInfo(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super().__init__
        self.bot = bot

    def fix_unicode(self, str):
        fixed = unicodedata.normalize("NFKD", str).encode("ascii", "ignore").decode()
        return fixed

    @app_commands.command(
        name="userinfo", description="Get information about someone or yourself"
    )
    @app_commands.describe(member='Leave blank for self or mention the member you want info for.')
    async def userinfo(
        self, interaction: discord.Interaction, member: Optional[discord.Member]
    ):
        if member is None:
            member = interaction.user  # type: ignore
        embed = discord.Embed(color=member.color)  # type: ignore
        embed.set_author(name=member.global_name, icon_url=member.avatar.url)  # type: ignore
        if member.nick:  # type: ignore
            embed.add_field(name="Nickname", value=member.nick, inline=True)  # type: ignore
        embed.add_field(
            name="Date Joined", value=format_date(member.joined_at), inline=True  # type: ignore
        )
        embed.add_field(
            name="User Creation Date", value=format_date(member.created_at), inline=True  # type: ignore
        )
        try:
            embed.set_footer(text=f"Requested by {interaction.user.name}", icon_url=interaction.user.avatar.url)  # type: ignore
        except:
            embed.set_footer(text=f"Requested by {interaction.user.name}")
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(UserInfo(bot))
    print(f"{__name__[5:].upper()} loaded")


async def teardown(bot):
    await bot.remove_cog(UserInfo(bot))
    print(f"{__name__[5:].upper()} unloaded")
