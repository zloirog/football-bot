from telegram import Update
from telegram.ext import ContextTypes
from date_utils import next_saturday
from match_files import load_data

def get_message():
    game_date = next_saturday()
    game_time_frmt = game_date.strftime("%d.%m.%Y %H:%M")
    message = f"Registration opened! \n{game_time_frmt}\n\n" + registered()
    return message



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