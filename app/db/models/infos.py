from dataclasses import dataclass
from uuid import uuid4

from db.client import redis_client

INFO_DATA_KEY = "{guild_id}:info:{info_id}:data"


@dataclass
class Info:
    id: str
    title: str
    description: str


def create_info(guild_id: int, title: str, description: str) -> Info:
    id = str(uuid4())

    data_key = INFO_DATA_KEY.format(guild_id=guild_id, info_id=id)
    mapping = {"id": id, "title": title, "description": description}
    redis_client.hset(data_key, mapping=mapping)

    return Info(**mapping)
