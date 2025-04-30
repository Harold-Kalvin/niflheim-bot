from collections.abc import Sequence

from discord.role import Role


def highligh_role(text: str, roles: Sequence[Role]) -> str:
    for role in roles:
        if role.name in text:
            text = text.replace(f"@{role.name}", role.mention)
    return text
