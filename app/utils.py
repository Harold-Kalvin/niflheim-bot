from collections.abc import Sequence

from discord import Client, Member, User
from discord.role import Role


async def handle_dm_message(client: Client, user: User | Member, dm_channel) -> str | None:
    try:
        message = await client.wait_for(
            "message", check=lambda m: m.author == user and m.channel == dm_channel, timeout=600
        )
    except TimeoutError:
        await dm_channel.send("❌ Timeout. Command aborted.")
        return

    content = message.content
    if content.lower() == "cancel":
        await dm_channel.send("❌ Command aborted.")
        return

    return content


def highligh_role(text: str, roles: Sequence[Role]) -> str:
    for role in roles:
        if role.name in text:
            text = text.replace(f"@{role.name}", role.mention)
    return text
