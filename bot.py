import json
import os

import discord
from discord.ext.commands import Bot, ExtensionAlreadyLoaded

with open("config.json", "r") as f:
    config = json.load(f)


intents = discord.Intents.none()
intents.guilds = True
intents.message_content = True

bot = Bot(command_prefix="?", intents=intents)

@bot.event
async def on_ready():
    for subdir, _, files in os.walk("cogs"):
        files = [file for file in files if file.endswith(".py") and "template" not in file]
        for file in files:
            if len(subdir.split("cogs\\")) >= 2:
                try:
                    sub = subdir.split('cogs\\')[1]
                    await bot.load_extension(f"cogs.{sub}.{file[:-3]}")
                except ExtensionAlreadyLoaded:
                    sub = subdir.split('cogs\\')[1]
                    await bot.reload_extension(f"cogs.{sub}.{file[:-3]}")
            else:
                try:
                    await bot.load_extension(f"{subdir}.{file[:-3]}")
                except ExtensionAlreadyLoaded:
                    await bot.reload_extension(f"{subdir}.{file[:-3]}")
    # await bot.tree.sync()
    print("Logged in with", bot.user)


bot.run(config["TOKEN"])
