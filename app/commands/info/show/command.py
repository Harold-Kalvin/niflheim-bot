from discord import Client, Embed, Interaction, TextChannel

from constants import PRIMARY_COLOR
from db.models.infos import get_info_by_id
from utils import highlight_mentions


async def run_show_info_command(interaction: Interaction, client: Client, info_id: str):
    await interaction.response.defer(ephemeral=True)

    channel = interaction.channel
    if not isinstance(channel, TextChannel):
        await interaction.followup.send("❌ The command must be triggered in a text channel.")
        return

    info = get_info_by_id(channel.guild.id, info_id)
    if not info:
        await interaction.followup.send("❌ The id does not exist.", ephemeral=True)
        return

    embed = Embed(
        title=info.title,
        description=highlight_mentions(
            info.description, channel.guild.roles, channel.guild.members
        ),
        color=PRIMARY_COLOR,
    )
    await channel.send(embed=embed)
    await interaction.followup.send("✅ Info showed successfully!", ephemeral=True)
