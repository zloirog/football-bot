import json
import datetime
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, CallbackContext
from constants import MAX_PLAYERS, PRIORITY_HOURS, DATA_FILE, LAST_MATCH_FILE, BAN_FILE
from utils import is_chat_admin

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

async def save_last_match(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_chat_admin(update, context):
        return

    data = load_data()
    game_id = list(data.keys())[-1]
    game = data[game_id]
    with open(LAST_MATCH_FILE, 'w') as file:
        json.dump(game["players"], file, indent=4)
        
def load_bans_file():
    if os.path.exists(BAN_FILE):
        with open(BAN_FILE, 'r') as file:
            return json.load(file)
    return []

def ban_player(who, until_when):
    data = load_bans_file()
    new_object = {'name': who, 'until': until_when}
    data.append(new_object)
    with open(BAN_FILE, 'w') as file:
        json.dump(data, file, indent=4)
    