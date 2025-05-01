import os

from discord import Intents
from discord.ext import commands

TOKEN = os.environ["DISCORD_TOKEN"]

intents = Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix="!", intents=intents)


@client.event
async def on_ready():
    await client.load_extension("commands.event.group")
    await client.tree.sync()


if __name__ == "__main__":
    client.run(TOKEN)
