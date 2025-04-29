import asyncio

from discord import Interaction, Message
from discord.ui import Button, View

from commands.event.entities import Team
from constants import NUMBER_EMOJIS


class TeamSelectionView(View):
    def __init__(self, teams: list[Team]):
        super().__init__(timeout=None)
        self.teams: dict[int, Team] = {team.id: team for team in teams}
        self.lock = asyncio.Lock()

        for id, team in self.teams.items():
            button = Button(label=NUMBER_EMOJIS[id], custom_id=f"team_{id}")
            button.callback = self.make_callback(team)
            self.add_item(button)

    async def update_message_embed(
        self, message: Message | None, teams_to_update: list[Team] | None = None
    ):
        if message and message.embeds:
            embed = message.embeds[0]
            if teams_to_update is None:
                teams_to_update = list(self.teams.values())

            for team in teams_to_update:
                # 0 -> start date
                # 1 -> end date
                # 2+ -> teams
                embed_index = 2 + team.id
                embed.set_field_at(embed_index, name=team.get_ui_title(), value=team.get_ui_value())
            await message.edit(embed=embed)

    def get_user_team(self, user_id: int) -> Team | None:
        for team in self.teams.values():
            if user_id in team.member_ids:
                return team
        return None

    def make_callback(self, new_team: Team):
        async def callback(interaction: Interaction):
            await interaction.response.defer()
            async with self.lock:
                user = interaction.user
                message = interaction.message

                # user leaves his current team
                current_team = self.get_user_team(user.id)
                if current_team and current_team.id == new_team.id:
                    current_team.members = [
                        member for member in current_team.members if member.id != user.id
                    ]
                    self.teams[current_team.id] = current_team
                    await self.update_message_embed(message)
                    return

                # destination team is full, do nothing
                if len(new_team.members) >= new_team.max_members:
                    await interaction.followup.send("The team is full!", ephemeral=True)
                    return

                # at this point, user will switch teams
                # remove user from all teams
                teams_to_update = []
                for id, team in self.teams.items():
                    if any(member.id == user.id for member in team.members):
                        self.teams[id].members = [
                            member for member in team.members if member.id != user.id
                        ]
                        teams_to_update.append(self.teams[id])

                # add user to new team
                self.teams[new_team.id].members.append(user)
                teams_to_update.append(self.teams[new_team.id])

                await self.update_message_embed(message, teams_to_update)

        return callback
