from dataclasses import dataclass

from db.client import redis_client

INFO_DATA_KEY = "{guild_id}:info:{info_id}:data"


@dataclass
class Info:
    id: str
    title: str
    description: str


def create_info(guild_id: int, id: str, title: str, description: str) -> Info:
    data_key = INFO_DATA_KEY.format(guild_id=guild_id, info_id=id)
    mapping = {"id": id, "title": title, "description": description}
    redis_client.hset(data_key, mapping=mapping)

    return Info(**mapping)


def get_info_by_id(guild_id: int, id: str) -> Info | None:
    data_key = INFO_DATA_KEY.format(guild_id=guild_id, info_id=id)
    data = redis_client.hgetall(data_key)
    if not data:
        return

    return Info(
        id=id,
        title=data[b"title"].decode(),  # pyright: ignore[reportIndexIssue]
        description=data[b"description"].decode(),  # pyright: ignore[reportIndexIssue]
    )


def delete_info(guild_id: int, id: str):
    data_key = INFO_DATA_KEY.format(guild_id=guild_id, info_id=id)
    redis_client.delete(data_key)


def get_infos(guild_id: int) -> list[Info]:
    pattern = INFO_DATA_KEY.format(guild_id=guild_id, info_id="*")
    data_keys = redis_client.scan_iter(match=pattern)
    infos = []
    for data_key in data_keys:
        data = redis_client.hgetall(data_key)
        infos.append(
            Info(
                id=data[b"id"].decode(),  # pyright: ignore[reportIndexIssue]
                title=data[b"title"].decode(),  # pyright: ignore[reportIndexIssue]
                description=data[b"description"].decode(),  # pyright: ignore[reportIndexIssue]
            )
        )
    return infos
