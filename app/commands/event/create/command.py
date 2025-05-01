import logging
from collections.abc import Sequence
from datetime import UTC, datetime

from discord import Client, Embed, Interaction, Message, TextChannel
from discord.role import Role

from commands.event.create.components import TeamSelectionView
from commands.event.create.entities import Team
from constants import PRIMARY_COLOR
from utils import highligh_role


def _parse_date_range(input: str) -> tuple[datetime | None, datetime | None]:
    input_stripped = input.strip()
    start, end = None, None
    if input_stripped != "None":
        start_str, end_str = input_stripped.split("/")
        start = datetime.fromisoformat(start_str).astimezone(UTC)
        end = datetime.fromisoformat(end_str).astimezone(UTC)
    return start, end


def _parse_teams(input: str, roles: Sequence[Role]) -> list[Team]:
    teams = []
    for id, team_str in enumerate(input.split(",")):
        team_name, max_members = team_str.split("/")
        teams.append(
            Team(
                id=id,
                name=highligh_role(team_name.strip(), roles),
                max_members=int(max_members.strip()),
                members=[],
            )
        )
    return teams


async def create_event(interaction: Interaction, client: Client):
    await interaction.response.defer()

    user = interaction.user
    dm_channel = await user.create_dm()
    channel = interaction.channel
    if not isinstance(channel, TextChannel):
        await dm_channel.send("The command must be triggered in a text channel.")
        return

    def check_message(message: Message) -> bool:
        return message.author == user and message.channel == dm_channel

    await dm_channel.send("What is the **title** of your event? (mandatory)")
    title_msg = await client.wait_for("message", check=check_message)

    await dm_channel.send("What is the **description** of your event? (mandatory)")
    description_msg = await client.wait_for("message", check=check_message)

    await dm_channel.send(
        "What is the **start and end time**? (optional, format: "
        "`2025-04-27T10:33:50Z/2025-04-27T10:33:50Z`, any timezone works. "
        "`None` to ignore)"
    )
    dates_msg = await client.wait_for("message", check=check_message)
    try:
        start, end = _parse_date_range(dates_msg.content)
    except ValueError as e:
        logging.exception(e)
        await dm_channel.send("Wrong format, aborting.")
        return

    await dm_channel.send(
        "What are the **teams** and their **maximum participants**? "
        "(mandatory, format: `team1/13, team2/5`)"
    )
    teams_msg = await client.wait_for("message", check=check_message)
    try:
        teams = _parse_teams(teams_msg.content, channel.guild.roles)
    except ValueError as e:
        logging.exception(e)
        await dm_channel.send("Wrong format, aborting.")
        return

    embed = Embed(
        title=title_msg.content,
        description=highligh_role(description_msg.content, channel.guild.roles),
        color=PRIMARY_COLOR,
        timestamp=datetime.now(tz=UTC),
    )

    if start and end:
        start_unix = int(start.timestamp())
        end_unix = int(end.timestamp())
        embed.add_field(
            name="From: ", value=f"<t:{start_unix}:F> (<t:{start_unix}:R>)", inline=False
        )
        embed.add_field(name="To: ", value=f"<t:{end_unix}:F> (<t:{end_unix}:R>)", inline=False)

    for team in teams:
        embed.add_field(name="", value=team.get_ui_value(), inline=True)

    view = TeamSelectionView(teams)
    await channel.send(embed=embed, view=view)
    await interaction.followup.send("✅ Event created successfully!")
