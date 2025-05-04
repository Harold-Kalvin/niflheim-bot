from dataclasses import dataclass
from datetime import timedelta
from typing import TypedDict
from uuid import uuid4

from constants import NUMBER_EMOJIS
from db.client import redis_client

TEAM_DATA_KEY = "{guild_id}:team:{team_id}:data"  # hash
TEAM_MEMBERS_KEY = "{guild_id}:team:{team_id}:members"  # set


@dataclass()
class Team:
    id: str
    number: int  # team number withing an event (from 0 to 9)
    name: str
    max_members: int
    member_ids: list[int]  # discord user ids

    @property
    def is_full(self):
        return len(self.member_ids) >= self.max_members

    @property
    def title(self) -> str:
        return (
            f"{NUMBER_EMOJIS[self.number]} {self.name} ({len(self.member_ids)}/{self.max_members})"
        )

    def get_ui_value(self, member_global_names: dict[int, str | None]) -> str:
        value = self.title
        if self.member_ids:
            value += "\n"
            value += "\n".join(f"> {member_global_names[id]}" for id in self.member_ids)
        return value


class CreateTeamSchema(TypedDict):
    number: int
    name: str
    max_members: int


def create_teams(guild_id: int, teams_data: list[CreateTeamSchema]) -> list[Team]:
    teams = []

    pipe = redis_client.pipeline()
    for team_data in teams_data:
        id = str(uuid4())

        # set teams
        data_key = TEAM_DATA_KEY.format(guild_id=guild_id, team_id=id)
        pipe.hset(
            data_key,
            mapping={
                "id": id,
                "number": team_data["number"],
                "name": team_data["name"],
                "max_members": team_data["max_members"],
            },
        )

        teams.append(
            Team(
                id=id,
                number=team_data["number"],
                name=team_data["name"],
                max_members=team_data["max_members"],
                member_ids=[],
            )
        )

        pipe.expire(data_key, timedelta(days=30))

    pipe.execute()
    return teams


def get_team_by_id(guild_id: int, id: str) -> Team | None:
    data_key = TEAM_DATA_KEY.format(guild_id=guild_id, team_id=id)
    data = redis_client.hgetall(data_key)
    if not data:
        return

    members_key = TEAM_MEMBERS_KEY.format(guild_id=guild_id, team_id=id)
    member_ids = redis_client.smembers(members_key)
    return Team(
        id=id,
        number=int(data[b"number"]),  # pyright: ignore[reportIndexIssue]
        name=data[b"name"].decode(),  # pyright: ignore[reportIndexIssue]
        max_members=int(data[b"max_members"]),  # pyright: ignore[reportIndexIssue]
        member_ids=[int(id) for id in member_ids],  # pyright: ignore[reportGeneralTypeIssues]
    )


def add_member_to_team(guild_id: int, team_id: str, user_id: int):
    key = f"{guild_id}:team:{team_id}:members"
    key_existed = redis_client.exists(key)
    redis_client.sadd(key, user_id)
    if not key_existed:
        redis_client.expire(key, timedelta(days=30))


def remove_member_from_team(guild_id: int, team_id: str, user_id: int):
    redis_client.srem(f"{guild_id}:team:{team_id}:members", user_id)
