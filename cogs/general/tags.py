import json
import unicodedata

import discord
from discord import app_commands
from discord.ext import commands
from sqlalchemy import create_engine, delete, insert, select, update
from sqlalchemy.orm import Session

from modals.tags import Tag

with open("./config.json", "r") as f:
    config = json.load(f)

engine = create_engine(config["DATABASE"])


class Tags(commands.GroupCog, name="tags"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        super().__init__()

    def fix_unicode(self, str):
        fixed = unicodedata.normalize("NFKD", str).encode("ascii", "ignore").decode()
        return fixed

    @app_commands.command(name="list", description="List existing tags.")
    async def list_tags(self, interaction: discord.Interaction):
        with Session(engine) as session:
            stmt = select(Tag.name).where(Tag.guild_id == interaction.guild_id)
            cur_tags = list(session.scalars(stmt).all())
        if len(cur_tags) == 0:
            return await interaction.response.send_message(
                f"No tags added.  To add a tag, do `/{interaction.command.parent.name} add`"
            )
        for tag in range(len(cur_tags)):
            cur_tags[tag] = "`" + cur_tags[tag] + "`"
        await interaction.response.send_message(
            f"Tags are short custom commands added by moderators. Current tags: {', '.join(cur_tags)}. To use a tag, do `/{interaction.command.parent.name} run`. ",
            ephemeral=True,
        )

    @app_commands.command(name="run", description="Runs the tag provided.")
    async def run_tag(self, interaction: discord.Interaction, tag_name: str):
        with Session(engine) as session:
            stmt = select(Tag).where(
                Tag.guild_id == interaction.guild_id, Tag.name == tag_name
            )
            tag = session.scalar(stmt)
        await interaction.response.send_message(tag.content)

    class NewTag(discord.ui.Modal, title="New Tag"):
        tag_name = discord.ui.TextInput(label="Tag Name")
        tag_content = discord.ui.TextInput(
            label="Tag Content", style=discord.TextStyle.paragraph
        )

        async def on_submit(self, interaction: discord.Interaction):
            await interaction.response.defer(thinking=True)
            with Session(engine) as session:
                stmt = select(Tag).where(
                    Tag.guild_id == interaction.guild_id,
                    Tag.name == self.tag_name.value,
                )
                exists = session.scalar(stmt)
                if exists:
                    return await interaction.followup.send(
                        content=f"The tag `{exists.name}` already exists. If you are trying to edit it, use `/{interaction.command.parent.name} edit {exists.name}`.",
                        ephemeral=True,
                    )
                else:
                    select_stmt = select(Tag).order_by(Tag.id.desc())
                    new_id = session.scalar(select_stmt)
                    if new_id:
                        new_id = new_id.id + 1
                    else:
                        new_id = 1
                    insert_stmt = insert(Tag).values(
                        id=new_id,
                        guild_id=interaction.guild_id,
                        name=self.tag_name.value.lower(),
                        content=self.tag_content.value,
                        added_by=interaction.user.id,
                    )
                    session.execute(insert_stmt)
                    session.commit()
            await interaction.followup.send(
                content=f"Added tag `{self.tag_name.value}`."
            )

    @app_commands.command(name="add", description="Adds a new tag.")
    @app_commands.checks.has_role("Trusted")
    async def add_tag(self, interaction: discord.Interaction):
        await interaction.response.send_modal(self.NewTag())

    @app_commands.command(name="remove", description="Removes the tag by name.")
    @app_commands.checks.has_role("Trusted")
    async def remove_tag(self, interaction: discord.Interaction, tag_name: str):
        with Session(engine) as session:
            sel_stmt = select(Tag).where(
                Tag.name == tag_name.lower(), Tag.guild_id == interaction.guild_id
            )
            sel = session.scalar(sel_stmt)
            if not sel:
                return await interaction.response.send_message(
                    f"`{tag_name}` not found.",
                    ephemeral=True,
                    delete_after=20,
                )
            stmt = delete(Tag).where(
                Tag.name == tag_name.lower(), Tag.guild_id == interaction.guild_id
            )
            session.execute(stmt)
            session.commit()
        await interaction.response.send_message(f"Removed tag `{tag_name}`.")

    @app_commands.command(name="update", description="Updates the tag by name.")
    @app_commands.checks.has_role("Trusted")
    async def update_tag(self, interaction: discord.Interaction, tag_name: str):
        with Session(engine) as session:
            sel_stmt = select(Tag).where(
                Tag.name == tag_name.lower(), Tag.guild_id == interaction.guild_id
            )
            sel = session.scalar(sel_stmt)
            if not sel:
                return await interaction.response.send_message(
                    f"`{tag_name}` not found.",
                    ephemeral=True,
                    delete_after=20,
                )
        await interaction.response.send_modal(
            self.UpdateTag(tag_name=sel.name, tag_content=sel.content)
        )

    class UpdateTag(discord.ui.Modal):
        def __init__(self, tag_name, tag_content):
            super().__init__(title="Update Tag")
            self.new_name = discord.ui.TextInput(label="Tag Name", default=tag_name)
            self.new_content = discord.ui.TextInput(
                label="Tag Content",
                style=discord.TextStyle.paragraph,
                default=tag_content,
            )
            self.add_item(self.new_name)
            self.add_item(self.new_content)

        async def on_submit(self, interaction: discord.Interaction):
            await interaction.response.defer(thinking=True)
            with Session(engine) as session:
                stmt = (
                    update(Tag)
                    .where(
                        Tag.name == self.new_name.value.lower(),
                        Tag.guild_id == interaction.guild_id,
                    )
                    .values(content=self.new_content.value)
                )
                session.execute(stmt)
                session.commit()
            await interaction.followup.send(content=f"Updated `{self.new_name.value}`")

    async def cog_app_command_error(
        self, interaction: discord.Interaction, error
    ) -> None:
        await interaction.response.send_message(error, ephemeral=True, delete_after=60)


async def setup(bot: commands.Bot):
    await bot.add_cog(Tags(bot))
    print(f"{__name__[5:].upper()} loaded")


async def teardown(bot: commands.Bot):
    await bot.remove_cog(Tags(bot))
    print(f"{__name__[5:].upper()} unloaded")
