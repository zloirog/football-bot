from datetime import datetime, timedelta
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from constants import MAX_PLAYERS, CHAT_ID, reply_markup
from utils import is_chat_admin, get_hours_until_match
from register_funcs import get_message
from match_files import load_data, save_data, ban_player


async def remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    if not data:
        return

    game_id = list(data.keys())[-1]
    game = data[game_id]
    user = update.callback_query.from_user.username
    query = update.callback_query

    is_game_full = len(game['players']) == MAX_PLAYERS

    format_str = '%Y-%m-%dT%H:%M:%S'
    datetime_parsed = datetime.strptime(game['datetime'], format_str)

    hours_difference = get_hours_until_match(datetime_parsed)

    if hours_difference < 22:
        two_weeks = timedelta(weeks=2)
        banned_until = datetime_parsed + two_weeks
        ban_player(user, banned_until.isoformat())
        await context.bot.send_message(chat_id=CHAT_ID, text=f"@{user} в бан нах! You are banned until {banned_until}")

    for list_name in ["players", "waiting_list"]:
        for player in game[list_name]:
            if player['name'] == user:
                game[list_name].remove(player)
                if is_game_full and list_name == "players" and not len(game['waiting_list']) == 0:
                    game["players"].append(game['waiting_list'][0])
                    del game['waiting_list'][0]

                save_data(data)

    try:
        await query.edit_message_text(text=get_message(), reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    except Exception as error:
        print("No update", error)
        return


async def remove_plus_one(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    if not data:
        return

    game_id = list(data.keys())[-1]
    game = data[game_id]
    user = update.callback_query.from_user.username
    query = update.callback_query

    is_game_full = len(game['players']) == MAX_PLAYERS

    for list_name in ["players", "waiting_list"]:
        for player in game[list_name]:
            if player['registered_by'] == user and player['name'] == f"{user} +1":
                game[list_name].remove(player)
                if is_game_full and list_name == "players":
                    game["players"].append(game['waiting_list'][0])
                    del game['waiting_list'][0]

                save_data(data)
    try:
        await query.edit_message_text(text=get_message(), reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    except:
        print("No update")
        return


async def remove_other(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_chat_admin(update, context):
        return

    data = load_data()
    if not data:
        await update.message.reply_text("No games available.")
        return

    game_id = list(data.keys())[-1]
    game = data[game_id]

    is_game_full = len(game['players']) == MAX_PLAYERS

    if len(context.args) == 1 and context.args[0].startswith('@'):
        user = context.args[0][1:]
    else:
        await update.message.reply_text("user is not provided.")
        return

    for list_name in ["players", "waiting_list"]:
        for player in game[list_name]:
            if player['name'] == user:
                game[list_name].remove(player)
                if is_game_full and list_name == "players":
                    game["players"].append(game['waiting_list'][0])
                    del game['waiting_list'][0]

                save_data(data)
                await update.message.reply_text(f"{user} removed successfully.")
                return

    await update.message.reply_text(f"{user} is not in the list.")
