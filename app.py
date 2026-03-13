"""Kahm-pew-terr — Slack bot entry point using Bolt in Socket Mode."""
import logging
import os

from dotenv import load_dotenv

load_dotenv()

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

logging.basicConfig(level=logging.DEBUG)

app = App(token=os.environ.get("SLACK_BOT_TOKEN"))

from handlers.message_handler import register_message_handlers
from handlers.mention_handler import register_mention_handler
register_message_handlers(app)
register_mention_handler(app)


# No-op handlers to silence unhandled event warnings
@app.event("app_home_opened")
def handle_app_home_opened(event, logger):
    logger.debug("app_home_opened received")



@app.event("member_joined_channel")
def handle_member_joined_channel(event, logger):
    logger.debug("member_joined_channel received")


if __name__ == "__main__":
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()
