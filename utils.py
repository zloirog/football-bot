import pytz
from operations.matches import get_last_match
from telegram import Update
from telegram.ext import ContextTypes, CallbackContext
from datetime import datetime

from constants import DATETIME_FORMAT, reply_markup
from telegram.constants import ParseMode
from register_funcs import get_message

async def is_chat_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    # Check if the user is an admin
    chat_member = await context.bot.get_chat_member(chat_id, user_id)
    if chat_member["status"] == "administrator" or chat_member["status"] == "creator":
        return True
    else:
        await update.message.reply_text('Вася, гуляй! Only admins of the chat can call this function.')
        return False


async def refresh_message(update: Update, context: CallbackContext):
    query = update.callback_query
    chat_id = update.effective_chat.id
    try:
        await query.edit_message_text(text=get_message(chat_id), reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        return
    except Exception as error:
        print(error)
        print("No update")
        return


async def show_registration_message(update: Update, context: CallbackContext):
    if not await is_chat_admin(update, context):
        return

    chat_id = update.effective_chat.id

    await context.bot.send_message(chat_id=chat_id, text=get_message(chat_id), reply_markup=reply_markup, parse_mode=ParseMode.HTML)


async def last_match(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    last_match = get_last_match(chat_id)

    if len(last_match) == 0:
        return await update.message.reply_text("No last match available", parse_mode=ParseMode.HTML)
    
    message = f"<b>Last Match Players for the game {last_match[0].datetime}:</b>\n"
    for idx, player in enumerate(last_match):
        message += f"{idx + 1}. @{player['nickname']}\n"

    await update.message.reply_text(message, parse_mode=ParseMode.HTML)

def get_hours_until_match(game_time):
    datetime_parsed = datetime.strptime(game_time, DATETIME_FORMAT)
    datetime_now = pytz.timezone("Europe/Prague").localize(datetime.now())

    time_delta = datetime_parsed - datetime_now

    hours_difference = time_delta.total_seconds() / 3600

    return hours_difference