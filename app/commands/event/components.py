import asyncio

from discord import Interaction
from discord.ui import Button, View

from constants import NUMBER_EMOJIS


class TeamSelectionView(View):
    def __init__(self, teams):
        super().__init__(timeout=None)
        self.teams = teams
        self.users_team_id = {}
        self.lock = asyncio.Lock()

        for idx in range(len(teams)):
            button = Button(label=NUMBER_EMOJIS[idx], custom_id=f"team_{idx}")
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

                embed_index = 2 + idx
                embed.set_field_at(
                    embed_index,
                    name=f"{NUMBER_EMOJIS[idx]} {team_name} ({current_total}/{max_participants})",
                    value=quoted_usernames,
                )
            await message.edit(embed=embed)

    def make_callback(self, new_team_id):
        async def callback(interaction: Interaction):
            await interaction.response.defer()
            async with self.lock:
                user = interaction.user
                message = interaction.message

                current_team_id = self.users_team_id.get(user.id)
                if current_team_id == new_team_id:
                    self.teams[current_team_id][2] = [
                        member for member in self.teams[current_team_id][2] if member.id != user.id
                    ]
                    self.users_team_id.pop(user.id, None)
                    await self.update_message_embed(message)
                    return

                if len(self.teams[new_team_id][2]) >= self.teams[new_team_id][1]:
                    await interaction.followup.send("The team is full!", ephemeral=True)
                    return

                team_ids_to_update = set()
                for idx, (_, _, members) in enumerate(self.teams):
                    if any(member.id == user.id for member in members):
                        self.teams[idx][2] = [member for member in members if member.id != user.id]
                        team_ids_to_update.add(idx)
                self.users_team_id.pop(user.id, None)

                self.teams[new_team_id][2].append(user)
                self.users_team_id[user.id] = new_team_id
                team_ids_to_update.add(new_team_id)

                await self.update_message_embed(message, team_ids_to_update)

        return callback
