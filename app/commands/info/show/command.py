from discord import Client, Interaction


async def run_show_info_command(interaction: Interaction, client: Client):
    await interaction.response.defer(ephemeral=True)
