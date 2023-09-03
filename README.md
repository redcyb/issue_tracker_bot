# issue_tracker_bot

### To run the app locally prepare an .env file and fill it with key-value pairs
```dotenv
TELEGRAM_TOKEN=<SOME-STR>
WEBHOOK_URL=<SOME-STR>
HOST_URL=http://localhost:5000
SECRET_KEY=<SOME-STR>
OAUTHLIB_RELAX_TOKEN_SCOPE=1
GOOGLE_APPLICATION_CREDENTIALS=credentials_sa.json
FOLDER_ID=<SOME-STR>
LOG_LEVEL=DEBUG
```

prepare `authorized_ids.json` and `credentials.json` and put them into `secrets` dir in the repo root. 

then run

```bash
gunicorn issue_tracker_bot.main:gunicorn_app
```
