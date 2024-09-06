from datetime import datetime

import pytz
from date_utils import get_hours_until_match, get_current_time
from operations.bans import delete_ban, get_players_ban
from operations.match_registrations import confirm_user_registration, create_match_registration, delete_match_registration, get_current_match_registrations
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CallbackContext, ContextTypes
from constants import  DATETIME_FORMAT, PRIORITY_HOURS, SQL_DATETIME_FORMAT, reply_markup
from operations.matches import get_current_match, was_in_last_match



def get_message(chat_id):
    current_match = get_current_match(chat_id)[0]
    current_match_registrations = get_current_match_registrations(chat_id)

    game_time_frmt = datetime.strptime(current_match['datetime'], DATETIME_FORMAT).strftime("%d.%m.%Y %H:%M")

    message = f"Registration opened! \n{game_time_frmt}\n\n"

    hours_until_match = get_hours_until_match(current_match['datetime'])

    if hours_until_match < 0:
        message = f"Registration <b>CLOSED!</b> \n{game_time_frmt}\n\n"


    message += registered(current_match_registrations)
    return message


def is_player_banned(player):
    player_bans = get_players_ban(player)
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
    name = job_data['name']

    curr_match = get_current_match_registrations(chat_id)

    for player in curr_match:
        if player['nickname'] == name and player['confirmed'] == False:
            delete_match_registration(player['registration_id'])
            await context.bot.send_message(chat_id=chat_id, text=f"@{name} did not confirmed his registration!")
            return


def get_priority(player, reg_time, game_time, was_in_last_match):
    now = get_current_time()
    reg_time = pytz.timezone("Europe/Prague").localize(datetime.strptime(reg_time, SQL_DATETIME_FORMAT))

    if is_player_banned(player):
        return 4
    if (now - reg_time).total_seconds() / 7200 < PRIORITY_HOURS and was_in_last_match:
        return 1

    hours_difference = get_hours_until_match(game_time)
    if hours_difference < 26:
        return 3

    return 2


async def register_another_from_chat(update: Update, context: CallbackContext):
    user = update.message.from_user.username
    chat_id = update.effective_chat.id
    message_id = update.message.id

    if not user:
        user = update.message.from_user.first_name

    if context.args[0].startswith('@'):
        player = context.args[0][1:]
    else:
        return

    res = register_core(chat_id, player, user, False, False)

    if res:
        await context.bot.set_message_reaction(chat_id=chat_id, message_id=message_id, reaction="👌")

    return


def register_core(chat_id, nickname, registered_by, is_plus=False, confirmed=True):
    was_in_last_match_res = was_in_last_match(chat_id, nickname)

    res = get_current_match(chat_id)
    current_match = res[0]
    match_id = current_match['match_id']
    start_time = current_match['datetime']
    reg_time = current_match['created_at']

    hours_until_match = get_hours_until_match(current_match['datetime'])

    if hours_until_match < 0:
        return

    priority = get_priority(nickname, reg_time, start_time, was_in_last_match_res)

    create_result = create_match_registration(nickname, registered_by, is_plus, confirmed, priority, match_id)

    return create_result


async def register_himself(update: Update, context: CallbackContext):
    user = update.callback_query.from_user.username
    chat_id = update.effective_chat.id

    if not user:
        user = update.callback_query.from_user.first_name

    res = register_core(chat_id, user, user)

    if res:
        query = update.callback_query
        await query.edit_message_text(text=get_message(chat_id), reply_markup=reply_markup, parse_mode=ParseMode.HTML)

    return

async def register_plus_one(update: Update, context: CallbackContext):
    user = update.callback_query.from_user.username
    chat_id = update.effective_chat.id

    if not user:
        user = update.callback_query.from_user.first_name

    player = user + " +1"
    res = register_core(chat_id, player, user, True)

    if res:
        query = update.callback_query
        await query.edit_message_text(text=get_message(chat_id), reply_markup=reply_markup, parse_mode=ParseMode.HTML)

    return


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

def registered(current_match):
    if len(current_match) == 0:
        message = "<b>No registrations yet!</b>"

        return message

    message = "<b>Registered Players:</b>\n"
    for idx, match_registration in enumerate(current_match):
        if idx == 14:
            message += "\n<b>Waiting List:</b>\n"

        message += f"{idx + 1}. @{match_registration['nickname']} <i>(Priority {match_registration['priority']})</i>"
        if not match_registration['confirmed']:
            message += "<i> Not confirmed</i>"
        message += "\n"

    return message


async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.message.from_user.username
    message_id = update.message.id

    confirm_user_registration(user)

    await context.bot.set_message_reaction(chat_id=chat_id, message_id=message_id, reaction="👌")
