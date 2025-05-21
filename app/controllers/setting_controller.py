import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    CallbackQueryHandler,
)
from app.controllers.controller import Controller
from app.db.db_manager import DBManager
from app.db.entities.setting import Setting
from app.db.entities.tag import Tag

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class SettingController(Controller):
    """
    Handles all operations related to chat settings.
    """

    def __init__(self):
        logger.info("Initializing SettingsController...")
        self.db = DBManager()

    async def handle_settings_command(self, update, context):
        """
        Displays the current settings for the chat and provides buttons to edit them.
        """
        if not await self.is_user_admin_or_owner(update, context):
            await update.message.reply_text(
                "You are not authorized to change the bot settings. only admins or owners can do this."
            )
            return

        # Get the chat object
        chat = self.get_chat(update=update, context=context)
        if not chat:
            return  # Exit if chat retrieval fails

        setting = Setting(chat_id=chat.id)
        setting.load()  # Load the latest settings from the database
        if not setting.is_exists():
            await self.send_error_message(
                update, "Failed to load settings for this chat."
            )
            return

        # Format the settings into a readable message
        settings_message = (
            f"⚙️ Settings for Chat ID {chat.id}:\n"
            f"🌐 Preferred Language: {setting.preferred_language}\n"
            f"⏰ Joke-Sending Schedule: {int(int(setting.schedule)/60)} minutes\n"
            f"✅ Joke-Sending Enabled: {setting.sending_jokes}\n"
            f"🗑️ Delete Last Joke: {setting.delete_last_joke}\n"
            f"🏷️ Preferred Tags: {', '.join([tag[1] for tag in setting.preferred_tags]) or 'None'}\n"
        )

        # Create an inline keyboard for editing settings
        keyboard = [
            [
                InlineKeyboardButton(
                    "Change Preferred Language", callback_data="edit_preferred_language"
                )
            ],
            [
                InlineKeyboardButton(
                    "Set Joke-Sending Schedule", callback_data="edit_schedule"
                )
            ],
            [
                InlineKeyboardButton(
                    "Toggle Delete Last Joke", callback_data="toggle_delete_last_joke"
                )
            ],
            [
                InlineKeyboardButton(
                    "Manage Preferred Tags", callback_data="manage_preferred_tags"
                )
            ],
            [
                InlineKeyboardButton(
                    "Reset Settings to Default", callback_data="reset_settings"
                )
            ],
            [InlineKeyboardButton("Close", callback_data="close_settings")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Send the settings message
        if update.message:
            await update.message.reply_text(settings_message, reply_markup=reply_markup)
        elif update.callback_query:
            await update.callback_query.edit_message_text(
                settings_message, reply_markup=reply_markup
            )

    async def handle_callback_query(self, update, context):
        """
        Handles callback queries for editing settings.
        """
        if not await self.is_user_admin_or_owner(update, context):
            await update.message.reply_text(
                "You are not authorized to change the bot Settings. only admins or owners can do this."
            )
            return

        query = update.callback_query
        if query:
            await query.answer()
            chat_id = query.message.chat_id
        else:
            chat_id = update.effective_chat.id

        setting = Setting(chat_id=chat_id)
        setting.load()  # Ensure the latest settings are loaded
        if not setting.is_exists():
            await self.send_error_message(update, "Settings not found for this chat.")
            return

        logger.info(
            f"Chat ID: {chat_id}, Setting: {setting}, Data: {query.data if query else 'Unknown'}"
        )

        # Handle specific callback actions
        if query:
            if query.data == "edit_preferred_language":
                await self._edit_preferred_language(update, setting)
            elif query.data == "edit_schedule":
                await self._edit_schedule(update, setting)
            elif query.data.startswith("set_schedule_"):
                await self._set_schedule(
                    setting=setting, update=update, context=context
                )
            elif query.data.startswith("set_language_"):
                await self._set_preferred_language(update, setting)
            elif query.data == "toggle_delete_last_joke":
                await self._edit_toggle_delete_last_joke(update, context)
            elif query.data == "toggle_delete_last_joke_yes":
                setting.delete_last_joke = "yes"
                setting.save()
                await query.edit_message_text(
                    "Delete last joke setting updated to: ✅ Yes"
                )
                await self.handle_settings_command(
                    update, context
                )  # Return to the main settings menu:
            elif query.data == "toggle_delete_last_joke_no":
                setting.delete_last_joke = "no"
                setting.save()
                await query.edit_message_text(
                    "Delete last joke setting updated to: ❌ No"
                )
                await self.handle_settings_command(
                    update, context
                )  # Return to the main settings menu:
            elif query.data == "manage_preferred_tags":
                await self._manage_preferred_tags(update, setting)
            elif query.data.startswith("add_tag_"):
                await self._add_preferred_tag(update, setting)
            elif query.data.startswith("remove_tag_"):
                await self._remove_preferred_tag(update, setting)
            elif query.data == "reset_settings":
                await self._reset_settings(update, setting)
            elif query.data == "return_to_settings":
                await self.handle_settings_command(update, context)
            elif query.data == "close_settings":
                await query.edit_message_text("Settings menu closed.")
            elif query.data.startswith("react_"):
                await self.react_to_joke(update, context)
            else:
                await query.answer("Unknown action. Please try again.")

    async def _edit_preferred_language(self, update, setting):
        """
        Allows the user to select a preferred language from available options.
        """
        languages = self.db.fetch_all("SELECT code, name FROM languages")
        if not languages:
            await self.send_error_message(
                update, "No languages available in the database."
            )
            return

        keyboard = [
            [InlineKeyboardButton(name, callback_data=f"set_language_{code}")]
            for code, name in languages
        ]
        keyboard.append(
            [
                InlineKeyboardButton(
                    "Return to Settings", callback_data="return_to_settings"
                )
            ]
        )
        reply_markup = InlineKeyboardMarkup(keyboard)

        if update.callback_query:
            await update.callback_query.edit_message_text(
                "Select your preferred language:", reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                "Select your preferred language:", reply_markup=reply_markup
            )

    async def _set_preferred_language(self, update, setting):
        """
        Updates the preferred language in the database.
        """
        query = update.callback_query
        data_parts = query.data.split("_")
        if len(data_parts) < 3:
            await query.edit_message_text(
                "Invalid language selection. Please try again."
            )
            return

        new_language_code = data_parts[-1]
        setting.preferred_language = new_language_code
        setting.save()

        await query.edit_message_text(
            f"Preferred language updated to: {new_language_code}"
        )
        await self.handle_settings_command(
            update, None
        )  # Return to the main settings menu

    async def _edit_schedule(self, update, setting):
        """
        Allows the user to set the joke-sending schedule.
        """
        intervals = [10, 20, 30, 40, 50, 60]
        # Create the keyboard with 3 buttons per row
        keyboard = [
            [
                InlineKeyboardButton(
                    f"{i} Minutes", callback_data=f"set_schedule_{i * 60}"
                )
                for i in intervals[j : j + 3]  # Group buttons in sets of 3
            ]
            for j in range(0, len(intervals), 3)
        ]
        keyboard.append(
            [
                InlineKeyboardButton(
                    "Return to Settings", callback_data="return_to_settings"
                )
            ]
        )
        reply_markup = InlineKeyboardMarkup(keyboard)

        if update.callback_query:
            await update.callback_query.edit_message_text(
                "Set Joke-Sending Schedule:", reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                "Set Joke-Sending Schedule:", reply_markup=reply_markup
            )

    async def _set_schedule(self, setting, update, context):
        """
        Updates the joke-sending schedule in the database.
        """
        query = update.callback_query
        data_parts = query.data.split("_")
        if len(data_parts) < 3 or not data_parts[-1].isdigit():
            await query.edit_message_text("Invalid schedule value. Please try again.")
            return

        new_schedule = int(data_parts[-1])
        if new_schedule <= 0:
            await query.edit_message_text(
                "Schedule must be a positive number. Please try again."
            )
            return

        setting.schedule = new_schedule
        setting.save()

        message = (
            f"Joke-sending schedule updated to: {int(int(setting.schedule)/60)} minutes"
        )
        await self.handle_settings_command(
            update, context=context
        )  # Return to the main settings menu
        await query.answer(message)
        logger.info(message)

    async def _toggle_setting(self, update, setting, setting_name):
        """
        Toggles a boolean setting (e.g., sending_jokes, delete_last_joke).
        """
        valid_settings = ["sending_jokes", "delete_last_joke"]
        if setting_name not in valid_settings:
            await self.send_error_message(update, f"Invalid setting: {setting_name}")
            return

        current_value = getattr(setting, setting_name, None)
        if current_value is None:
            await self.send_error_message(
                update, f"Setting '{setting_name}' not found."
            )
            return

        new_value = "on" if current_value == "off" else "off"
        setattr(setting, setting_name, new_value)
        setting.save()

        query = update.callback_query
        await query.edit_message_text(
            f"{setting_name.replace('_', ' ').title()} toggled to: {new_value}"
        )
        await self.handle_settings_command(
            update, None
        )  # Return to the main settings menu

    async def _manage_preferred_tags(self, update, setting):
        """
        Allows the user to add or remove preferred tags.
        Displays a grid of buttons with symbols for Add (➕) and Remove (➖).
        """
        # Fetch all available tags from the database
        all_tags = Tag().get_all_tags()
        if not all_tags:
            await self.send_error_message(update, "No tags available in the database.")
            return

        keyboard = []
        row = []  # Temporary list to hold buttons for the current row

        for tag in all_tags:
            # Determine the button text and callback data
            if (tag.id, tag.name) in setting.preferred_tags:
                button_text = f"➖ {tag.name}"  # Use "➖" for Remove
                callback_data = f"remove_tag_{tag.id}"
            else:
                button_text = f"➕ {tag.name}"  # Use "➕" for Add
                callback_data = f"add_tag_{tag.id}"

            # Add the button to the current row
            row.append(InlineKeyboardButton(button_text, callback_data=callback_data))

            # If the row has 3 buttons, add it to the keyboard and start a new row
            if len(row) == 3:  # Change to 4 if you want 4 buttons per row
                keyboard.append(row)
                row = []

        # Add any remaining buttons in the last row (if not empty)
        if row:
            keyboard.append(row)

        # Add the "Return to Settings" button as a separate row
        keyboard.append(
            [
                InlineKeyboardButton(
                    "↩️ Return to Settings", callback_data="return_to_settings"
                )
            ]
        )

        # Create the reply markup
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Send or edit the message with the inline keyboard
        if update.callback_query:
            await update.callback_query.edit_message_text(
                "Manage Preferred Tags:", reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                "Manage Preferred Tags:", reply_markup=reply_markup
            )

    async def _add_preferred_tag(self, update, setting):
        """
        Adds a tag to the preferred_tags list.
        """
        query = update.callback_query
        data_parts = query.data.split("_")
        if len(data_parts) < 3 or not data_parts[-1].isdigit():
            await query.edit_message_text("Invalid tag selection. Please try again.")
            return

        tag_id = int(data_parts[-1])
        setting.add_preferred_tag(tag_id)

        await query.edit_message_text("Tag added to preferred tags.")
        await self._manage_preferred_tags(
            update, setting
        )  # Refresh the tag management menu

    async def _remove_preferred_tag(self, update, setting):
        """
        Removes a tag from the preferred_tags list.
        """
        query = update.callback_query
        data_parts = query.data.split("_")
        if len(data_parts) < 3 or not data_parts[-1].isdigit():
            await query.edit_message_text("Invalid tag selection. Please try again.")
            return

        tag_id = int(data_parts[-1])
        setting.remove_preferred_tag(tag_id)

        await query.edit_message_text("Tag removed from preferred tags.")
        await self._manage_preferred_tags(
            update, setting
        )  # Refresh the tag management menu

    async def _reset_settings(self, update, setting):
        """
        Resets all settings to their default values.
        """
        setting.reset_settings()

        query = update.callback_query
        await query.edit_message_text(
            "All settings have been reset to their default values."
        )
        await self.handle_settings_command(
            update, None
        )  # Return to the main settings menu

    async def _edit_toggle_delete_last_joke(self, update, context):
        """
        Displays an inline keyboard to toggle the 'delete_last_joke' setting.
        """
        # Get the chat object and load the latest settings
        chat = self.get_chat(update=update, context=context)
        if not chat:
            await self.send_error_message(
                update, "Failed to retrieve chat information."
            )
            return

        setting = Setting(chat_id=chat.id)
        setting.load()  # Load the latest settings from the database
        if not setting.is_exists():
            await self.send_error_message(update, "Settings not found for this chat.")
            return

        # Determine the current state of delete_last_joke
        current_state = setting.delete_last_joke

        # Create the inline keyboard with "Yes" and "No" buttons
        keyboard = [
            [
                InlineKeyboardButton(
                    "Yes ✅" if current_state == "no" else "Yes",
                    callback_data="toggle_delete_last_joke_yes",
                ),
                InlineKeyboardButton(
                    "No ❌" if current_state == "yes" else "No",
                    callback_data="toggle_delete_last_joke_no",
                ),
            ],
            [
                InlineKeyboardButton(
                    "Return to Settings", callback_data="return_to_settings"
                )
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Determine the message text based on the current state
        message_text = (
            "Do you want to delete the last joke before sending a new one?\n\n"
            f"Current Setting: {'✅ Yes' if current_state == 'yes' else '❌ No'}"
        )

        # Send or edit the message with the inline keyboard
        if update.callback_query:
            await update.callback_query.edit_message_text(
                message_text, reply_markup=reply_markup
            )
        elif update.message:
            await update.message.reply_text(message_text, reply_markup=reply_markup)

    def setup_handler(self):
        self.application.add_handler(
            CommandHandler("settings", self.handle_settings_command)
        )

        self.application.add_handler(CallbackQueryHandler(self.handle_callback_query))
