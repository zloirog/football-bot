from datetime import datetime, timedelta
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from constants import DATETIME_FORMAT, reply_markup
from date_utils import get_hours_until_match
from operations.bans import create_ban
from operations.match_registrations import delete_match_plus_one_registration, delete_match_registration, get_current_match_registrations
from operations.matches import get_current_match
from utils import is_chat_admin
from register_funcs import get_message

async def remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.callback_query.from_user.username
    chat_id = update.effective_chat.id
    query = update.callback_query

    current_match = get_current_match_registrations(chat_id)[0]

    datetime_parsed = datetime.strptime(current_match['datetime'], DATETIME_FORMAT)

    hours_difference = get_hours_until_match(current_match['datetime'])

    if hours_difference < 20:
        ten_days = timedelta(days=10)
        banned_until = datetime_parsed + ten_days
        create_ban(user, banned_until)
        await context.bot.send_message(chat_id, text=f"@{user}, you've been banned until {banned_until} for cancelling your registration too close to the match.")

    delete_match_registration(current_match['match_id'], user)

    try:
        await query.edit_message_text(text=get_message(chat_id), reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    except Exception as error:
        print("No update", error)
        return

async def remove_plus_one(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.callback_query.from_user.username
    chat_id = update.effective_chat.id
    query = update.callback_query

    current_match = get_current_match_registrations(chat_id)[0]

    hours_difference = get_hours_until_match(current_match['datetime'])

    if hours_difference < 22:
        await context.bot.send_message(chat_id, text=f"@{user}, your plus one has been removed as it was cancelled less than 20 hours before the match.")

    delete_match_plus_one_registration(current_match['match_id'], user)

    try:
        await query.edit_message_text(text=get_message(chat_id), reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    except Exception as error:
        print("No update", error)
        return

async def remove_other(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_chat_admin(update, context):
        return

    chat_id = update.effective_chat.id
    current_match = get_current_match(chat_id)[0]
    message_id = update.message.id

    if len(context.args) == 1 and context.args[0].startswith('@'):
        user = context.args[0][1:]
    else:
        await update.message.reply_text("No user was provided.")
        return

    delete_match_registration(current_match['match_id'], user)

    await context.bot.set_message_reaction(chat_id=chat_id, message_id=message_id, reaction="👌")

async def remove_other_plus_one(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_chat_admin(update, context):
        return

    chat_id = update.effective_chat.id
    current_match = get_current_match(chat_id)[0]
    message_id = update.message.id

    if len(context.args) == 1 and context.args[0].startswith('@'):
        user = context.args[0][1:]
    else:
        await update.message.reply_text("No user was provided.")
        return

    delete_match_plus_one_registration(current_match['match_id'], user)

    await context.bot.set_message_reaction(chat_id=chat_id, message_id=message_id, reaction="👌")
