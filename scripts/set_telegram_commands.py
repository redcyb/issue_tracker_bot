import asyncio

from telegram import Bot
from telegram import BotCommand

from issue_tracker_bot import settings


if __name__ == "__main__":
    bot = Bot(token=settings.TELEGRAM_TOKEN)

    commands = [
        BotCommand(command="/start", description="Почати роботу"),
        BotCommand(
            command="/problem", description="Доповісти про проблему із пристроєм"
        ),
        BotCommand(
            command="/solution", description="Доповісти про рішення для пристрою"
        ),
        BotCommand(command="/status", description="Отримати поточний статус пристрою"),
        BotCommand(
            command="/open_problems",
            description="Отримати список усіх незакритих проблем",
        ),
        BotCommand(command="/help", description="Отримати підказу про використання"),
    ]

    asyncio.run(bot.set_my_commands(commands))
