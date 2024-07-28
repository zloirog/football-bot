import json
import os
from constants import DATA_FILE, LAST_MATCH_FILE, BAN_FILE

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
