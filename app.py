"""Kahm-pew-terr — Slack bot entry point using Bolt in Socket Mode."""
import logging
import os

from dotenv import load_dotenv

load_dotenv()

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO").upper())

app = App(token=os.environ.get("SLACK_BOT_TOKEN"))

from handlers.message_handler import register_message_handlers
from handlers.mention_handler import register_mention_handler
from handlers.slash_handler import register_slash_handler
from handlers.home_handler import register_home_handler

register_message_handlers(app)
register_mention_handler(app)
register_slash_handler(app)
register_home_handler(app)


# No-op handlers for subscribed events the bot doesn't act on.
# Without these, Bolt returns 404 → Slack retries → retries pile up →
# disconnect/reconnect storm that accumulates stale WebSocket connections.
@app.event("member_joined_channel")
def handle_member_joined_channel(event, logger):
    logger.debug("member_joined_channel received")


@app.event("reaction_added")
def handle_reaction_added(event, logger):
    logger.debug("reaction_added received")


@app.event("reaction_removed")
def handle_reaction_removed(event, logger):
    logger.debug("reaction_removed received")


if __name__ == "__main__":
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()
