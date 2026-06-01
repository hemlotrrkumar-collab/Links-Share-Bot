# Links-Share-Bot

A Telegram bot to share protected links with auto-deletion, cloning features, and broadcast capabilities.

## Features
- **Auto-Delete Posts**: Links provided to users auto-delete after 10 seconds.
- **Auto-Delete Broadcast**: Admin broadcasts auto-delete after 8 seconds.
- **Bot Cloning**: Admins can clone the bot using a bot token.
- **Channel Link Protection**: Generate timed verification links for channels.
- **Restricted Access**: Only admins and authorized users can access the bot menu.
- **Small Caps Styling**: Beautiful small caps text and inline buttons.

## Deployment Instructions

### 1. Requirements
- Python 3.8 or higher.
- Telegram `API_ID` and `API_HASH` (get from [my.telegram.org](https://my.telegram.org)).
- Telegram `BOT_TOKEN` (get from [@BotFather](https://t.me/BotFather)).

### 2. Installation
Clone this repository and install the dependencies:
```bash
pip install -r requirements.txt
```

### 3. Environment Variables
Set the following environment variables on your server:
- `API_ID`: Your Telegram API ID.
- `API_HASH`: Your Telegram API Hash.
- `BOT_TOKEN`: Your primary Bot Token.

### 4. Run the Bot
```bash
python main.py
```

### 5. Running in Background (VPS)
Use `tmux` or `screen` to keep the bot running:
```bash
tmux new -s bot
python main.py
# Press Ctrl+B then D to detach
```