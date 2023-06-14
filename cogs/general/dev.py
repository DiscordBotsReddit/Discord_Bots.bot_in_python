import json
import unicodedata

import discord
from discord import app_commands
from discord.ext import commands
from sqlalchemy import create_engine, delete, select
from sqlalchemy.orm import Session

from modals.devapplication import DevApplication

with open("./config.json", "r") as f:
    config = json.load(f)

engine = create_engine(config["DATABASE"])
DEV_ROLE = "DEVELOPER"
RESPONSE_MESSAGE = "Thank you for your application!  Please be patient as The Council processes your request."
EXISTING_APP_MESSAGE = f"You already requested the `{DEV_ROLE}` role.  Please be patient as The Council processes your request."
ALREADY_DEV_MESSAGE = f"You already have the `{DEV_ROLE}` role."
APPROVED_MESSAGE = (
    f"Your application for the `{DEV_ROLE.capitalize()}` role has been approved!"
)
DENIED_MESSAGE = (
    f"Your application for the `{DEV_ROLE.capitalize()}` role has been denied."
)


class Dev(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot
        self.APPROVED = (0, 90, 181)
        self.DENIED = (220, 50, 32)
        self.ORPHANED = (0, 0, 0)
        self.PENDING = (254, 254, 254)

    def fix_unicode(self, str):
        fixed = unicodedata.normalize("NFKD", str).encode("ascii", "ignore").decode()
        return fixed

    class ApprovalButtons(discord.ui.View):
        def __init__(self):
            super().__init__()
            self.APPROVED = (0, 90, 181)
            self.DENIED = (220, 50, 32)
            self.ORPHANED = (0, 0, 0)
            self.PENDING = (254, 254, 254)

        @discord.ui.button(label="Approve", style=discord.ButtonStyle.success)
        async def approved_callback(
            self, interaction: discord.Interaction, button: discord.ui.Button
        ):
            old_embed: dict = interaction.message.embeds[0].to_dict()
            embed: discord.Embed = discord.Embed(title="Developer Role Application")
            embed.set_author(
                name=old_embed["author"]["name"],
                icon_url=old_embed["author"]["icon_url"],
            )
            for field in old_embed["fields"]:
                embed.add_field(
                    name=field["name"], value=field["value"], inline=field["inline"]
                )
            try:
                member: discord.Member = await interaction.guild.fetch_member(
                    int(interaction.message.embeds[0].fields[0].value)
                )
                dev_role = [
                    role
                    for role in interaction.guild.roles
                    if role.name.lower() == DEV_ROLE.lower()
                ]
                if len(dev_role) == 0:
                    return await interaction.followup.send(
                        content=f"`{DEV_ROLE}` role not found."
                    )
                await member.add_roles(dev_role[0])
                embed.title = "**APPROVED** Developer Role Application"
                embed.color = discord.Color.from_rgb(*self.APPROVED)
                embed.set_footer(
                    text=f"Approved by {interaction.user.display_name} ({interaction.user.id})"
                )
                await member.send(APPROVED_MESSAGE)
            except:
                embed.title = "**ORPHANED** Developer Role Application"
                embed.color = discord.Color.from_rgb(*self.ORPHANED)
                embed.set_footer(
                    text=f"Checked by {interaction.user.display_name} ({interaction.user.id})"
                )
            with Session(engine) as session:
                del_stmt = delete(DevApplication).where(
                    DevApplication.user_id
                    == int(interaction.message.embeds[0].fields[0].value)
                )
                session.execute(del_stmt)
                session.commit()
            for child in self.children:
                if type(child) == discord.ui.Button:
                    child.disabled = True
                if child.label == "Deny":
                    child.style = discord.ButtonStyle.grey
            await interaction.response.edit_message(view=self, embed=embed)

        @discord.ui.button(label="Deny", style=discord.ButtonStyle.danger)
        async def deny_callback(
            self, interaction: discord.Interaction, button: discord.ui.Button
        ):
            old_embed = interaction.message.embeds[0].to_dict()
            embed = discord.Embed(title="Developer Role Application")
            embed.set_author(
                name=old_embed["author"]["name"],
                icon_url=old_embed["author"]["icon_url"],
            )
            for field in old_embed["fields"]:
                embed.add_field(
                    name=field["name"], value=field["value"], inline=field["inline"]
                )
            try:
                member = await interaction.guild.fetch_member(
                    int(interaction.message.embeds[0].fields[0].value)
                )
                embed.title = "**DENIED** Developer Role Application"
                embed.color = discord.Color.from_rgb(*self.DENIED)
                embed.set_footer(
                    text=f"Denied by {interaction.user.display_name} ({interaction.user.id})"
                )
                await member.send(DENIED_MESSAGE)
            except:
                embed.title = "**ORPHANED** Developer Role Application"
                embed.color = discord.Color.from_rgb(*self.ORPHANED)
                embed.set_footer(
                    text=f"Checked by {interaction.user.display_name} ({interaction.user.id})"
                )
            with Session(engine) as session:
                del_stmt = delete(DevApplication).where(
                    DevApplication.user_id
                    == int(interaction.message.embeds[0].fields[0].value)
                )
                session.execute(del_stmt)
                session.commit()
            for child in self.children:
                if type(child) == discord.ui.Button:
                    child.disabled = True
                if child.label == "Approve":
                    child.style = discord.ButtonStyle.grey
            await interaction.response.edit_message(view=self, embed=embed)

    @app_commands.command(
        name="dev_app", description="Apply to get the developer role."
    )
    async def new_dev_app(self, interaction: discord.Interaction, github_url: str):
        with Session(engine) as session:
            stmt = select(DevApplication).where(
                DevApplication.user_id == interaction.user.id
            )
            exists = session.execute(stmt).all()
        if len(exists) > 0:
            return await interaction.response.send_message(
                EXISTING_APP_MESSAGE, ephemeral=True
            )
        if len(interaction.user.roles) > 1:
            has_role = [
                role
                for role in interaction.user.roles
                if role.name.lower() == DEV_ROLE.lower()
            ]
            if len(has_role) > 0:
                return await interaction.response.send_message(
                    ALREADY_DEV_MESSAGE, ephemeral=True
                )
        mod_log = discord.utils.find(
            lambda c: c.name.lower() == "mod-log", interaction.guild.text_channels
        )
        application_embed = discord.Embed(
            title="Developer Role Application",
            color=discord.Color.from_rgb(*self.PENDING),
        )
        application_embed.set_author(
            name=interaction.user.display_name, icon_url=interaction.user.avatar.url
        )
        application_embed.add_field(
            name="User ID", value=interaction.user.id, inline=False
        )
        application_embed.add_field(name="Github URL", value=github_url)
        approval_buttons = self.ApprovalButtons()
        log_message = await mod_log.send(embed=application_embed, view=approval_buttons)
        dev_application = DevApplication(
            user_id=interaction.user.id,
            guild_id=interaction.guild_id,
            github_url=github_url,
            message_id=log_message.id,
        )
        with Session(engine) as session:
            session.add(dev_application)
            session.commit()
        await interaction.response.send_message(RESPONSE_MESSAGE, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Dev(bot))
    print(f"{__name__[5:].upper()} loaded")


async def teardown(bot: commands.Bot) -> None:
    await bot.remove_cog(Dev(bot))
    print(f"{__name__[5:].upper()} unloaded")
