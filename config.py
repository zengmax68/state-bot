from dotenv import load_dotenv
import os

load_dotenv("secrets.env")

TOKEN = os.getenv("BOT_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID", "0"))
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

if not TOKEN:
    raise SystemExit("BOT_TOKEN missing. Set BOT_TOKEN in secrets.env or environment.")
