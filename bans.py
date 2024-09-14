from datetime import datetime, timedelta
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from constants import DATETIME_FORMAT
from operations.bans import create_ban, delete_ban, get_all_bans, get_players_ban
from operations.matches import get_current_match
from utils import is_chat_admin

async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_chat_admin(update, context):
        return

    chat_id = update.effective_chat.id
    message_id = update.message.id

    if context.args and context.args[0].startswith('@'):
        player = context.args[0][1:]
    else:
        await context.bot.send_message(chat_id=chat_id, text="Please provide a valid username to ban.")
        return

    current_match = get_current_match(chat_id)[0]
    datetime_parsed = datetime.strptime(current_match['datetime'], DATETIME_FORMAT)

    ten_days = timedelta(days=10)
    banned_until = datetime_parsed + ten_days
    create_ban(player, banned_until)

    await context.bot.set_message_reaction(chat_id=chat_id, message_id=message_id, reaction="👌")

async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_chat_admin(update, context):
        return

    chat_id = update.effective_chat.id
    message_id = update.message.id

    if context.args and context.args[0].startswith('@'):
        player = context.args[0][1:]
    else:
        await context.bot.send_message(chat_id=chat_id, text="Please provide a valid username to unban.")
        return

    delete_ban(player)

    await context.bot.set_message_reaction(chat_id=chat_id, message_id=message_id, reaction="👌")

async def get_my_bans(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user.username
    chat_id = update.effective_chat.id

    bans = get_players_ban(user)

    message = f"Hello @{user}!\nHere's a list of your current bans:\n"

    if not bans:
        message += "You currently have no bans."
    else:
        for idx, ban in enumerate(bans, start=1):
            message += f"<b>Ban {idx}:</b> Expires on {ban['until']}\n"

    await context.bot.send_message(chat_id=chat_id, text=message, parse_mode=ParseMode.HTML)

async def get_all_bans_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    bans = get_all_bans()

    message = "Here's a list of all current bans:\n"

    if not bans:
        message += "There are currently no bans."
    else:
        for idx, ban in enumerate(bans, start=1):
            message += f"<b>Ban {idx} - {ban['nickname']}:</b> Expires on {ban['until']}\n"

    await context.bot.send_message(chat_id=chat_id, text=message, parse_mode=ParseMode.HTML)
