from discord import Interaction, app_commands
from discord.ext import commands

from commands.event.create.command import run_create_event_command
from commands.event.remind.command import run_remind_event_command


class EventGroup(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    event = app_commands.Group(name="event", description="Manage events")

    @event.command(name="create", description="Create a new event")
    async def create(self, interaction: Interaction):
        await run_create_event_command(interaction, self.bot)

    @event.command(name="remind", description="Remind when an event ends in an hour")
    async def remind(self, interaction: Interaction):
        await run_remind_event_command(interaction, self.bot)


async def setup(bot: commands.Bot):
    await bot.add_cog(EventGroup(bot))
