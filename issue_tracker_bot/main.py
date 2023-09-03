from fastapi import FastAPI, Request

from telegram import Update

from issue_tracker_bot.bot_controller import create_application

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
