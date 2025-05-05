import logging
from datetime import UTC, datetime

from discord import Client, Embed, Guild, Interaction, TextChannel

from commands.event.create.components import TeamSelectionView
from constants import PRIMARY_COLOR
from db.models.events import create_event
from db.models.teams import Team, create_teams
from utils import handle_dm_message, highlight_mentions


def _parse_date_range(input: str) -> tuple[datetime | None, datetime | None]:
    input_stripped = input.strip()
    start, end = None, None
    if input_stripped != "None":
        start_str, end_str = input_stripped.split("/")
        start = datetime.fromisoformat(start_str).astimezone(UTC)
        end = datetime.fromisoformat(end_str).astimezone(UTC)
    return start, end


def _parse_teams(input: str, guild: Guild) -> list[Team]:
    teams_data = []
    for number, team_str in enumerate(input.split(",")):
        team_name, max_members = team_str.split("/")
        highlighted_team_name = highlight_mentions(team_name.strip(), guild.roles, guild.members)
        stripped_max_members = int(max_members.strip())
        teams_data.append(
            {"name": highlighted_team_name, "number": number, "max_members": stripped_max_members}
        )
    return create_teams(guild.id, teams_data)


def _create_embed(
    channel: TextChannel,
    title: str,
    description: str,
    start: datetime | None,
    end: datetime | None,
    teams: list[Team],
) -> Embed:
    embed = Embed(
        title=title,
        description=highlight_mentions(description, channel.guild.roles, channel.guild.members),
        color=PRIMARY_COLOR,
        timestamp=datetime.now(tz=UTC),
    )

    if start:
        start_unix = int(start.timestamp())
        embed.add_field(
            name="From: ", value=f"<t:{start_unix}:F> (<t:{start_unix}:R>)", inline=False
        )

    if end:
        end_unix = int(end.timestamp())
        embed.add_field(name="Until: ", value=f"<t:{end_unix}:F> (<t:{end_unix}:R>)", inline=False)

    for team in teams:
        display_names = {m.id: m.display_name for m in channel.guild.members}
        embed.add_field(name="", value=team.get_ui_value(display_names), inline=True)

    return embed


async def run_create_event_command(interaction: Interaction, client: Client):
    await interaction.response.defer(ephemeral=True)

    user = interaction.user
    dm_channel = await user.create_dm()
    channel = interaction.channel
    if not isinstance(channel, TextChannel):
        await interaction.followup.send("❌ The command must be triggered in a text channel.")
        return

    await dm_channel.send("What is the **name** of your event?")
    name = await handle_dm_message(client, user, dm_channel)
    if not name:
        await interaction.followup.send("❌ Command aborted.", ephemeral=True)
        return

    await dm_channel.send("What is the **description** of your event?")
    description = await handle_dm_message(client, user, dm_channel)
    if not description:
        await interaction.followup.send("❌ Command aborted.", ephemeral=True)
        return

    await dm_channel.send(
        "What is the **start and end time**? (format: "
        "`2025-04-27T10:33:50Z/2025-04-27T10:33:50Z`, any timezone works. "
        "`None` to ignore)"
    )
    dates = await handle_dm_message(client, user, dm_channel)
    if not dates:
        await interaction.followup.send("❌ Command aborted.", ephemeral=True)
        return

    try:
        start, end = _parse_date_range(dates)
    except ValueError as e:
        logging.exception(e)
        await dm_channel.send("❌ Wrong format. Aborting.")
        await interaction.followup.send("❌ Command aborted.", ephemeral=True)
        return

    await dm_channel.send(
        "What are the **teams** and their **maximum participants**? (format: `team1/13, team2/5`)"
    )
    teams_msg = await handle_dm_message(client, user, dm_channel)
    if not teams_msg:
        await interaction.followup.send("❌ Command aborted.", ephemeral=True)
        return

    try:
        teams = _parse_teams(teams_msg, channel.guild)
    except ValueError as e:
        logging.exception(e)
        await dm_channel.send("❌ Wrong format. Aborting.")
        await interaction.followup.send("❌ Command aborted.", ephemeral=True)
        return

    event = create_event(channel.guild.id, name, start, end, [team.id for team in teams])
    embed = _create_embed(channel, name, description, start, end, teams)
    view = TeamSelectionView(channel.guild.id, event.id)
    await channel.send(embed=embed, view=view)
    await interaction.followup.send("✅ Event created successfully!", ephemeral=True)
