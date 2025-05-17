# File: test.py

from bot_token import BOT_TOKEN
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from app.controllers.adding_jokes import AddingJokes


if __name__ == "__main__":

    application = Application.builder().token(BOT_TOKEN).build()
    addingjokes = AddingJokes()
    addingjokes.application = application
    addingjokes.setup_handler()

    print("Bot is running...")
    application.run_polling()
