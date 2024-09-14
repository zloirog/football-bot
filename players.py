from telegram import Update
from telegram.ext import CallbackContext, ContextTypes

from operations.players import create_player, get_all_players_in_the_chat
from utils import is_chat_admin

async def register_player(update: Update, context: CallbackContext):
    nickname = update.effective_user.username
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    name = f"{update.effective_user.first_name} {update.effective_user.last_name}"
    
    try:
        create_player(user_id, nickname, name, chat_id)
        await context.bot.send_message(chat_id=chat_id, text="Thank you for registering.")
    except Exception as e:
        await context.bot.send_message(chat_id=chat_id, text=f"Oops! Something went wrong: {str(e)}")

async def get_all_players(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_chat_admin(update, context):
        return
    
    chat_id = update.effective_chat.id
    
    players = get_all_players_in_the_chat(chat_id)
    
    message = "Here are the users who have registered in the bot:\n"
    
    for idx, player in enumerate(players, start=1):
        message += f"{idx}. Name: {player['name']}, Nickname: {player['nickname']}, ID: {player['player_id']}\n"
        
    await context.bot.send_message(chat_id=chat_id, text=message)
