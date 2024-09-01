from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Constants
MAX_PLAYERS = 14
PRIORITY_HOURS = 2
DATA_FILE = 'football_matches.json'
LAST_MATCH_FILE = 'last_match.json'
BAN_FILE = 'bans.json'
CHAT_ID = '-1001198949892'

keyboard = [
    [InlineKeyboardButton("Register", callback_data='register')],
    [InlineKeyboardButton("Register ➕ 1️⃣", callback_data='register_plus_one')],
    [InlineKeyboardButton("Quit", callback_data='quit')],
    [InlineKeyboardButton("Remove ➕ 1️⃣", callback_data='remove_plus_one')],
    [InlineKeyboardButton("Refresh 🔄", callback_data='refresh_message')],

]
reply_markup = InlineKeyboardMarkup(keyboard)

DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S%z'
SQL_DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'