from datetime import datetime
import pytz
from date_utils import get_hours_until_match, get_current_time
from operations.bans import delete_ban, get_players_ban
from operations.chats import get_chat_by_tg_id
from operations.match_registrations import check_if_user_played_before, check_if_user_registered, confirm_user_registration, create_match_registration, delete_match_registration, get_current_match_registrations
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import CallbackContext, ContextTypes
from constants import PRIORITY_HOURS, SQL_DATETIME_FORMAT
from operations.matches import get_current_match, was_in_last_match
from operations.users import get_all_users_from_db, get_user
from utils import get_reply_markup, is_user_in_chat, get_message

def is_player_banned(user_id):
    player_bans = get_players_ban(user_id)
    current_datetime = get_current_time()

    for ban in player_bans:
        user_date = datetime.fromisoformat(ban['until'])

        if current_datetime < user_date:
            return True

        delete_ban(ban['ban_id'])

    return False

async def check_for_confimation(context: ContextTypes.DEFAULT_TYPE):
    job_data = context.job.data
    tg_chat_id = job_data['chat_id']
    user_id = job_data['user_id']

    chat_data = get_chat_by_tg_id(tg_chat_id)

    curr_match = get_current_match(chat_data['id'])

    is_user_registered = check_if_user_registered(curr_match['match_id'], user_id)

    if is_user_registered['confirmed'] == 0:
        delete_match_registration(curr_match['match_id'], user_id)
        await context.bot.send_message(chat_id=tg_chat_id, text=f"@{is_user_registered['nickname']} did not confirm their registration!")
        return

def get_priority(user_id, reg_time, game_time, was_in_last_match, is_plus):
    now = get_current_time()
    reg_time = pytz.timezone("Europe/Prague").localize(datetime.strptime(reg_time, SQL_DATETIME_FORMAT))

    if is_player_banned(user_id):
        return 4
    if (now - reg_time).total_seconds() / 7200 < PRIORITY_HOURS and was_in_last_match:
        return 1

    hours_difference = get_hours_until_match(game_time)
    if hours_difference < 26:
        return 3

    if not check_if_user_played_before(user_id):
        return 3

    if is_plus:
        return 3


    return 2

async def register_another_from_chat(update: Update, context: CallbackContext):
    user_id = update.callback_query.from_user.id
    tg_chat_id = update.effective_chat.id
    users = get_all_users_from_db()

    message = "Here are the users who have registered in the bot click the button with the user you want to register:\n"

    keyboard = []

    for idx, user in enumerate(users, start=1):
        next_user = users[(idx) % len(users)]

        if idx % 2 != 0 and idx == len(users):
            keyboard.append([InlineKeyboardButton(f"{next_user['name']}", callback_data=f"registerplusone_{tg_chat_id}_{next_user['user_id']}")])
            continue

        if idx % 2 != 0:
            continue

        keyboard.append([InlineKeyboardButton(f"{user['name']}", callback_data=f"registerplusone_{tg_chat_id}_{user['user_id']}"),
                         InlineKeyboardButton(f"{next_user['name']}", callback_data=f"registerplusone_{tg_chat_id}_{next_user['user_id']}")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(chat_id=user_id, text=message, reply_markup=reply_markup)


def register_core(chat_id, user_id, registered_by_id, is_plus=False, confirmed=True):
    was_in_last_match_res = was_in_last_match(chat_id, user_id)

    current_match = get_current_match(chat_id)
    match_id = current_match['match_id']
    start_time = current_match['datetime']
    reg_time = current_match['created_at']

    is_user_registered = check_if_user_registered(match_id, user_id)

    if is_user_registered and is_user_registered['confirmed'] == 0:
        confirm_user_registration(match_id, user_id)
        return True

    if is_user_registered:
        return False

    hours_until_match = get_hours_until_match(current_match['datetime'])

    if hours_until_match < 0:
        return False

    priority = get_priority(user_id, reg_time, start_time, was_in_last_match_res, is_plus)
    create_result = create_match_registration(user_id, registered_by_id, is_plus, confirmed, priority, match_id)

    return create_result

async def register_himself(update: Update, context: CallbackContext):
    user_id = update.callback_query.from_user.id
    user_name = update.callback_query.from_user.username
    tg_chat_id = update.effective_chat.id

    chat_data = get_chat_by_tg_id(tg_chat_id)
    user = get_user(user_id)

    chat_id = chat_data['id']

    if not user:
        await context.bot.send_message(chat_id=tg_chat_id, text=f"@{user_name} To be able to register to the matches you need to activate me in the DM.")
        return

    res = register_core(chat_id, user_id, user_id)

    if res:
        query = update.callback_query
        await query.edit_message_text(text=get_message(chat_id), reply_markup=get_reply_markup(tg_chat_id), parse_mode=ParseMode.HTML)

    return

async def register_plus_one(update: Update, context: CallbackContext, tg_chat_id, user_id):
    request_user_id = update.callback_query.from_user.id
    user_name = update.callback_query.from_user.username

    chat_data = get_chat_by_tg_id(tg_chat_id)
    user = get_user(request_user_id)
    current_match = get_current_match(chat_data['id'])

    if not user:
        await context.bot.send_message(chat_id=tg_chat_id, text=f"@{user_name} To be able to register to the matches you need to activate me in the DM.")
        return

    user_in_chat = await is_user_in_chat(update, context, tg_chat_id, user_id)
    res = register_core(chat_data['id'], user_id=user_id, registered_by_id=request_user_id, is_plus=not user_in_chat, confirmed=False)

    if res:
        keyboard = [[InlineKeyboardButton("Confirm", callback_data=f'confirm_{tg_chat_id}')]]
        keyboard2 = [[InlineKeyboardButton("Quit", callback_data=f'removefromdm_{tg_chat_id}')]]

        reply_markup = InlineKeyboardMarkup(keyboard)

        reply_markup2 = InlineKeyboardMarkup(keyboard2)

        print(user_id)

        await context.bot.send_message(chat_id=user_id, text=f"Hey, you have been registered to the football match in CUEFA chat at {current_match['datetime']}. Confirm your registration with button below withing 4 hours.", reply_markup=reply_markup)
        await context.bot.send_message(chat_id=user_id, text="In case if you decide not to play, you can click this button and quit. Please note, if you quit less then 24 hours until the match, you may be banned.", reply_markup=reply_markup2)

        job_data = {'user_id': user_id, 'chat_id': tg_chat_id}
        context.job_queue.run_once(check_for_confimation, 14400, data=job_data)

        await context.bot.send_message(chat_id=request_user_id, text="User registered, thanks.")
    else:
        await context.bot.send_message(chat_id=request_user_id, text="You cannot register more people.")

async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE, tg_chat_id):
    user_id = update.callback_query.from_user.id
    chat_data = get_chat_by_tg_id(tg_chat_id)

    res = get_current_match(chat_data['id'])
    current_match = res
    match_id = current_match['match_id']

    confirm_user_registration(match_id, user_id)