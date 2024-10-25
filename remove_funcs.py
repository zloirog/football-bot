from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ContextTypes
from constants import DATETIME_FORMAT
from date_utils import get_hours_until_match
from operations.bans import create_ban
from operations.chats import get_chat_by_tg_id
from operations.match_registrations import delete_match_plus_one_registration, delete_match_registration
from operations.matches import get_current_match
from operations.users import get_user, get_user_by_nickname
from utils import is_chat_admin
from bans import ban_func

async def remove_from_dm(update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id):
    user_id = update.callback_query.from_user.id
    query = update.callback_query

    current_match = get_current_match(chat_id)

    datetime_parsed = datetime.strptime(current_match['datetime'], DATETIME_FORMAT)

    hours_difference = get_hours_until_match(current_match['datetime'])

    if hours_difference < 20:
        ten_days = timedelta(days=10)
        banned_until = datetime_parsed + ten_days
        create_ban(user_id, banned_until)
        user = get_user(user_id)
        await context.bot.send_message(chat_id=chat_id, text=f"@{user['nickname']} - {user['name']}, you've been banned until {banned_until} for cancelling your registration too close to the match.")

    delete_match_registration(current_match['match_id'], user_id)

    try:
        await query.edit_message_text(text="Thank you for the confirmation.")
    except Exception as error:
        print("Error!", error)
        return

async def remove_plus_one(update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id):
    user_id = update.callback_query.from_user.id
    current_match = get_current_match(chat_id)

    hours_difference = get_hours_until_match(current_match['datetime'])

    user = get_user(user_id)

    if hours_difference < 22:
        ban_func(chat_id, user_id)
        await context.bot.send_message(chat_id=chat_id, text=f"@{user['nickname']} - {user['name']}, your plus one has been banned as it was removed less than 20 hours before the match.")

    removed_user_id = delete_match_plus_one_registration(current_match['match_id'], user_id)

    try:
        await context.bot.send_message(chat_id=removed_user_id, text=f"You have been removed from the match registration by @{user['nickname']} - {user['name']}")
    except Exception as error:
        print("Error: ", error)
        return

async def remove_other(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_chat_admin(update, context):
        return

    tg_chat_id = update.effective_chat.id
    chat = get_chat_by_tg_id(tg_chat_id)

    current_match = get_current_match(chat['id'])
    message_id = update.message.id

    if len(context.args) == 1 and context.args[0].startswith('@'):
        user_nickname = context.args[0][1:]
        user = get_user_by_nickname(user_nickname)
        if not user:
            await context.bot.send_message(chat_id=tg_chat_id, text="This user is not registered in bot.")
    else:
        await update.message.reply_text("No user was provided.")
        return

    delete_match_registration(current_match['match_id'], user['user_id'])

    await context.bot.set_message_reaction(chat_id=tg_chat_id, message_id=message_id, reaction="👌")

async def remove_other_plus_one(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_chat_admin(update, context):
        return

    tg_chat_id = update.effective_chat.id
    chat = get_chat_by_tg_id(tg_chat_id)

    current_match = get_current_match(chat['id'])
    message_id = update.message.id

    if len(context.args) == 1 and context.args[0].startswith('@'):
        user_nickname = context.args[0][1:]
        user = get_user_by_nickname(user_nickname)
        if not user:
            await context.bot.send_message(chat_id=tg_chat_id, text="This user is not registered in bot.")
    else:
        await update.message.reply_text("No user was provided.")
        return

    delete_match_plus_one_registration(current_match['match_id'], user['user_id'])

    await context.bot.set_message_reaction(chat_id=tg_chat_id, message_id=message_id, reaction="👌")
