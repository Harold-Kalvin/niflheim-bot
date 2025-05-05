import asyncio

from discord import Interaction, Message
from discord.ui import Button, View

from constants import NUMBER_EMOJIS
from db.models.events import get_event_by_id, get_teams_by_event
from db.models.teams import add_member_to_team, get_team_by_id, remove_member_from_team


class TeamSelectionView(View):
    def __init__(self, guild_id: int, event_id: str):
        super().__init__(timeout=None)
        self.guild_id = guild_id
        self.event_id = event_id
        self.lock = asyncio.Lock()

        sorted_teams = sorted(
            get_teams_by_event(self.guild_id, self.event_id), key=lambda t: t.number
        )
        for team in sorted_teams:
            button = Button(label=NUMBER_EMOJIS[team.number], custom_id=team.id)
            button.callback = self.make_callback(team.id)
            self.add_item(button)

    async def refresh_ui(self, message: Message | None):
        if not message or not message.embeds:
            return

        embed = message.embeds[0]
        if event := get_event_by_id(self.guild_id, self.event_id):
            for team_id in event.team_ids:
                if team := get_team_by_id(self.guild_id, team_id):
                    # embed field indexes:
                    # - 0 -> start date
                    # - 1 -> end date
                    # - 2+ -> teams
                    embed_index = team.number
                    embed_index += 1 if event.start else 0
                    embed_index += 1 if event.end else 0

                    if message.guild:
                        display_names = {m.id: m.display_name for m in message.guild.members}
                        embed.set_field_at(
                            embed_index, name="", value=team.get_ui_value(display_names)
                        )

            await message.edit(embed=embed)

    def make_callback(self, team_id: str):
        async def callback(interaction: Interaction):
            await interaction.response.defer(ephemeral=True)
            async with self.lock:
                user_id = interaction.user.id
                message = interaction.message

                team = get_team_by_id(self.guild_id, team_id)
                if not team:
                    await interaction.followup.send("❌ Team not found.", ephemeral=True)
                    return

                # user clicked on team he is already part of => leaves
                if user_id in team.member_ids:
                    remove_member_from_team(self.guild_id, team.id, user_id)
                    await self.refresh_ui(message)
                    return

                if team.is_full:
                    await interaction.followup.send("❌ Team is full.", ephemeral=True)
                    return

                # at this point, user switches teams
                for team in get_teams_by_event(self.guild_id, self.event_id):
                    remove_member_from_team(self.guild_id, team.id, user_id)

                add_member_to_team(self.guild_id, team_id, user_id)
                await self.refresh_ui(message)

        return callback
