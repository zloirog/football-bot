from datetime import datetime
import pytz
from date_utils import get_hours_until_match, get_current_time
from operations.bans import delete_ban, get_players_ban
from operations.match_registrations import check_if_user_registered, confirm_user_registration, create_match_registration, delete_match_registration, get_current_match_registrations
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CallbackContext, ContextTypes
from constants import DATETIME_FORMAT, PRIORITY_HOURS, SQL_DATETIME_FORMAT, reply_markup
from operations.matches import get_current_match, was_in_last_match
from operations.users import get_user, get_user_by_nickname

def get_message(chat_id):
    current_match = get_current_match(chat_id)
    current_match_registrations = get_current_match_registrations(chat_id)

    game_time_frmt = datetime.strptime(current_match['datetime'], DATETIME_FORMAT).strftime("%d.%m.%Y %H:%M")

    message = f"Registration is now open! \nMatch time: {game_time_frmt}\n\n"

    hours_until_match = get_hours_until_match(current_match['datetime'])

    if hours_until_match < 0:
        message = f"Registration is <b>CLOSED!</b> \nMatch time: {game_time_frmt}\n\n"

    message += registered(current_match_registrations)
    return message

def is_player_banned(player_id):
    player_bans = get_players_ban(player_id)
    current_datetime = get_current_time()

    for ban in player_bans:
        user_date = datetime.fromisoformat(ban['until'])

        if current_datetime < user_date:
            return True

        delete_ban(['id'])

    return False

async def check_for_confimation(context: ContextTypes.DEFAULT_TYPE):
    job_data = context.job.data
    chat_id = job_data['chat_id']
    player_id = job_data['player_id']

    curr_match = get_current_match(chat_id)

    is_user_registered = check_if_user_registered(curr_match['match_id'], player_id)

    if is_user_registered['confirmed'] == 0:
        delete_match_registration(curr_match['match_id'], player_id)
        await context.bot.send_message(chat_id=chat_id, text=f"@{player_id} did not confirm their registration!")
        return

def get_priority(player_id, reg_time, game_time, was_in_last_match):
    now = get_current_time()
    reg_time = pytz.timezone("Europe/Prague").localize(datetime.strptime(reg_time, SQL_DATETIME_FORMAT))

    if is_player_banned(player_id):
        return 4
    if (now - reg_time).total_seconds() / 7200 < PRIORITY_HOURS and was_in_last_match:
        return 1

    hours_difference = get_hours_until_match(game_time)
    if hours_difference < 26:
        return 3

    return 2

async def register_another_from_chat(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    chat_id = update.effective_chat.id
    message_id = update.message.id

    if context.args[0].startswith('@'):
        player_nickname = context.args[0][1:]
        player = get_user_by_nickname(player_nickname)
        if not player:
            await context.bot.send_message(chat_id=chat_id, text="This user is not registered in bot.")
    else:
        return

    res = register_core(chat_id, player['user_id'], user_id, False, False)

    job_data = {'player_id': player['user_id'], 'chat_id': chat_id}
    context.job_queue.run_once(check_for_confimation, 14400, data=job_data)

    if res:
        await context.bot.set_message_reaction(chat_id=chat_id, message_id=message_id, reaction="👌")

    return

def register_core(chat_id, player_id, registered_by_id, is_plus=False, confirmed=True):
    was_in_last_match_res = was_in_last_match(chat_id, player_id)

    res = get_current_match(chat_id)
    current_match = res[0]
    match_id = current_match['match_id']
    start_time = current_match['datetime']
    reg_time = current_match['created_at']

    is_user_registered = check_if_user_registered(match_id, player_id)

    if is_user_registered and is_user_registered['confirmed'] == 0:
        confirm_user_registration(match_id, player_id)
        return True

    hours_until_match = get_hours_until_match(current_match['datetime'])

    if hours_until_match < 0:
        return

    priority = get_priority(player_id, reg_time, start_time, was_in_last_match_res)

    create_result = create_match_registration(player_id, registered_by_id, is_plus, confirmed, priority, match_id)

    return create_result

async def register_himself(update: Update, context: CallbackContext):
    user_id = update.callback_query.from_user.id
    chat_id = update.effective_chat.id

    res = register_core(chat_id, user_id, user_id)

    if res:
        query = update.callback_query
        await query.edit_message_text(text=get_message(chat_id), reply_markup=reply_markup, parse_mode=ParseMode.HTML)

    return

async def register_plus_one(update: Update, context: CallbackContext):
    user_id = update.callback_query.from_user.id
    chat_id = update.effective_chat.id
    
    # Send message to user
    if not user_id:
        user_id = update.callback_query.from_user.first_name

    player = user_id + " +1"
    res = register_core(chat_id, player, user_id, True)

    if res:
        query = update.callback_query
        await query.edit_message_text(text=get_message(chat_id), reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    return

def registered(current_match):
    if len(current_match) == 0:
        message = "<b>No registrations yet!</b>"

        return message

    message = "<b>Registered Players:</b>\n"
    for idx, match_registration in enumerate(current_match):
        if idx == 14:
            message += "\n<b>Waiting List:</b>\n"
        player = get_user(match_registration['user_id'])

        message += f"{idx + 1}. @{player['nickname']} - {player['name']} <i>(Priority {match_registration['priority']})</i>"
        if not match_registration['confirmed']:
            message += "<i> Not confirmed</i>"
        message += "\n"

    return message

async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.message.from_user.id
    message_id = update.message.id

    res = get_current_match(chat_id)
    current_match = res
    match_id = current_match['match_id']

    confirm_user_registration(match_id, user_id)

    await context.bot.set_message_reaction(chat_id=chat_id, message_id=message_id, reaction="👌")
