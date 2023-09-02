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

from telegram import Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, MessageHandler


def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(settings.TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("help", srv.help_command))
    application.add_handler(CommandHandler("start", srv.start))
    application.add_handler(MessageHandler(None, srv.text))
    application.add_handler(CallbackQueryHandler(srv.button))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
