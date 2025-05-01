import logging
import os

from discord import Intents
from discord.ext import commands

from tasks.reminders import ReminderTask

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

TOKEN = os.environ["DISCORD_TOKEN"]

intents = Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix="!", intents=intents)


@client.event
async def on_ready():
    await client.load_extension("commands.event.group")
    await client.tree.sync()

    # tasks
    ReminderTask(client)


if __name__ == "__main__":
    client.run(TOKEN)
