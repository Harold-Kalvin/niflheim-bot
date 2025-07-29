from discord import Client, Interaction, TextChannel

from db.models.infos import create_info
from utils import handle_dm_message


async def run_create_info_command(interaction: Interaction, client: Client):
    await interaction.response.defer(ephemeral=True)

    user = interaction.user
    dm_channel = await user.create_dm()
    channel = interaction.channel
    if not isinstance(channel, TextChannel):
        await interaction.followup.send("❌ The command must be triggered in a text channel.")
        return

    await dm_channel.send("What is the **title** of your info?")
    title = await handle_dm_message(client, user, dm_channel)
    if not title:
        await interaction.followup.send("❌ Command aborted.", ephemeral=True)
        return

    await dm_channel.send("What is the **description** of your info?")
    description = await handle_dm_message(client, user, dm_channel)
    if not description:
        await interaction.followup.send("❌ Command aborted.", ephemeral=True)
        return

    create_info(channel.guild.id, title, description)
    await interaction.followup.send("✅ Info created successfully!", ephemeral=True)
