import asyncio

from telegram import Bot
from telegram import BotCommand

from issue_tracker_bot import settings


if __name__ == "__main__":
    bot = Bot(token=settings.TELEGRAM_TOKEN)

    # fmt: off
    commands = [
        BotCommand(command="/start", description="Почати роботу"),
        BotCommand(command="/problem", description="Доповісти про проблему із пристроєм"),
        BotCommand(command="/solution", description="Доповісти про рішення для пристрою"),
        BotCommand(command="/status", description="Отримати поточний статус пристрою"),
        BotCommand(command="/open_problems", description="Отримати список усіх відкритих проблем"),
        BotCommand(command="/sync_context", description="(Адмін) Синхронізувати контекст"),
        BotCommand(command="/export_reports", description="(Адмін) Експортувати дані"),
        BotCommand(command="/help", description="Отримати підказу про використання"),
    ]
    # fmt: on

    asyncio.run(bot.set_my_commands(commands))
