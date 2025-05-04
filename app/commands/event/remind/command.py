import logging
from datetime import UTC, datetime, timedelta

from discord import Client, Interaction, TextChannel

from db.models.reminders import create_reminder
from utils import handle_dm_message, highlight_mentions


async def run_remind_event_command(interaction: Interaction, client: Client):
    await interaction.response.defer(ephemeral=True)

    user = interaction.user
    dm_channel = await user.create_dm()
    channel = interaction.channel
    if not isinstance(channel, TextChannel):
        await interaction.followup.send("❌ The command must be triggered in a text channel.")
        return

    await dm_channel.send("What is the **title** of your event?")
    title = await handle_dm_message(client, user, dm_channel)
    if not title:
        await interaction.followup.send("❌ Command aborted.", ephemeral=True)
        return

    await dm_channel.send("When does it end? (format: `2025-04-27T10:33:50Z`)")
    end = await handle_dm_message(client, user, dm_channel)
    if not end:
        await interaction.followup.send("❌ Command aborted.", ephemeral=True)
        return
    try:
        end_date = datetime.fromisoformat(end).astimezone(UTC)
        end_unix = int(end_date.timestamp())
    except ValueError as e:
        logging.exception(e)
        await dm_channel.send("❌ Wrong format. Aborting.")
        await interaction.followup.send("❌ Command aborted.", ephemeral=True)
        return

    remind_time = end_date - timedelta(hours=1)
    if remind_time <= datetime.now(tz=UTC):
        await dm_channel.send("❌ The reminder time has already passed.")
        await interaction.followup.send("❌ Command aborted.", ephemeral=True)
        return

    await dm_channel.send("Who should I ping for the reminder? (mention a role, e.g., @Guildies)")
    role = await handle_dm_message(client, user, dm_channel)
    if not role:
        await interaction.followup.send("❌ Command aborted.", ephemeral=True)
        return
    highlighted_mentions = highlight_mentions(role, channel.guild.roles, channel.guild.members)

    text = f"{highlighted_mentions} {title} is ending soon (<t:{end_unix}:R>)."
    reminder = create_reminder(channel.guild.id, text, remind_time, channel.id)
    logging.info("Creating reminder %s", reminder)

    await interaction.followup.send("✅ Reminder created successfully!", ephemeral=True)
