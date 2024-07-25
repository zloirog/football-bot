import os
import json

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