import json
import datetime
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, CallbackContext
from match_files import load_data, save_data, load_last_match, save_last_match
from date_utils import next_saturday
from register_funcs import register, register_old, register_plus_one
from remove_funcs import remove, remove_plus_one, remove_other
from jobs_funcs import get_jobs, start_repeating_job, stop_repeating_job

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

def get_message():
    game_date = next_saturday()
    message = f"Registration opened! \n{game_date.strftime("%d.%m.%Y %H:%M")}\n\n" + registered()
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
    game_id = game_date.strftime("%d.%m.%Y_%H_%M")

    data = load_data()
    if game_id in data:
        await context.bot.send_message(chat_id=chat_id, text="Game already exists!")
        return

    data[game_id] = {
        "datetime": game_date,
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
    application = Application.builder().token(os.getenv('TG_TOKEN')).build()

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
