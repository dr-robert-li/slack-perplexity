"""Kahm-pew-terr — Slack bot entry point using Bolt in Socket Mode."""
import logging
import os

from dotenv import load_dotenv

load_dotenv()

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

logging.basicConfig(level=logging.DEBUG)

app = App(token=os.environ.get("SLACK_BOT_TOKEN"))

from handlers.dm_handler import register_dm_handler
register_dm_handler(app)


# No-op handlers to silence unhandled event warnings
@app.event("app_home_opened")
def handle_app_home_opened(event, logger):
    logger.debug("app_home_opened received")



@app.event("member_joined_channel")
def handle_member_joined_channel(event, logger):
    logger.debug("member_joined_channel received")


if __name__ == "__main__":
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()
