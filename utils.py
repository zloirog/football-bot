import json
from telegram import Update
from telegram.ext import ContextTypes, CallbackContext
from constants import reply_markup, LAST_MATCH_FILE
from telegram.constants import ParseMode
from register_funcs import get_message
from match_files import load_last_match, load_data


async def is_chat_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    # Check if the user is an admin
    chat_member = await context.bot.get_chat_member(chat_id, user_id)
    if chat_member["status"] == "administrator":
        return True
    else:
        await update.message.reply_text('Вася, гуляй! Only admins of the chat can call this function.')
        return False


async def refresh_message(update: Update, context: CallbackContext):
    query = update.callback_query
    try:
        await query.edit_message_text(text=get_message(), reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    except:
        print("No update")
        return


async def show_registration_message(update: Update, context: CallbackContext):
    if not await is_chat_admin(update, context):
        return

    chat_id = update.effective_chat.id

    sent_message = await context.bot.send_message(chat_id=chat_id, text=get_message(), reply_markup=reply_markup, parse_mode=ParseMode.HTML)


async def last_match(update: Update, context: ContextTypes.DEFAULT_TYPE):
    last_match_players = load_last_match()

    if not last_match_players:
        await update.message.reply_text("No last match data available.")
        return

    message = "<b>Last Match Players:</b>\n"
    for idx, player in enumerate(last_match_players):
        message += f"{idx + 1}. @{player['name']}\n"

    await update.message.reply_text(message, parse_mode=ParseMode.HTML)


async def save_last_match(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_chat_admin(update, context):
        return

    data = load_data()
    game_id = list(data.keys())[-1]
    game = data[game_id]
    with open(LAST_MATCH_FILE, 'w') as file:
        json.dump(game["players"], file, indent=4)
