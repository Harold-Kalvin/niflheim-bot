import logging
from datetime import UTC, datetime, timedelta

from discord import Client, Interaction, Message, TextChannel

from db.models.reminders import create_reminder
from utils import highligh_role


async def remind_event(interaction: Interaction, client: Client):
    await interaction.response.defer()

    user = interaction.user
    dm_channel = await user.create_dm()
    channel = interaction.channel
    if not isinstance(channel, TextChannel):
        await dm_channel.send("The command must be triggered in a text channel.")
        return

    def check_message(message: Message) -> bool:
        return message.author == user and message.channel == dm_channel

    await dm_channel.send("What is the **title** of your event?")
    title_msg = await client.wait_for("message", check=check_message)

    await dm_channel.send("When does it end? (format: `2025-04-27T10:33:50Z`)")
    end_msg = await client.wait_for("message", check=check_message)
    try:
        end = datetime.fromisoformat(end_msg.content).astimezone(UTC)
    except ValueError as e:
        logging.exception(e)
        await dm_channel.send("❌ Wrong format. Aborting.")
        return

    remind_time = end - timedelta(hours=1)
    if remind_time <= datetime.now(tz=UTC):
        await dm_channel.send("❌ The reminder time has already passed.")
        return

    await dm_channel.send("Who should I ping for the reminder? (mention a role, e.g., @Guildies)")
    role_msg = await client.wait_for("message", check=check_message)
    highlighted_role = highligh_role(role_msg.content, channel.guild.roles)

    end_unix = int(end.timestamp())
    text = f"{highlighted_role} {title_msg.content} is ending soon (<t:{end_unix}:R>)."
    reminder = create_reminder(channel.guild.id, text, remind_time, channel.id)
    logging.info("Creating reminder %s", reminder)

    await interaction.followup.send("✅ Reminder created successfully!")
