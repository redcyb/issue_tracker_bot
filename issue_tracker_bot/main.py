from fastapi import FastAPI
from fastapi import Request
from telegram import Update

from issue_tracker_bot.repository import database
from issue_tracker_bot.services.telegram.bot_app_initializer import create_application

database.Base.metadata.create_all(bind=database.engine)

app = FastAPI()

ta = create_application()


@app.get("/")
async def health():
    return {"message": "ok"}


@app.post("/")
async def root(req: Request):
    async with ta:
        update = Update.de_json(await req.json(), ta.bot)
        await ta.process_update(update)

    return {"message": "accepted"}
