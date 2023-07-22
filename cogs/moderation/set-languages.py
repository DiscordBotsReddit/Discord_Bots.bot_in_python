import json
import unicodedata
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands
from sqlalchemy import create_engine, delete, insert, select
from sqlalchemy.orm import Session

from modals.language import Language

with open("./config.json", "r") as f:
    config = json.load(f)

engine = create_engine(config["DATABASE"])


class SetLanguages(commands.GroupCog, name="languages"):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot

    def fix_unicode(self, str):
        fixed = unicodedata.normalize("NFKD", str).encode("ascii", "ignore").decode()
        return fixed

    @app_commands.command(name="add", description="Add a new language.")
    @app_commands.describe(
        role="Leave blank for a new role to be created with the same name as the language."
    )
    @app_commands.checks.has_role("Trusted")
    @app_commands.checks.bot_has_permissions(manage_roles=True)
    async def add_language(
        self,
        interaction: discord.Interaction,
        language: str,
        role: Optional[discord.Role],
    ):
        if role is None:
            lang_role = [
                role
                for role in interaction.guild.roles  # type: ignore
                if role.name.lower() == language.lower()
            ]
            if len(lang_role) > 0:
                role = lang_role[0]
            else:
                role = await interaction.guild.create_role(name=language.capitalize())  # type: ignore
        with Session(engine) as session:
            stmt = select(Language).where(
                Language.guild_id == interaction.guild_id,
                Language.name == language.lower(),
            )
            exists = session.scalar(stmt)
            if exists:
                return await interaction.response.send_message(
                    f"The language `{exists.name}` already exists.",
                    ephemeral=True,
                    delete_after=60,
                )
            else:
                select_stmt = select(Language).order_by(Language.id.desc())
                insert_stmt = insert(Language).values(  
                    guild_id=interaction.guild_id,
                    name=language.lower(),
                    role_id=role.id,
                )
                session.execute(insert_stmt)
                session.commit()
                await interaction.response.send_message(
                    f"Added `{language}` to languages."
                )

    @app_commands.command(name="remove", description="Remove a language.")
    @app_commands.checks.has_role("Trusted")
    async def remove_language(self, interaction: discord.Interaction, language: str):
        with Session(engine) as session:
            stmt = select(Language).where(
                Language.guild_id == interaction.guild_id,
                Language.name == language.lower(),
            )
            exists = session.scalar(stmt)
            if not exists:
                return await interaction.response.send_message(
                    f"Language `{language}` not found.",
                    ephemeral=True,
                    delete_after=20,
                )
            del_stmt = delete(Language).where(
                Language.guild_id == interaction.guild_id,
                Language.name == language.lower(),
            )
            session.execute(del_stmt)
            session.commit()
        lang_role = discord.utils.find(
            lambda c: c.name.lower() == language.lower(), interaction.guild.roles  # type: ignore
        )
        print(lang_role)
        await interaction.response.send_message(f"Deleted `{language}` from languages.")

    @app_commands.command(name="list", description="List all the languages available.")
    async def list_languages(self, interaction: discord.Interaction):
        with Session(engine) as session:
            stmt = select(Language.name).where(
                Language.guild_id == interaction.guild_id  # type: ignore
            )
            cur_langs = list(session.scalars(stmt).all())
        if len(cur_langs) == 0:
            return await interaction.response.send_message(
                f"No languages added.  To add a language, do `/{interaction.command.parent.name} add"  # type: ignore
            )
        for lang in range(len(cur_langs)):
            cur_langs[lang] = "`" + cur_langs[lang] + "`"
        await interaction.response.send_message(
            f"Current languages: {', '.join(cur_langs)}. To get a language role, do `/{interaction.command.parent.name} get`. ",  # type: ignore
            ephemeral=True,
        )

    @app_commands.command(name="get", description="Get the language role specified.")
    async def get_language_role(self, interaction: discord.Interaction, language: str):
        with Session(engine) as session:
            stmt = select(Language).where(
                Language.guild_id == interaction.guild_id,
                Language.name == language.lower(),
            )
            lang = session.scalar(stmt)
        lang_role = interaction.guild.get_role(lang.role_id)  # type: ignore
        if lang_role not in interaction.user.roles:  # type: ignore
            await interaction.user.add_roles(lang_role)  # type: ignore
            await interaction.response.send_message(
                f"Added `{lang.name.capitalize()}`", ephemeral=True, delete_after=60  # type: ignore
            )
        else:
            await interaction.response.send_message(
                f"You already have the {lang_role.mention} role."  # type: ignore
            )


async def setup(bot):
    await bot.add_cog(SetLanguages(bot))
    print(f"{__name__[5:].upper()} loaded")


async def teardown(bot):
    await bot.remove_cog(SetLanguages(bot))
    print(f"{__name__[5:].upper()} unloaded")
