import os
import unicodedata
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

HELPER_ROLE = "HELPER"
DEVELOPER_ROLE = "DEVELOPER"


async def find_cmd(bot: commands.Bot, cmd: str, group: Optional[str]):
    if group is None:
        command = discord.utils.find(
            lambda c: c.name.lower() == cmd.lower(),
            await bot.tree.fetch_commands(),
        )
        return command
    else:
        cmd_group = discord.utils.find(
            lambda cg: cg.name.lower() == group.lower(),
            await bot.tree.fetch_commands(),
        )
        for child in cmd_group.options:  # type: ignore
            if child.name.lower() == cmd.lower():
                return child
    return "No command found."


class Helper(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super().__init__
        self.bot = bot

    def fix_unicode(self, str):
        fixed = unicodedata.normalize("NFKD", str).encode("ascii", "ignore").decode()
        return fixed

    @app_commands.command(
        name="helper",
        description="Toggles the helper role if you have the developer role.",
    )
    async def get_helper_role(self, interaction: discord.Interaction):
        dev_role = discord.utils.find(
            lambda r: r.name.lower() == DEVELOPER_ROLE.lower(), interaction.guild.roles  # type: ignore
        )
        if dev_role not in interaction.user.roles:  # type: ignore
            dev_app = await find_cmd(self.bot, cmd="dev_app")  # type: ignore
            return await interaction.response.send_message(
                f"You do not have the {dev_role.mention} role.  Please apply to be a developer with {dev_app.mention} before adding the helper role!",  # type: ignore
                ephemeral=True,
                delete_after=60,
            )
        helper_role = discord.utils.find(
            lambda r: r.name.lower() == HELPER_ROLE.lower(), interaction.guild.roles  # type: ignore
        )
        if helper_role in interaction.user.roles:  # type: ignore
            await interaction.user.remove_roles(helper_role)  # type: ignore
            return await interaction.response.send_message(
                f"Removed the {helper_role.mention} role!"  # type: ignore
            )
        else:
            await interaction.user.add_roles(helper_role)  # type: ignore
            await interaction.response.send_message(
                f"Added the {helper_role.mention} role!",  # type: ignore
                ephemeral=True,
                delete_after=60,
            )

    async def cog_app_command_error(
        self, interaction: discord.Interaction, error
    ) -> None:
        await interaction.response.send_message(error, ephemeral=True, delete_after=60)


async def setup(bot):
    await bot.add_cog(Helper(bot))
    print(f"{__name__[5:].upper()} loaded")


async def teardown(bot):
    await bot.remove_cog(Helper(bot))
    print(f"{__name__[5:].upper()} unloaded")
