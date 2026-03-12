"""Kahm-pew-terr — Slack bot entry point using Bolt in Socket Mode."""
import os

from dotenv import load_dotenv

load_dotenv()

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

app = App(token=os.environ.get("SLACK_BOT_TOKEN"))

from handlers.dm_handler import register_dm_handler
register_dm_handler(app)

if __name__ == "__main__":
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()
