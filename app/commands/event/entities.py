from dataclasses import dataclass

from discord import Member, User

from constants import NUMBER_EMOJIS


@dataclass
class Team:
    id: int
    name: str
    max_members: int
    members: list[User | Member]

    @property
    def member_ids(self) -> list[int]:
        return [member.id for member in self.members]

    def get_ui_title(self):
        return f"{NUMBER_EMOJIS[self.id]} {self.name} ({len(self.members)}/{self.max_members})"

    def get_ui_value(self):
        return "\n".join(f"> {member.global_name}" for member in self.members)
