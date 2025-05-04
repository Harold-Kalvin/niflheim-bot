from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import uuid4

from db.client import redis_client
from db.models.teams import Team, get_team_by_id

EVENT_DATA_KEY = "{guild_id}:event:{event_id}:data"  # hash
EVENT_TEAMS_KEY = "{guild_id}:event:{event_id}:teams"  # set


@dataclass
class Event:
    id: str
    name: str
    start: datetime | None
    end: datetime | None
    team_ids: list[str]


def create_event(
    guild_id: int, name: str, start: datetime | None, end: datetime | None, team_ids: list[str]
) -> Event:
    pipe = redis_client.pipeline()
    id = str(uuid4())

    # set event
    data_key = EVENT_DATA_KEY.format(guild_id=guild_id, event_id=id)
    mapping = {"id": id, "name": name}
    if start:
        mapping["start"] = start.isoformat()
    if end:
        mapping["end"] = end.isoformat()
    pipe.hset(data_key, mapping=mapping)

    # set teams in event
    teams_key = EVENT_TEAMS_KEY.format(guild_id=guild_id, event_id=id)
    for team_id in team_ids:
        pipe.sadd(teams_key, team_id)

    event = Event(id=id, name=name, start=start, end=end, team_ids=team_ids)

    pipe.expire(data_key, timedelta(days=30))
    pipe.expire(teams_key, timedelta(days=30))
    pipe.execute()

    return event


def get_event_by_id(guild_id: int, id: str) -> Event | None:
    data_key = EVENT_DATA_KEY.format(guild_id=guild_id, event_id=id)
    data = redis_client.hgetall(data_key)
    if not data:
        return

    teams_key = EVENT_TEAMS_KEY.format(guild_id=guild_id, event_id=id)
    team_ids = redis_client.smembers(teams_key)

    start = data.get(b"start")  # pyright: ignore[ reportAttributeAccessIssue ]
    if start:
        start = datetime.fromisoformat(start.decode("utf-8"))

    end = data.get(b"end")  # pyright: ignore[ reportAttributeAccessIssue ]
    if end:
        end = datetime.fromisoformat(end.decode("utf-8"))

    return Event(
        id=id,
        name=data[b"name"].decode(),  # pyright: ignore[reportIndexIssue]
        start=start,
        end=end,
        team_ids=[id.decode("utf-8") for id in team_ids],  # pyright: ignore[reportGeneralTypeIssues]
    )


def get_events(guild_id: int) -> list[Event]:
    pattern = EVENT_DATA_KEY.format(guild_id=guild_id, event_id="*")
    data_keys = redis_client.scan_iter(match=pattern)
    events = []
    for data_key in data_keys:
        data = redis_client.hgetall(data_key)
        id = data[b"id"].decode("utf-8")  # pyright: ignore[reportIndexIssue]

        teams_key = EVENT_TEAMS_KEY.format(guild_id=guild_id, event_id=id)
        team_ids = redis_client.smembers(teams_key)

        start = data.get(b"start")  # pyright: ignore[ reportAttributeAccessIssue ]
        if start:
            start = datetime.fromisoformat(start.decode("utf-8"))

        end = data.get(b"end")  # pyright: ignore[ reportAttributeAccessIssue ]
        if end:
            end = datetime.fromisoformat(end.decode("utf-8"))

        events.append(
            Event(
                id=id,
                name=data[b"name"].decode(),  # pyright: ignore[reportIndexIssue]
                start=start,
                end=end,
                team_ids=[id.decode("utf-8") for id in team_ids],  # pyright: ignore[reportGeneralTypeIssues]
            )
        )

    return events


def get_teams_by_event(guild_id: int, event_id: str) -> list[Team]:
    teams = []
    if event := get_event_by_id(guild_id, event_id):
        for team_id in event.team_ids:
            teams.append(get_team_by_id(guild_id, team_id))
    return teams
