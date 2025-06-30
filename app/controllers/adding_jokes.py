from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
from app.controllers.controller import Controller
from app.db.entities.joke import Joke
from app.db.entities.language import Language
from app.db.entities.tag import Tag

# States
(
    DISPLAYING_JOKE,
    ADDING_JOKE,
    EDIT_CONTENT,
    SET_CONTENT,
    EDIT_TAGS,
    SET_TAGS,
    EDIT_LANGUAGE,
    SET_LANGUAGE,
) = range(8)

BREAK_LINE = "------------------------------------------\n"

back_to_adding_joke_view_button = InlineKeyboardButton(
    "↩️ Back", callback_data="back_to_menu"
)


class AddingJokes(Controller):
    def __init__(self):
        print("Initializing AddingJokes...")

    def init_joke(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = self.get_user(update, context)
        joke = Joke()
        joke.content = "*"
        joke.language_code = "en"
        joke.status = "draft"
        joke.tags = []
        joke.add_by = user.id
        joke.load_language()
        context.user_data["joke"] = joke

        return joke

    def get_joke(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> Joke:
        if "selected_tags" not in context.user_data:
            context.user_data["selected_tags"] = []
        if "language_code" not in context.user_data:
            context.user_data["language_code"] = "en"
        if "joke" not in context.user_data:
            self.init_joke(update, context)
        elif context.user_data["joke"] == None:
            self.init_joke(update, context)

        return context.user_data["joke"]

    def formatted_joke(self, joke: Joke, status_line="") -> str:
        if status_line == "":
            if joke.id is None:
                status_line = "Adding a new Joke . . ."
            else:
                status_line = f"Editing Joke ID: {joke.id} 🤣"

        text = f"{status_line}\n{BREAK_LINE}"
        text += f"{joke.content}\n{BREAK_LINE}"
        text += f"Language: {joke.language.name or 'Not set'}\n"
        tag_names = (
            ", ".join([f"#{tag.name}" for tag in joke.tags]) if joke.tags else "None"
        )
        text += f"Tags: {tag_names}\n"
        text += f"Status: {joke.status.capitalize()}\n"
        text += BREAK_LINE
        return text

    def get_menu(self):
        keyboard = [
            [
                InlineKeyboardButton("📝 Content", callback_data="edit_content"),
                InlineKeyboardButton("🏷 Tags", callback_data="edit_tags"),
                InlineKeyboardButton("🌐 Language", callback_data="edit_language"),
            ],
            [
                InlineKeyboardButton("💾 Save", callback_data="joke_save"),
                InlineKeyboardButton("🔄 Reset", callback_data="reset"),
                InlineKeyboardButton("❌ Cancel", callback_data="cancel"),
            ],
        ]
        return InlineKeyboardMarkup(keyboard)

    async def start_adding(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.check_is_private_chat(update, context):
            return

        await self.update_temp_joke(update, context)
        return ADDING_JOKE

    async def update_temp_joke(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        if not await self.check_is_private_chat(update, context):
            return

        joke = self.get_joke(update, context)
        formatted_joke = self.formatted_joke(joke)
        try:
            if "message_id" in context.user_data:
                # Delete the last message
                await context.bot.delete_message(
                    chat_id=update.effective_chat.id,
                    message_id=context.user_data["message_id"],
                )
            # Send a new message
            if update.callback_query:
                sent_message = await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=formatted_joke,
                    reply_markup=self.get_menu(),
                )
            else:
                sent_message = await update.message.reply_text(
                    text=formatted_joke,
                    reply_markup=self.get_menu(),
                )
            context.user_data["message_id"] = sent_message.message_id
        except Exception as e:
            print(f"[ERROR] Failed to update message: {e}")

    async def edit_content(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.check_is_private_chat(update, context):
            return

        query = update.callback_query
        await query.answer()
        menu = InlineKeyboardMarkup([[back_to_adding_joke_view_button]])
        await query.edit_message_text(
            "Please enter the joke content:", reply_markup=menu
        )
        return EDIT_CONTENT

    async def set_content(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.check_is_private_chat(update, context):
            return

        joke = self.get_joke(update, context)
        joke.content = update.message.text
        await update.message.reply_text("✅ Content updated.")
        await self.update_temp_joke(update, context)
        return ADDING_JOKE

    async def back_to_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.check_is_private_chat(update, context):
            return

        await self.update_temp_joke(update, context)
        return ADDING_JOKE

    async def reset_joke(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.check_is_private_chat(update, context):
            return

        context.user_data["joke"] = Joke()
        context.user_data["joke"].status = "draft"
        await self.update_temp_joke(update, context)
        return ADDING_JOKE

    async def cancel_joke(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.check_is_private_chat(update, context):
            return

        query = update.callback_query
        await query.edit_message_text("❌ Process cancelled.")
        context.user_data["joke"] = None
        return ConversationHandler.END

    async def save_joke(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.check_is_private_chat(update, context):
            return

        joke = self.get_joke(update, context)
        min_content_len = 30
        if len(joke.content) >= min_content_len:
            joke.status = "pending"
            joke.save()
            joke.tags_save()
            await self.display_joke(update, context)
            return DISPLAYING_JOKE
        else:
            await update.callback_query.answer(
                text=f"Content is less than {min_content_len} characters",
                show_alert=True,
            )
            await self.update_temp_joke(update, context)
            return ADDING_JOKE

    async def display_joke(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.check_is_private_chat(update, context):
            return

        query = update.callback_query
        print(f"[display_joke] : data = {query.data} \n")
        if query.data.startswith("joke_display_"):
            joke_id = query.data.split("_")[2]
            joke = Joke(id=int(joke_id))
            joke.get()
            joke.load_tags()
        else:
            joke = self.get_joke(update, context)

        formatted_joke = self.formatted_joke(
            joke, status_line=f"Displaying joke ID: {joke.id} . . ."
        )
        message_id = update.callback_query.message.message_id
        context.user_data["message_id"] = message_id
        keyboard = [
            [
                InlineKeyboardButton("✏️ Edit", callback_data=f"joke_edit_{joke.id}"),
                InlineKeyboardButton(
                    "🗑 Delete", callback_data=f"joke_delete_{joke.id}"
                ),
                InlineKeyboardButton(
                    "⏳ Pending" if joke.status == "published" else "✅ Publish",
                    callback_data="toggle_status",
                ),
            ],
            [InlineKeyboardButton("❌ Close", callback_data=f"close_{message_id}")],
        ]
        menu = InlineKeyboardMarkup(keyboard)

        try:
            await query.edit_message_text(text=formatted_joke, reply_markup=menu)
        except Exception as e:
            print(f"[ERROR] Failed to display joke: {e}")

        return DISPLAYING_JOKE

    async def edit_tags(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.check_is_private_chat(update, context):
            return

        query = update.callback_query
        await query.answer()
        tags = Tag.select()
        selected_tags = context.user_data.get("selected_tags", [])
        keyboard = []
        row = []
        for tag in tags:
            if tag in selected_tags:
                row.append(
                    InlineKeyboardButton(
                        f"➖ {tag.name}", callback_data=f"set_tags_remove_{tag.id}"
                    )
                )
            else:
                row.append(
                    InlineKeyboardButton(
                        f"➕ {tag.name}", callback_data=f"set_tags_add_{tag.id}"
                    )
                )
            if len(row) == 3:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
        keyboard.append([back_to_adding_joke_view_button])
        menu = InlineKeyboardMarkup(keyboard)
        try:
            await query.edit_message_text("🏷 Select tags:", reply_markup=menu)
        except Exception as e:
            print(f"[ERROR][.edit_tags] Failed to edit message: {e}")
        return EDIT_TAGS

    async def set_tags(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.check_is_private_chat(update, context):
            return

        query = update.callback_query
        await query.answer()
        data = query.data.split("_")
        if len(data) < 4:
            await query.edit_message_text("⚠ Invalid action. Returning to main menu.")
            await self.back_to_menu(update, context)
            return ADDING_JOKE
        action = data[2]
        try:
            tag_id = int(data[3])
        except (ValueError, IndexError):
            await query.edit_message_text("⚠ Error parsing tag ID.")
            return EDIT_TAGS
        tag = Tag(id=tag_id)
        selected_tags = context.user_data.setdefault("selected_tags", [])
        if action == "add":
            if tag not in selected_tags:
                selected_tags.append(tag)
        elif action == "remove":
            if tag in selected_tags:
                selected_tags.remove(tag)
        await self.edit_tags(update, context)
        return EDIT_TAGS

    async def edit_language(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.check_is_private_chat(update, context):
            return

        query = update.callback_query
        await query.answer()
        languages = Language.select()
        keyboard = []
        row = []
        for lang in languages:
            row.append(
                InlineKeyboardButton(
                    lang.name, callback_data=f"set_language_{lang.code}"
                )
            )
            if len(row) == 3:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
        keyboard.append([back_to_adding_joke_view_button])
        menu = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("🌐 Select a language:", reply_markup=menu)
        return EDIT_LANGUAGE

    async def set_language(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.check_is_private_chat(update, context):
            return

        query = update.callback_query
        await query.answer()
        data = query.data
        lang_code = data.split("_")[2]
        context.user_data["language_code"] = lang_code
        joke = self.get_joke(update, context)
        joke.language_code = lang_code
        joke.load_language()
        await query.answer(f"✅ Language set to `{lang_code}`")
        await self.update_temp_joke(update, context)
        return ADDING_JOKE

    async def delete_joke(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.check_is_private_chat(update, context):
            return

        query = update.callback_query
        joke_id = query.data.split("_")[2]
        joke = Joke()
        joke.id = joke_id
        joke.delete()

        query = update.callback_query
        await query.edit_message_text(
            text=f"Joke was successfully deleted! If you want to add a new joke, click /addjoke."
        )
        # context.user_data.clear()
        context.user_data["joke"] = None
        return ConversationHandler.END

    async def toggle_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.check_is_private_chat(update, context):
            return

        joke = self.get_joke(update, context)

        print(
            f"[DEBUG] id:{joke.id}, add_by:{joke.add_by}, content:{joke.content}, {joke.status}, "
        )
        joke.status = "pending" if joke.status == "published" else "published"
        joke.save()
        await self.display_joke(update, context)
        return DISPLAYING_JOKE

    async def edit_joke(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.check_is_private_chat(update, context):
            return

        query = update.callback_query
        joke_id = query.data.split("_")[2]
        joke = Joke(id=int(joke_id))
        joke.get()
        joke.load_tags()

        context.user_data["joke"] = joke
        context.user_data["language_code"] = joke.language_code
        context.user_data["selected_tags"] = joke.tags
        formatted_joke = self.formatted_joke(joke)
        try:
            if "message_id" in context.user_data:
                # Delete the last message
                await context.bot.delete_message(
                    chat_id=update.effective_chat.id,
                    message_id=context.user_data["message_id"],
                )
            # Send a new message
            if update.callback_query:
                sent_message = await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=formatted_joke,
                    reply_markup=self.get_menu(),
                )
            else:
                sent_message = await update.message.reply_text(
                    text=formatted_joke,
                    reply_markup=self.get_menu(),
                )
            context.user_data["message_id"] = sent_message.message_id
        except Exception as e:
            print(f"[ERROR] Failed to update message: {e}")

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.check_is_private_chat(update, context):
            return

        query = update.callback_query
        await query.answer()
        data = query.data
        print(f"[handle_callback], data={data} .\n\n")

        if data == "edit_content":
            return await self.edit_content(update, context)
        elif data == "edit_tags":
            return await self.edit_tags(update, context)
        elif data.startswith("set_tags_"):
            return await self.set_tags(update, context)
        elif data == "edit_language":
            return await self.edit_language(update, context)
        elif data.startswith("set_language"):
            return await self.set_language(update, context)
        elif data == "back_to_menu":
            return await self.back_to_menu(update, context)
        elif data == "reset":
            return await self.reset_joke(update, context)
        elif data == "cancel":
            return await self.cancel_joke(update, context)
        elif data == "joke_save":
            return await self.save_joke(update, context)
        elif data.startswith("joke_edit_"):
            return await self.edit_joke(update, context)
        elif data.startswith("joke_delete_"):
            return await self.delete_joke(update, context)
        elif data.startswith("joke_display_"):
            return await self.display_joke(update, context)
        elif data == "toggle_status":
            return await self.toggle_status(update, context)
        elif data == "jokes_pending":
            where = ' status ="pending"'
            return self.my_jokes(update, context, where)
        elif data == "jokes_published":
            where = ' status ="published"'
            return self.my_jokes(update, context, where)
        elif data.startswith("close"):
            try:
                message_id = int(data.split("_")[1])
                chat_id = update.effective_chat.id
                context.user_data["joke"] = None
                await context.bot.edit_message_text(
                    chat_id=chat_id, message_id=message_id, text="❌ Closed."
                )
                return ConversationHandler.END
            except (IndexError, ValueError) as e:
                print(f"[ERROR] Failed to parse message ID: {e}")
                await query.edit_message_text("⚠ Error closing the message.")
                return await self.back_to_menu(update, context)
        else:
            await query.edit_message_text("⚠ Unknown action. Returning to main menu.")
            return await self.back_to_menu(update, context)

    async def my_jokes(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE, where=None
    ):
        if not await self.check_is_private_chat(update, context):
            return
        user = self.get_user(update, context)
        my_jokes = user.my_jokes(where)

        jokes_menu = [
            [
                InlineKeyboardButton("Published", callback_data="jokes_published"),
                InlineKeyboardButton("Pending", callback_data="jokes_pending"),
            ]
        ]
        for joke in my_jokes:
            jokes_menu.append(
                [
                    InlineKeyboardButton(
                        f"ID:{joke.id} | {joke.content[:50]}...",
                        callback_data=f"joke_display_{joke.id}",
                    )
                ]
            )

        menu = InlineKeyboardMarkup(jokes_menu)

        # If called from a callback query, edit the message; else, send a new one
        if update.callback_query:
            query = update.callback_query
            await query.answer()
            if len(my_jokes) == 0:
                await query.edit_message_text(
                    "You have no jokes in this category. Add one using /addjoke.",
                    reply_markup=menu,
                )
            else:
                await query.edit_message_text(
                    text="Here are your jokes:", reply_markup=menu
                )
        else:
            if len(my_jokes) == 0:
                await update.message.reply_text(
                    "You have no jokes yet. Add one using /addjoke.",
                    reply_markup=menu,
                )
            else:
                await update.message.reply_text(
                    text="Here are your jokes:", reply_markup=menu
                )

    def setup_handler(self):
        conv_handler = ConversationHandler(
            entry_points=[
                CommandHandler("addjoke", self.start_adding),
                CallbackQueryHandler(self.display_joke, pattern="^joke_display_"),
            ],
            states={
                ADDING_JOKE: [CallbackQueryHandler(self.handle_callback)],
                EDIT_CONTENT: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.set_content),
                    CallbackQueryHandler(self.back_to_menu, pattern="^back_to_menu$"),
                ],
                EDIT_TAGS: [
                    CallbackQueryHandler(self.set_tags, pattern="^set_tags_"),
                    CallbackQueryHandler(self.back_to_menu, pattern="^back_to_menu$"),
                ],
                EDIT_LANGUAGE: [
                    CallbackQueryHandler(self.set_language),
                ],
                DISPLAYING_JOKE: [
                    CallbackQueryHandler(self.handle_callback),
                    CallbackQueryHandler(self.display_joke, pattern="^joke_display_"),
                ],
            },
            fallbacks=[
                CommandHandler("cancel", self.cancel_joke),
                CallbackQueryHandler(self.cancel_joke, pattern="^cancel$"),
            ],
        )

        self.application.add_handler(conv_handler)
        self.application.add_handler(CommandHandler("jokes", self.my_jokes))
