from typing import List

import nextcord
from nextcord.ext import commands

from configuration import Configuration

bot = commands.Bot()

@bot.event
async def on_ready():
    print(
        f"Ready! Logged in as {bot.user.name}#{bot.user.discriminator}"
    )

config = Configuration("configuration.json")

bot.load_extension("minecraftpinger", extras={"config": config})

bot.run(config.BOT_TOKEN)