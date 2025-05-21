import os

BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("No BOT_TOKEN set in environment variables!")


if __name__ == "__main__":
    print(BOT_TOKEN)
