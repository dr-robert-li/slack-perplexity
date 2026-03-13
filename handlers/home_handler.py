"""App Home tab handler — publishes a Block Kit view to the user's Home tab."""

import os

ADMIN_UID = os.environ.get("ADMIN_UID", "")


def handle_app_home_opened(client, event: dict, logger) -> None:
    """Publish the App Home view when a user opens the bot's Home tab."""
    user_id = event["user"]
    view = {
        "type": "home",
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "Kahm-pew-terr",
                    "emoji": True,
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        "*Your AI research assistant.*\n"
                        "Ask me anything and I'll search the web for a source-cited answer."
                    ),
                },
            },
            {"type": "divider"},
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        "*How to use me:*\n"
                        "• *DM* — Send me a direct message with your question.\n"
                        "• *@mention in a channel* — @mention me in any channel with your question.\n"
                        "• */ask command* — Run `/ask <your question>` from any channel for a visible reply.\n"
                        "• *@mention in a group DM* — Add me to a group DM and @mention me with your question."
                    ),
                },
            },
            {"type": "divider"},
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Issues? Contact <@{ADMIN_UID}>",
                },
            },
        ],
    }

    try:
        client.views_publish(user_id=user_id, view=view)
    except Exception as exc:
        logger.error("Failed to publish App Home view for user %s: %s", user_id, exc)


def register_home_handler(app) -> None:
    """Register the app_home_opened event handler with the Bolt app."""
    app.event("app_home_opened")(handle_app_home_opened)
