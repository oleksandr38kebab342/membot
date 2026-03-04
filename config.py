import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_USERS = [824228525]

JOKE_DAY_TIME = os.getenv("JOKE_DAY_TIME", "13:00")
TIMEZONE = os.getenv("TIMEZONE", "Europe/Kyiv")
COOLDOWN_SECONDS = int(os.getenv("COOLDOWN_SECONDS", "150"))

PROFILE_BUTTON = "Профіль"
