import logging
from datetime import UTC, datetime

from discord.ext import tasks

from db.models.reminders import get_reminders, mark_reminder_as_processed


class ReminderTask:
    def __init__(self, bot):
        self.bot = bot
        self.send_reminder.start()

    @tasks.loop(minutes=1.0)
    async def send_reminder(self):
        now = datetime.now(tz=UTC)

        # for each reminders of each servers
        for guild in self.bot.guilds:
            reminders = get_reminders(guild.id)
            for reminder in reminders:
                # send unprocessed reminders in due time
                if now >= reminder.remind_time and not reminder.processed:
                    mark_reminder_as_processed(guild.id, reminder.id)
                    if channel := self.bot.get_channel(reminder.channel_id):
                        logging.info("Sending reminder: %s", reminder)
                        await channel.send(reminder.text)
                    else:
                        logging.error("Reminder %s not sent. Channel not found.", reminder)

    @send_reminder.before_loop
    async def before_loop(self):
        await self.bot.wait_until_ready()
