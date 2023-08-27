import logging
import os

from flask import Blueprint
from flask import Flask
from flask import request

from issue_tracker_bot.controller import Controller
from issue_tracker_bot.settings import configure_logging

api_endpoint = Blueprint("api_endpoint", __name__)

controller = Controller()


@api_endpoint.route("/", methods=["GET", "HEAD", "OPTIONS"])
def index():
    return {"message": "test"}


@api_endpoint.route("/", methods=["POST"])
def handle_bot_request():
    message = {"message": "ok"}

    try:
        controller.process(request.json)
    except Exception:
        logging.exception("")
        message = {"message": "exception"}

    return message


def create_app(app_name="fin-bot"):
    app = Flask(app_name)
    app.secret_key = os.environ["SECRET_KEY"]
    app.register_blueprint(api_endpoint)
    return app


configure_logging()

gunicorn_app = create_app()
