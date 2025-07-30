from discord import Interaction, app_commands
from discord.ext import commands

from commands.info.create.command import run_create_info_command
from commands.info.delete.command import run_delete_info_command
from commands.info.list_ids.command import run_list_info_ids_command
from commands.info.show.command import run_show_info_command


class InfoGroup(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    event = app_commands.Group(name="info", description="Manage informations")

    @event.command(name="create", description="Create a new information")
    async def create(self, interaction: Interaction):
        await run_create_info_command(interaction, self.bot)

    @event.command(name="delete", description="Delete an information")
    async def delete(self, interaction: Interaction, id: str):
        await run_delete_info_command(interaction, self.bot, id)

    @event.command(name="show", description="Show an information")
    async def show(self, interaction: Interaction, id: str):
        await run_show_info_command(interaction, self.bot, id)

    @event.command(name="list_ids", description="List all the information ids")
    async def list_ids(self, interaction: Interaction):
        await run_list_info_ids_command(interaction, self.bot)


async def setup(bot: commands.Bot):
    await bot.add_cog(InfoGroup(bot))
