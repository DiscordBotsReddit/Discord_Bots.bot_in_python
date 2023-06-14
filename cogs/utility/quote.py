import json
import unicodedata

import discord
from discord import app_commands
from discord.ext import commands

with open("./config.json", "r") as f:
    config = json.load(f)


class Quote(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super().__init__
        self.bot = bot

    def fix_unicode(self, str):
        fixed = unicodedata.normalize("NFKD", str).encode("ascii", "ignore").decode()
        return fixed

    @app_commands.command(
        name="quote",
        description="Quote a message.  If quoting by text, include the user.",
    )
    async def quote_message(
        self,
        interaction: discord.Interaction,
        id: str = None,  # Apparently int doesn't support IDs. 🤷‍♂️
        link: str = None,
        text: str = None,
        user: discord.Member = None,
    ):
        if id is not None:
            try:
                int(id)
            except:
                return await interaction.response.send_message(
                    "If searching by ID, you must use only the message_id."
                )
            try:
                text_channels = [chan for chan in interaction.guild.text_channels]
                for channel in text_channels:
                    async for msg in channel.history(limit=200):
                        if msg.id == int(id):
                            message = msg
            except Exception as e:
                return await interaction.response.send_message(
                    e, ephemeral=True, delete_after=10
                )
        elif link is not None:
            try:
                text_channels = [chan for chan in interaction.guild.text_channels]
                for channel in text_channels:
                    async for msg in channel.history(limit=200):
                        if msg.id == int(link.split("/")[-1]):
                            message = msg
            except:
                return await interaction.response.send_message(
                    "Invalid message link.", ephemeral=True, delete_after=20
                )
        elif text is not None and user is not None:
            messages = [
                message
                async for message in interaction.channel.history(limit=200)
                if message.author == user and text.lower() in message.content.lower()
            ]
            if len(messages) > 1:
                return await interaction.response.send_message(
                    "Too many messages.  Please narrow down the text.",
                    ephemeral=True,
                    delete_after=60,
                )
            else:
                message = messages[0]
        else:
            return await interaction.response.send_message(
                "No valid search query entered.\nIf searching by `text`, you must include a `member` in the search.",
                ephemeral=True,
                delete_after=10,
            )
        quote_text = message.content
        quote_permalink = f"\n\n[Permalink]({message.jump_url})"
        if len(quote_text) > config["DESCRIPTION_LIMIT"] - len(quote_permalink):
            quote_text = (
                quote_text[0 : config["DESCRIPTION_LIMIT"] - len(quote_permalink) - 1]
                + "..."
            )
        try:
            member = await interaction.guild.fetch_member(message.author.id)
            embed = discord.Embed(
                color=member.color,
                timestamp=message.created_at,
                description=quote_text + quote_permalink,
            )
            embed.set_author(
                name=message.author.display_name,
                icon_url=message.author.avatar.url,
            )
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            return await interaction.response.send_message(
                f"That member is no longer in this server and is unable to be quoted.\n{e}",
                ephemeral=True,
                delete_after=20,
            )


async def setup(bot):
    await bot.add_cog(Quote(bot))
    print(f"{__name__[5:].upper()} loaded")


async def teardown(bot):
    await bot.remove_cog(Quote(bot))
    print(f"{__name__[5:].upper()} unloaded")
