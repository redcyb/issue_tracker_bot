# pylint: disable=wrong-import-position
import logging

from issue_tracker_bot import settings
from issue_tracker_bot.services.telegram import bot_service as srv

logger = logging.getLogger(__name__)

from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
)


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
        .token(settings.TELEGRAM_TOKEN)
        .build()
    )

    # fmt: off
    application.add_handler(CommandHandler("help", srv.handle_help))
    application.add_handler(CommandHandler("start", srv.handle_start))
    application.add_handler(CommandHandler("problem", srv.handle_init_problem_request))
    application.add_handler(CommandHandler("solution", srv.handle_init_solution_request))
    application.add_handler(CommandHandler("open_problems", srv.handle_open_problems_request))
    application.add_handler(CommandHandler("sync_context", srv.handle_sync_context_request))
    application.add_handler(CommandHandler("export_reports", srv.handle_export_reports_request))
    application.add_handler(CommandHandler("status", srv.handle_init_status_request))
    application.add_handler(CallbackQueryHandler(srv.handle_button))
    application.add_handler(MessageHandler(None, srv.handle_text))
    # fmt: on

    return application


if __name__ == "__main__":
    create_application()
