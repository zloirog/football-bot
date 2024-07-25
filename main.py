import json
import datetime
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, CallbackContext

# Constants
DATA_FILE = 'football_matches.json'
LAST_MATCH_FILE = 'last_match.json'
MAX_PLAYERS = 14
PRIORITY_HOURS = 2


keyboard = [
    [InlineKeyboardButton("Register", callback_data='register')],
    [InlineKeyboardButton("Register ➕ 1️⃣", callback_data='register_plus_one')],
    [InlineKeyboardButton("Quit", callback_data='quit')],
    [InlineKeyboardButton("Remove ➕ 1️⃣", callback_data='remove_plus_one')],
    [InlineKeyboardButton("Refresh 🔄", callback_data='refresh_message')],

]
reply_markup = InlineKeyboardMarkup(keyboard)

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

# Load data
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as file:
            return json.load(file)
    return {}

def save_data(data):
    with open(DATA_FILE, 'w') as file:
        json.dump(data, file, indent=4)

def load_last_match():
    if os.path.exists(LAST_MATCH_FILE):
        with open(LAST_MATCH_FILE, 'r') as file:
            return json.load(file)
    return []

def can_user_register(player, players):
    himself = True
    from_chat = True
    plus_one = True
    for obj in players:
        if obj['name'] == player and obj['registered_by'] == player:
            himself = False
        if obj['name'] != player and obj['registered_by'] == player:
            from_chat = False
        if obj['registered_by'] == player and obj['is_plus'] == True:
            plus_one = False
    return {"himself": himself, "from_chat": from_chat, "plus_one": plus_one}


async def save_last_match(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_chat_admin(update, context):
        return

    data = load_data()
    game_id = list(data.keys())[-1]
    game = data[game_id]
    with open(LAST_MATCH_FILE, 'w') as file:
        json.dump(game["players"], file, indent=4)

def was_in_last_match(player):
    last_match = load_last_match()
    res = False
    for playerObj in last_match:
        if playerObj["name"] == player:
            res = True

    return res

# Commands
async def start_manually(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_chat_admin(update, context):
        return

    if len(context.args) < 2:
        await update.message.reply_text("Usage: /start <date> <time> (e.g. /start 29.6 9:30)")
        return

    game_date = context.args[0]
    game_time = context.args[1]
    game_id = f"{game_date}_{game_time.replace(':', '')}"
    message = " ".join(context.args[1: ])

    data = load_data()
    if game_id in data:
        await update.message.reply_text("Game already exists!")
        return

    data[game_id] = {
        "datetime": f"{game_date} {game_time}",
        "players": [],
        "waiting_list": [],
        "start_time": datetime.datetime.now().isoformat(),
        "message": message
    }
    save_data(data)

    await show_registration_message(update, context)

def next_saturday():
    today = datetime.datetime.now()
    # Calculate how many days until the next Saturday (Saturday is 5 in Python's weekday())
    days_until_saturday = (5 - today.weekday() + 7) % 7
    if days_until_saturday == 0:
        days_until_saturday = 7  # Ensures we get the next Saturday, not today if today is Saturday
    next_saturday_date = today + datetime.timedelta(days=days_until_saturday)
    return next_saturday_date.strftime("%d.%m.%Y")

def get_message():
    game_date = next_saturday()
    game_time = "9:30"
    message = f"Registration opened! \n{game_date} at {game_time}\n\n" + registered()
    return message

async def start(context: CallbackContext):
    data = load_data()
    game_id = list(data.keys())[-1]
    game = data[game_id]
    with open(LAST_MATCH_FILE, 'w') as file:
        json.dump(game["players"], file, indent=4)

    job_data = context.job.data
    chat_id = job_data['chat_id']
    game_date = next_saturday()
    game_time = "9:30"
    game_id = f"{game_date}_{game_time.replace(':', '')}"

    data = load_data()
    if game_id in data:
        await context.bot.send_message(chat_id=chat_id, text="Game already exists!")
        return

    data[game_id] = {
        "datetime": f"{game_date} {game_time}",
        "players": [],
        "waiting_list": [],
        "start_time": datetime.datetime.now().isoformat(),
        "message": ""
    }
    save_data(data)

    sent_message = await context.bot.send_message(chat_id=chat_id, text=f"Registration opened! \n{game_date} at {game_time}", reply_markup=reply_markup)
    await context.bot.pin_chat_message(chat_id=chat_id, message_id=sent_message.message_id)

async def show_registration_message(update: Update, context: CallbackContext):
    if not await is_chat_admin(update, context):
        return

    chat_id = update.effective_chat.id

    sent_message = await context.bot.send_message(chat_id=chat_id, text=get_message(), reply_markup=reply_markup, parse_mode=ParseMode.HTML)

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

async def confirm(update: Update, context:ContextTypes.DEFAULT_TYPE):
    data = load_data()
    if not data:
        await update.message.reply_text("No games available.")
        return

    game_id = list(data.keys())[-1]
    game = data[game_id]
    user = update.message.from_user.username

    for list_name in ["players", "waiting_list"]:
        for idx, player in enumerate(game[list_name]):
            if player['name'] == user and player['confirmed'] == False:
                player['confirmed'] = True
                save_data(data)
                await update.message.reply_text(f"{user} confirmed his registration.")
                await query.edit_message_text(text=get_message(), reply_markup=reply_markup, parse_mode=ParseMode.HTML)
                return

    await update.message.reply_text(f"{user}, buddy, you don't need to confirm anything.")

async def check_for_confimation(context:ContextTypes.DEFAULT_TYPE):
    job_data = context.job.data
    chat_id = job_data['chat_id']
    name = job_data['name']

    data = load_data()
    if not data:
        await context.bot.send_message(chat_id=chat_id, text="No games available.")
        return

    game_id = list(data.keys())[-1]
    game = data[game_id]

    for list_name in ["players", "waiting_list"]:
        for idx, player in enumerate(game[list_name]):
            if player['name'] == name and player['confirmed'] == False:
                game[list_name].remove(player)
                save_data(data)
                await context.bot.send_message(chat_id=chat_id, text=f"{name} did not confirmed his registration!")
                return


async def remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
            if player['name'] == user:
                game[list_name].remove(player)
                if is_game_full and list_name == "players" and not len(game['waiting_list']) == 0:
                    game["players"].append(game['waiting_list'][0])
                    del game['waiting_list'][0]

                save_data(data)

    try:
        await query.edit_message_text(text=get_message(), reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    except:
        print("No update")

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

async def remove_other(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_chat_admin(update, context):
        return

    data = load_data()
    if not data:
        await update.message.reply_text("No games available.")
        return

    game_id = list(data.keys())[-1]
    game = data[game_id]
    if len(context.args) == 1 and context.args[0].startswith('@'):
        user = context.args[0][1:]
    else:
         await update.message.reply_text("user is not provided.")
         return

    for list_name in ["players", "waiting_list"]:
        for player in game[list_name]:
            if player['name'] == user:
                game[list_name].remove(player)
                save_data(data)
                await update.message.reply_text(f"{user} removed successfully.")
                return

    await update.message.reply_text(f"{user} is not in the list.")

def registered():
    data = load_data()

    game_id = list(data.keys())[-1]
    game = data[game_id]

    players = sorted(game["players"], key=lambda x: x['priority'])
    waiting_list = sorted(game["waiting_list"], key=lambda x: x['priority'])

    message = "<b>Registered Players:</b>\n"
    for idx, player in enumerate(players):
        message += f"{idx + 1}. @{player['name']} (Priority {player['priority']})"
        if not player['confirmed']:
            message += "Not confirmed"
        message += "\n"

    if waiting_list:
        message += "\n<b>Waiting List:</b>\n"
        for idx, player in enumerate(waiting_list):
            message += f"{idx + 1}. @{player['name']} (Priority {player['priority']})\n"

    return message

async def last_match(update: Update, context: ContextTypes.DEFAULT_TYPE):
    last_match_players = load_last_match()

    if not last_match_players:
        await update.message.reply_text("No last match data available.")
        return

    message = "<b>Last Match Players:</b>\n"
    for idx, player in enumerate(last_match_players):
        message += f"{idx + 1}. @{player['name']}\n"

    await update.message.reply_text(message, parse_mode=ParseMode.HTML)

async def get_jobs(update: Update, context: CallbackContext):
    jobs = context.job_queue.jobs()

    s = ""
    for job in jobs:
      s += repr(job)

    await update.message.reply_text("jobs: " + s)


async def start_repeating_job(update: Update, context: CallbackContext):
    if not await is_chat_admin(update, context):
        return

    chat_id = update.effective_chat.id

    jobs = context.job_queue.jobs()

    if len(jobs) != 0:
        await update.message.reply_text('Already started in that chat.')
        return


    # Calculate time to next Wednesday at 12:00
    now = datetime.datetime.now()
    next_wednesday = now + datetime.timedelta((2 - now.weekday() + 7) % 7)  # 2 for Wednesday
    next_wednesday = datetime.datetime.combine(next_wednesday, datetime.time(10, 0))
    if next_wednesday < now:
        next_wednesday += datetime.timedelta(days=7)
    initial_delay = (next_wednesday - now).total_seconds()

    # Schedule job to run every week
    weekly_interval = 7 * 24 * 60 * 60  # 7 days in seconds

    job_data = {
        'chat_id': chat_id,
    }

    job = context.job_queue.run_repeating(
        start,
        interval=weekly_interval,
        first=initial_delay,
        data=job_data,
        name=str(chat_id)  # Using chat_id as job name
    )
    context.chat_data['job'] = job

async def stop_repeating_job(update: Update, context: CallbackContext):
    if not await is_chat_admin(update, context):
        return
    job = context.chat_data.get('job')
    if job:
        job.schedule_removal()
        await update.message.reply_text("Bot stopped.")
    else:
        await update.message.reply_text("No recurrent messages are currently scheduled.")


async def info(update: Update, context: CallbackContext):
        await update.message.reply_text("""Запись проходит автоматически каждую среду в 12 часов дня.
- Что бы зарегистрировать своего другана из чата который, например, занят, нужно написать `/register @druzhok` (druzhok надо заменить на ник своего товарища)
- Твой дружок должен будет в течении следующих трех часов подтвердить запись написав в чат `/confirm` иначе дружок с тобой на футбол не пойдет.
- `/last_match` покажет кто играл в прошлой игре

Остальное не важно, и почитай регламент в файлах.
                              """)

async def refresh_message(update: Update, context: CallbackContext):
    query = update.callback_query
    try:
        await query.edit_message_text(text=get_message(), reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    except:
        print("No update")


# Main function
def main():
    application = Application.builder().token("7254318229:AAGeSF-EJQf7ZZThsRFlecG0fXuzwjk1vWU").build()

    application.add_handler(CommandHandler("start", start_repeating_job))
    application.add_handler(CommandHandler("stop", stop_repeating_job))
    application.add_handler(CommandHandler("start_manually", start_manually))

    application.add_handler(CommandHandler("info", start_manually))

    application.add_handler(CommandHandler("show_registration_message", show_registration_message))

    application.add_handler(CommandHandler("register", register_old))
    application.add_handler(CommandHandler("quit", remove))
    application.add_handler(CommandHandler("last_match", last_match))
    application.add_handler(CommandHandler("save_last_match", save_last_match))
    application.add_handler(CommandHandler("remove_other", remove_other))
    application.add_handler(CommandHandler("confirm", confirm))
    application.add_handler(CommandHandler("get_jobs", get_jobs))


    callback_mapping = {
        'register': register,
        'register_plus_one': register_plus_one,
        'quit': remove,
        'refresh_message': refresh_message,
        'remove_plus_one': remove_plus_one
    }

    async def callback_query_handler(update: Update, context: CallbackContext) -> None:
        query = update.callback_query
        # Get the callback data
        data = query.data
        # Call the corresponding function
        if data in callback_mapping:
           await callback_mapping[data](update, context)

    application.add_handler(CallbackQueryHandler(callback_query_handler))

    now = datetime.datetime.now()
    next_wednesday = now + datetime.timedelta((2 - now.weekday() + 7) % 7)  # 2 for Wednesday
    next_wednesday = datetime.datetime.combine(next_wednesday, datetime.time(10, 0))
    if next_wednesday < now:
        next_wednesday += datetime.timedelta(days=7)
    initial_delay = (next_wednesday - now).total_seconds()

    # Schedule job to run every week
    weekly_interval = 7 * 24 * 60 * 60  # 7 days in seconds

    chat_id = "-1001198949892"

    job_data = {
        'chat_id': chat_id,
    }

    application.job_queue.run_repeating(
        start,
        interval=weekly_interval,
        first=initial_delay,
        data=job_data,
        name=str(chat_id)
    )

    application.run_polling()
    application.idle()

if __name__ == '__main__':
    main()
