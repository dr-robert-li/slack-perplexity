# Kahm-pew-terr

A Slack bot that answers questions using Perplexity AI with cited sources. DM it or @mention it in any channel — get a researched answer with clickable citations.

## How it works

1. DM the bot or @mention it in a channel with a question
2. It replies with "Searching..." in a thread
3. Perplexity AI searches the web and generates a cited answer
4. The loading message updates in-place with the full response
5. Markdown is automatically converted to Slack-native formatting
6. Citations appear as clickable Slack links at the bottom

## Setup

### Prerequisites

- Python 3.10+
- A [Perplexity API key](https://docs.perplexity.ai/)
- A Slack workspace where you can install apps

### 1. Create the Slack App

1. Go to [api.slack.com/apps](https://api.slack.com/apps) and click **Create New App**
2. Select **From scratch**
3. Name the app (e.g. "Kahm-pew-terr") and select your workspace
4. Click **Create App**

### 2. Enable Socket Mode

1. In the left sidebar, click **Socket Mode**
2. Toggle **Enable Socket Mode** to ON
3. When prompted, create an App-Level Token:
   - Name: `socket-mode-token`
   - Scope: `connections:write`
   - Click **Generate**
4. Copy the `xapp-...` token — this is your `SLACK_APP_TOKEN`

### 3. Subscribe to Bot Events

1. In the left sidebar, click **Event Subscriptions**
2. Toggle **Enable Events** to ON
3. Expand **Subscribe to bot events** and add:
   - `message.im` — DMs to the bot
   - `app_mention` — @mentions in channels
   - `app_home_opened` — Home tab visits (future use)
   - `message.channels` — messages in public channels (future use)
   - `message.groups` — messages in private channels (future use)
   - `member_joined_channel` — channel join events (future use)
4. Click **Save Changes**

### 4. Add OAuth Scopes

1. In the left sidebar, click **OAuth & Permissions**
2. Under **Bot Token Scopes**, add:

   | Scope | Purpose |
   |-------|---------|
   | `chat:write` | Send and update messages |
   | `im:history` | Read DM message history |
   | `im:read` | View DM metadata |
   | `im:write` | Open and manage DMs |
   | `channels:history` | Read public channel messages |
   | `groups:history` | Read private channel messages |
   | `reactions:read` | Read emoji reactions (future use) |

### 5. Install to Workspace

1. In the left sidebar, click **Install App**
2. Click **Install to Workspace**
3. Review the permissions and click **Allow**
4. Copy the `xoxb-...` token — this is your `SLACK_BOT_TOKEN`

> **Note:** If you add or change scopes later, you must reinstall the app for the changes to take effect.

### 6. Install Dependencies & Run

```bash
# Clone the repo
git clone <repo-url>
cd slack-computer

# Install Python dependencies
pip install -r requirements.txt

# Create your .env file from the template
cp .env.example .env
```

Edit `.env` with your credentials:

```
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_APP_TOKEN=xapp-your-app-token
PERPLEXITY_API_KEY=pplx-your-api-key
```

Start the bot:

```bash
python app.py
```

You should see `Bolt app is running!` — the bot is now live.

### 7. Test It

- **DM:** Open a direct message with the bot and type a question
- **Channel:** Invite the bot to a channel, then `@Kahm-pew-terr your question here`

## Project Structure

```
├── app.py                  # Entry point — Bolt app with Socket Mode
├── handlers/
│   └── dm_handler.py       # DM and @mention handlers
├── services/
│   └── perplexity.py       # Perplexity API client with citation extraction
├── utils/
│   └── formatting.py       # Slack mrkdwn formatter and message splitter
├── tests/
│   ├── conftest.py         # Shared pytest fixtures
│   ├── test_app.py
│   ├── test_dm_handler.py
│   ├── test_formatting.py
│   └── test_perplexity_service.py
├── requirements.txt
└── .env.example
```

## Testing

```bash
pytest
```

## License

[MIT](LICENSE)
