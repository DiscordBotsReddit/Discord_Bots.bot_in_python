import json
import unicodedata
from datetime import UTC, datetime, timedelta
from os import name
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands, tasks
from humanfriendly import parse_timespan
from sqlalchemy import create_engine, delete, insert, select
from sqlalchemy.orm import Session

from modals.reminders import Reminder

with open("./config.json", "r") as f:
    config = json.load(f)

engine = create_engine(config["DATABASE"])


class RemindMe(commands.GroupCog, name='reminders'):
    def __init__(self, bot: commands.Bot):
        super().__init__
        self.bot = bot
        self.check_reminders.start()

    def fix_unicode(self, str):
        fixed = unicodedata.normalize("NFKD", str).encode("ascii", "ignore").decode()
        return fixed
    
    @app_commands.command(name='set', description='Have the bot remind you of a message.')
    @app_commands.describe(length='Humanfriendly version (5h = 5 hours / 10m = 10 minutes / etc.)')
    async def set_reminder(self, interaction: discord.Interaction, length: str, reminder: Optional[str]):
        if not str(interaction.channel.type) == 'text':  # type: ignore
            return await interaction.response.send_message("Please run this command in a text channel.", ephemeral=True, delete_after=60)
        if reminder is None:
            reminder = "No reminder reason given"
        parsed_length = parse_timespan(length)
        timestamp_reminding_from = int((datetime.now(tz=UTC) - datetime(1970,1,1,tzinfo=UTC)).total_seconds())
        timestamp_to_remind_at = int(((datetime.now(tz=UTC) + timedelta(seconds=parsed_length)) - datetime(1970,1,1,tzinfo=UTC)).total_seconds())
        with Session(engine) as session:
            new_reminder = Reminder(
                user_id=interaction.user.id,
                timestamp_to_remind_at=timestamp_to_remind_at,
                timestamp_reminding_from=timestamp_reminding_from,
                original_channel_id=interaction.channel_id,
                reminder=reminder
            )
            session.add(new_reminder)
            session.commit()
        await interaction.response.send_message(f"Set a reminder for {interaction.user.mention} at <t:{timestamp_to_remind_at}:f> for `{reminder}`.")

    @app_commands.command(name='unset', description='Remove a reminder.')
    @app_commands.describe(reminder_id="Get the reminder ID with the '/reminders list' command.")
    async def unset_reminder(self, interaction: discord.Interaction, reminder_id: int):
        with Session(engine) as session:
            reminder = session.scalar(select(Reminder).where(Reminder.id==reminder_id))
        if reminder is None:
            return await interaction.response.send_message(f"No reminder found with ID #{reminder_id}.  Please try again.", ephemeral=True, delete_after=5)
        if reminder.user_id == interaction.user.id:  # type: ignore
            session.execute(delete(Reminder).where(Reminder.id==reminder.id))
            session.commit()
            return await interaction.response.send_message(f"Your reminder `{reminder.reminder}` for <t:{reminder.timestamp_to_remind_at}:f> was removed.", ephemeral=True, delete_after=120)
        else:
            return await interaction.response.send_message("That's not a reminder you set.", ephemeral=True, delete_after=30)
        
    @app_commands.command(name='list', description='Lists the next 25 of your active reminders.')
    async def list_active_reminders(self, interaction: discord.Interaction):
        with Session(engine) as session:
            reminders = session.scalars(select(Reminder).where(Reminder.user_id==interaction.user.id).order_by(Reminder.timestamp_to_remind_at.asc()).limit(25)).all()
        if len(reminders) == 0:
            return await interaction.response.send_message("No reminders set.", ephemeral=True, delete_after=10)
        reminder_embed = discord.Embed(title="Active Reminders", color=discord.Color.dark_embed())
        if interaction.user.avatar.url is not None:
            reminder_embed.set_footer(text="​", icon_url=interaction.user.avatar.url)
        for reminder in reminders:
            reminder_embed.add_field(name=f'ID #{reminder.id}', value=f'`{reminder.reminder}`\n<t:{reminder.timestamp_to_remind_at}:R>', inline=False)
        await interaction.response.send_message(embed=reminder_embed, ephemeral=True, delete_after=300)

    @tasks.loop(seconds=1)
    async def check_reminders(self):
        timestamp_now = int((datetime.now(tz=UTC) - datetime(1970,1,1,tzinfo=UTC)).total_seconds())
        with Session(engine) as session:
            reminders_to_send = session.scalars(select(Reminder).where(Reminder.timestamp_to_remind_at<=timestamp_now)).all()
        if len(reminders_to_send) > 0:
            for reminder in reminders_to_send:
                chan_to_send_reminder = await self.bot.fetch_channel(reminder.original_channel_id)
                user_that_set_reminder = await chan_to_send_reminder.guild.fetch_member(reminder.user_id)  # type: ignore
                await chan_to_send_reminder.send(f"Reminder!  {user_that_set_reminder.mention}:  `{reminder.reminder}`")  # type: ignore
                with Session(engine) as session:
                    session.execute(delete(Reminder).where(Reminder.id==reminder.id))
                    session.commit()
                continue

async def setup(bot):
    await bot.add_cog(RemindMe(bot))
    print(f"{__name__[5:].upper()} loaded")


async def teardown(bot):
    await bot.remove_cog(RemindMe(bot))
    print(f"{__name__[5:].upper()} unloaded")
