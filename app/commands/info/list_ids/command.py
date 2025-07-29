from discord import Client, Embed, Interaction, TextChannel

from constants import PRIMARY_COLOR
from db.models.infos import Info, get_infos


def _generate_embed_description(infos: list[Info]):
    result = ""
    for info in infos:
        result += f"__**{info.id}**__: {info.title}\n"
    return result


async def run_list_info_ids_command(interaction: Interaction, client: Client):
    await interaction.response.defer(ephemeral=True)

    channel = interaction.channel
    if not isinstance(channel, TextChannel):
        await interaction.followup.send("❌ The command must be triggered in a text channel.")
        return

    infos = get_infos(channel.guild.id)
    if not infos:
        await interaction.followup.send("❌ No informations yet.", ephemeral=True)
        return

    embed = Embed(
        title="Information ids", description=_generate_embed_description(infos), color=PRIMARY_COLOR
    )
    await interaction.followup.send(embed=embed, ephemeral=True)
