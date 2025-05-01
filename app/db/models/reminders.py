from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from db.client import redis_client


@dataclass()
class Reminder:
    id: str
    text: str
    remind_time: datetime
    channel_id: int
    processed: bool = False

    def __str__(self):
        return f"{self.remind_time} / {self.text} / {self.channel_id}"


def create_reminder(guild_id: int, text: str, remind_time: datetime, channel_id: int) -> Reminder:
    id = str(uuid4())
    key = f"{guild_id}:reminder:{id}"
    redis_client.hset(
        key,
        mapping={
            "id": id,
            "text": text,
            "remind_time": remind_time.isoformat(),
            "channel_id": channel_id,
            "processed": "0",
        },
    )

    # expires 1 day after the remind time
    expiry_delta = remind_time + timedelta(days=1) - datetime.now(tz=UTC)
    redis_client.expire(key, expiry_delta)
    return Reminder(id=id, text=text, remind_time=remind_time, channel_id=channel_id)


def get_reminders(guild_id: int) -> list[Reminder]:
    pattern = f"{guild_id}:reminder:*"
    keys = redis_client.scan_iter(match=pattern)
    reminders = []
    for key in keys:
        data = redis_client.hgetall(key)
        reminders.append(
            Reminder(
                id=data[b"id"].decode("utf-8"),  # pyright: ignore[reportIndexIssue]
                text=data[b"text"].decode("utf-8"),  # pyright: ignore[reportIndexIssue]
                remind_time=datetime.fromisoformat(
                    data[b"remind_time"].decode("utf-8")  # pyright: ignore[reportIndexIssue]
                ),
                channel_id=int(data[b"channel_id"].decode("utf-8")),  # pyright: ignore[reportIndexIssue]
                processed=data[b"processed"].decode("utf-8") == "1",  # pyright: ignore[reportIndexIssue]
            )
        )
    return reminders


def mark_reminder_as_processed(guild_id: int, reminder_id: str):
    key = f"{guild_id}:reminder:{reminder_id}"
    redis_client.hset(key, "processed", "1")
