import logging

from discord.ext.commands import Bot

from commands.event.create.components import TeamSelectionView
from db.models.events import get_events


def restore_team_views(bot: Bot):
    for guild in bot.guilds:
        try:
            events = get_events(guild.id)
            for event in events:
                logging.info("Restoring event: %s", event.id)
                view = TeamSelectionView(guild.id, event.id)
                bot.add_view(view)
        except Exception as e:
            logging.exception(e)
