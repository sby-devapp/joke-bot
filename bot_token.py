# export BOT_TOKEN="7460388943:AAFpQi4XupuZBgc59eC2ibV4wh0BE1dBiGI"

import os

BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("No BOT_TOKEN set in environment variables!")

if __name__ == "__main__":
    print(f"BOT_TOKEN: {BOT_TOKEN} / is set correctly.")
