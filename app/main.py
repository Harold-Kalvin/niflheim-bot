import asyncio
import logging
import os
from datetime import UTC, datetime

from discord import Color, Embed, Intents, Interaction, TextChannel
from discord.ext import commands
from discord.ui import Button, View

TOKEN = os.environ["DISCORD_TOKEN"]

intents = Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix="!", intents=intents)
emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]


@client.event
async def on_ready():
    # Sync the slash commands
    await client.tree.sync()
    logging.info("We have logged in as %s", client.user)


class TeamSelectionView(View):
    def __init__(self, teams):
        super().__init__(timeout=None)
        self.teams = teams  # list of (team_name, max_participants, member list)
        self.users_team_id = {}
        self.lock = asyncio.Lock()

        for idx in range(len(teams)):
            button = Button(label=emojis[idx], custom_id=f"team_{idx}")
            button.callback = self.make_callback(idx)
            self.add_item(button)

    async def update_message_embed(self, message, team_ids_to_update=None):
        if message and message.embeds:
            embed = message.embeds[0]
            if team_ids_to_update is None:
                team_ids_to_update = range(len(self.teams))

            for idx in team_ids_to_update:
                team_name, max_participants, members = self.teams[idx]
                current_total = len(members)
                quoted_usernames = "\n".join(f"> {member.global_name}" for member in members)

                embed_index = 2 + idx  # assuming field 2+ are the teams
                embed.set_field_at(
                    embed_index,
                    name=f"{emojis[idx]} {team_name} ({current_total}/{max_participants})",
                    value=quoted_usernames,
                )
            await message.edit(embed=embed)

    def make_callback(self, new_team_id):
        async def callback(interaction: Interaction):
            await interaction.response.defer()
            async with self.lock:
                user = interaction.user
                message = interaction.message

                # check if the user is already in the team (toggle = leave)
                current_team_id = self.users_team_id.get(user.id)

                # if user clicks their own current team, just leave
                if current_team_id == new_team_id:
                    self.teams[current_team_id][2] = [
                        member for member in self.teams[current_team_id][2] if member.id != user.id
                    ]
                    self.users_team_id.pop(user.id, None)
                    await self.update_message_embed(message)
                    return

                # check if target team is full BEFORE changing anything
                if len(self.teams[new_team_id][2]) >= self.teams[new_team_id][1]:
                    await interaction.followup.send("The team is full!", ephemeral=True)
                    return

                # at this point, the user will switch teams

                # remove user from all teams
                team_ids_to_update = set()
                for idx, (_, _, members) in enumerate(self.teams):
                    if any(member.id == user.id for member in members):
                        self.teams[idx][2] = [member for member in members if member.id != user.id]
                        team_ids_to_update.add(idx)
                self.users_team_id.pop(user.id, None)

                # Add to new team
                self.teams[new_team_id][2].append(user)
                self.users_team_id[user.id] = new_team_id
                team_ids_to_update.add(new_team_id)

                await self.update_message_embed(message, team_ids_to_update)

        return callback


@client.tree.command(name="event", description="Create a simple poll")
async def event(interaction: Interaction):
    await interaction.response.defer()

    user = interaction.user
    dm_channel = await user.create_dm()

    def check_message(m):
        return m.author == user and m.channel == dm_channel

    await dm_channel.send("What is the **title** of your event? (mandatory)")
    title_msg = await client.wait_for("message", check=check_message)
    title = title_msg.content

    await dm_channel.send("What is the **description** of your event? (mandatory)")
    description_msg = await client.wait_for("message", check=check_message)
    description = description_msg.content

    await dm_channel.send(
        "What is the **start and end time**? (optional, format: "
        "`2025-04-27T10:33:50Z/2025-04-27T10:33:50Z`, any timezone works. "
        "`None` to ignore)"
    )
    date_msg = await client.wait_for("message", check=check_message)
    date_stripped = date_msg.content.strip()
    start, end = None, None
    if date_stripped != "None":
        try:
            start_str, end_str = date_stripped.split("/")
            start = datetime.fromisoformat(start_str).astimezone(UTC)
            end = datetime.fromisoformat(end_str).astimezone(UTC)
        except ValueError as e:
            logging.exception(e)
            await dm_channel.send("Wrong format, aborting.")
            return

    await dm_channel.send(
        "What are the **teams** and their **maximum participants**? "
        "(mandatory, format: `team1/13, team2/5`)"
    )
    teams_msg = await client.wait_for("message", check=check_message)
    teams = []
    for team_str in teams_msg.content.strip().split(","):
        try:
            team_name, max_participant = team_str.split("/")
            teams.append([team_name.strip(), int(max_participant.strip()), []])
        except ValueError as e:
            logging.exception(e)
            await dm_channel.send("Wrong format, aborting.")
            return

    channel = interaction.channel
    if not isinstance(channel, TextChannel):
        await dm_channel.send("The command must be triggered in a text channel.")
        return

    embed = Embed(
        title=title,
        description=description,
        color=Color(int("#7c4f9c".strip("#"), 16)),
        timestamp=datetime.now(tz=UTC),
    )

    if start and end:
        start_unix = int(start.timestamp())
        end_unix = int(end.timestamp())
        value = (
            f"From: <t:{start_unix}:F> (<t:{start_unix}:R>)\n"
            f"To: <t:{end_unix}:F> (<t:{end_unix}:R>)"
        )
        embed.add_field(name="**Event Duration:**", value=value, inline=False)

    embed.add_field(name="**Teams:**", value="", inline=False)
    for idx, (team_name, max_participants, _) in enumerate(teams):
        embed.add_field(
            name=f"{emojis[idx]} {team_name} (0/{max_participants})", value="", inline=True
        )

    view = TeamSelectionView(teams)
    await channel.send(embed=embed, view=view)
    await interaction.followup.send("✅ Event created successfully!")


if __name__ == "__main__":
    client.run(TOKEN)
