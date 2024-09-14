from telegram import Update
from telegram.ext import CallbackContext, ContextTypes

from operations.players import create_player


async def register_player(update: Update, context: CallbackContext):
    nickname = update.effective_user.username
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    name = update.effective_user.first_name + update.effective_user.last_name
    
    res = create_player(user_id, nickname, name, chat_id)

    if res:
        await context.bot.send_message(chat_id=chat_id, text=f"Thank you for registration.")
    else:
        await context.bot.send_message(chat_id=chat_id, text=f"Something went wrong.")