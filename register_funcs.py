import json
import datetime
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, CallbackContext


async def register_old(update: Update, context: CallbackContext):
    data = load_data()
    if not data:
        await update.message.reply_text("No games available. Start a new game with /start")
        return

    chat_id = update.effective_chat.id
    game_id = list(data.keys())[-1]
    game = data[game_id]
    user = update.message.from_user.username
    now = datetime.datetime.now()
    start_time = datetime.datetime.fromisoformat(game["start_time"])
    is_plus = False
    confirmed = True
    priority = 3


    if not user:
        user = update.message.from_user.id

    can_user_register_val = can_user_register(user, game["players"] + game['waiting_list'])

    if len(context.args) == 0:
        player = user
        if (now - start_time).total_seconds() / 3600 < PRIORITY_HOURS and was_in_last_match(player):
            priority = 1
        priority = 2 if priority > 2 else priority
        if not can_user_register_val['himself']:
            await update.message.reply_text("You are already registered.")
            return

    elif context.args[0].startswith('@'):
        player = context.args[0][1:]

        if (now - start_time).total_seconds() / 3600 < PRIORITY_HOURS and was_in_last_match(player):
            priority = 1

        if len(context.args) == 2 and context.args[1] == '+1':
            is_plus = True
            priority = 3 if priority > 3 else priority
            if not can_user_register_val['plus_one']:
                await update.message.reply_text("You can't register more +1s.")
                return
        else:
            if not can_user_register_val['from_chat']:
                await update.message.reply_text("You can't register more people from the chat.")
                return

            confirmed = False
            job_data = {'name': player, 'chat_id': chat_id}
            context.job_queue.run_once(check_for_confimation, 14400, data=job_data)
            priority = 2 if priority > 2 else priority
    else:
        await update.message.reply_text("Invalid promt. User @ to tag player or type +1")
        return

    if player in [p['name'] for p in game['players'] + game['waiting_list']]:
        await update.message.reply_text(f"{player} is already registered.")
        return

    player_entry = {
        "name": player,
        "registered_by": user,
        "priority": priority,
        "is_plus": is_plus,
        "confirmed": confirmed
    }

    if len(game["players"]) < MAX_PLAYERS:
        game["players"].append(player_entry)
        game["players"] = sorted(game["players"], key=lambda x: x['priority'])
    else:
        sorted_players = sorted(game["players"], key=lambda x: x['priority'])


        insert_index = None
        for i, item in enumerate(sorted_players):
            if item["priority"] > player_entry["priority"]:
                insert_index = i
                break

        if insert_index is None:
            game["waiting_list"].append(player_entry)
        else:
            sorted_players.insert(insert_index, player_entry)
            game["waiting_list"].append(sorted_players[-1])
            del sorted_players[-1]
            game["players"] = sorted_players

    save_data(data)
    await update.message.reply_text(f"{player} registered successfully.")

async def register(update: Update, context: CallbackContext):
    data = load_data()
    if not data:
        await update.message.reply_text("No games available. Start a new game with /start")
        return


    chat_id = update.effective_chat.id
    game_id = list(data.keys())[-1]
    game = data[game_id]
    user = update.callback_query.from_user.username
    now = datetime.datetime.now()
    start_time = datetime.datetime.fromisoformat(game["start_time"])
    is_plus = False
    confirmed = True
    priority = 3

    print("register", user, now, game)

    if not user:
        user = update.callback_query.from_user.first_name

    can_user_register_val = can_user_register(user, game["players"] + game['waiting_list'])

    # if len(context.args) == 0:
    player = user
    if (now - start_time).total_seconds() / 3600 < PRIORITY_HOURS and was_in_last_match(player):
        priority = 1
    priority = 2 if priority > 2 else priority
    if not can_user_register_val['himself']:
        return

    if player in [p['name'] for p in game['players'] + game['waiting_list']]:
        return

    player_entry = {
        "name": player,
        "registered_by": user,
        "priority": priority,
        "is_plus": is_plus,
        "confirmed": confirmed
    }

    if len(game["players"]) < MAX_PLAYERS:
        game["players"].append(player_entry)
        game["players"] = sorted(game["players"], key=lambda x: x['priority'])
    else:
        sorted_players = sorted(game["players"], key=lambda x: x['priority'])

        insert_index = None
        for i, item in enumerate(sorted_players):
            if item["priority"] > player_entry["priority"]:
                insert_index = i
                break

        if insert_index is None:
            game["waiting_list"].append(player_entry)
        else:
            sorted_players.insert(insert_index, player_entry)
            game["waiting_list"].insert(0, sorted_players[-1])
            del sorted_players[-1]
            game["players"] = sorted_players

    save_data(data)
    query = update.callback_query

    try:
        await query.edit_message_text(text=get_message(), reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    except:
        print("No update")

async def register_plus_one(update: Update, context: CallbackContext):
    data = load_data()
    if not data:
        await update.message.reply_text("No games available. Start a new game with /start")
        return

    chat_id = update.effective_chat.id
    game_id = list(data.keys())[-1]
    game = data[game_id]
    user = update.callback_query.from_user.username
    now = datetime.datetime.now()
    start_time = datetime.datetime.fromisoformat(game["start_time"])
    is_plus = True
    confirmed = True
    priority = 3

    print("register", user, now, game)

    if not user:
        user = update.callback_query.from_user.first_name

    can_user_register_val = can_user_register(user, game["players"] + game['waiting_list'])

    # if len(context.args) == 0:
    player = user + " +1"
    if (now - start_time).total_seconds() / 3600 < PRIORITY_HOURS and was_in_last_match(player):
        priority = 1

    if not can_user_register_val['plus_one']:
        return

    if player in [p['name'] for p in game['players'] + game['waiting_list']]:
        return

    player_entry = {
        "name": player,
        "registered_by": user,
        "priority": priority,
        "is_plus": is_plus,
        "confirmed": confirmed
    }

    if len(game["players"]) < MAX_PLAYERS:
        game["players"].append(player_entry)
        game["players"] = sorted(game["players"], key=lambda x: x['priority'])
    else:
        sorted_players = sorted(game["players"], key=lambda x: x['priority'])


        insert_index = None
        for i, item in enumerate(sorted_players):
            if item["priority"] > player_entry["priority"]:
                insert_index = i
                break

        if insert_index is None:
            game["waiting_list"].append(player_entry)
        else:
            sorted_players.insert(insert_index, player_entry)
            game["waiting_list"].append(sorted_players[-1])
            del sorted_players[-1]
            game["players"] = sorted_players

    save_data(data)
    query = update.callback_query

    try:
        await query.edit_message_text(text=get_message(), reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    except:
        print("No update")
