import os

# Get these from my.telegram.org
API_ID = int(os.environ.get("API_ID", 12345))
API_HASH = os.environ.get("API_HASH", "your_api_hash")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "your_bot_token")

# Database file
DB_FILE = "database.json"

# Admin IDs (list of integers)
ADMINS = [6241315571] # You can add more here
