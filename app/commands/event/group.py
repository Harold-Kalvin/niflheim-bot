from discord import Interaction, app_commands
from discord.ext import commands

from commands.event.create.command import create_event


class EventGroup(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    event = app_commands.Group(name="event", description="Manage events")

    @event.command(name="create", description="Create a new event")
    async def create(self, interaction: Interaction):
        await create_event(interaction, self.bot)


async def setup(bot: commands.Bot):
    await bot.add_cog(EventGroup(bot))
