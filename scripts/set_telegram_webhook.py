import requests

from issue_tracker_bot import settings


def set_webhook():
    url = settings.BASE_URL + "/setWebhook"
    response = requests.get(url, params={"url": settings.WEBHOOK_URL}).json()

    if not response["ok"]:
        raise RuntimeError(response["description"])


def delete_webhook():
    url = settings.BASE_URL + "/deleteWebhook"
    response = requests.get(url).json()

    if not response["ok"]:
        raise RuntimeError(response["description"])


if __name__ == "__main__":
    # delete_webhook()
    set_webhook()
    ...
