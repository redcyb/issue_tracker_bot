# pylint: disable=wrong-import-position

"""Simple Bot to reply to Telegram messages.

This is built on the API wrapper, see echobot.py to see the same example built
on the telegram.ext bot framework.
This program is dedicated to the public domain under the CC0 license.
"""
from issue_tracker_bot import settings
from issue_tracker_bot.services.telegram import bot_service as srv

import logging

logger = logging.getLogger(__name__)

from telegram.ext import Application, CallbackQueryHandler, CommandHandler, MessageHandler


def create_application():
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    application = (
        Application.builder()
        .read_timeout(settings.TG_READ_TIMEOUT)
        .get_updates_read_timeout(settings.TG_READ_TIMEOUT)
        .connect_timeout(settings.TG_READ_TIMEOUT)
        .pool_timeout(settings.TG_READ_TIMEOUT)
        .write_timeout(settings.TG_WRITE_TIMEOUT)
        .token(settings.TELEGRAM_TOKEN).build()
    )

    application.add_handler(CommandHandler("help", srv.handle_help))
    application.add_handler(CommandHandler("start", srv.handle_start))
    application.add_handler(MessageHandler(None, srv.handle_text))
    application.add_handler(CallbackQueryHandler(srv.handle_button))

    return application


if __name__ == "__main__":
    create_application()
