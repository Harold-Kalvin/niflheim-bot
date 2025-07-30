from discord import Client, Interaction, TextChannel

from db.models.infos import delete_info, get_info_by_id


async def run_delete_info_command(interaction: Interaction, client: Client, info_id: str):
    await interaction.response.defer(ephemeral=True)

    channel = interaction.channel
    if not isinstance(channel, TextChannel):
        await interaction.followup.send("❌ The command must be triggered in a text channel.")
        return

    info = get_info_by_id(channel.guild.id, info_id)
    if not info:
        await interaction.followup.send("❌ The id does not exist.", ephemeral=True)
        return

    delete_info(channel.guild.id, info_id)
    await interaction.followup.send("✅ Info deleted successfully!", ephemeral=True)
