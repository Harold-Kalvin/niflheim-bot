import os

from discord import Intents, Interaction
from discord.ext import commands

from commands.event import event_command

TOKEN = os.environ["DISCORD_TOKEN"]

intents = Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix="!", intents=intents)


@client.event
async def on_ready():
    await client.tree.sync()


@client.tree.command(name="event", description="Create a simple poll")
async def event(interaction: Interaction):
    await event_command(interaction, client)


if __name__ == "__main__":
    client.run(TOKEN)
