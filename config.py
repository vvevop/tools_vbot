import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

BOT_VERSION = "0.0.0"

if not BOT_TOKEN:
    raise ValueError("Переменная BOT_TOKEN не установлена в файле .env!")

X0_UPLOAD_URL = "https://x0.at/"
