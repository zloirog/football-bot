# Create
from operations.common import execute_query, fetch_query


def create_user(id, nickname, name, user_chat_id):
    return execute_query("INSERT INTO Players (player_id, nickname, name, user_chat_id) VALUES (?, ?, ?, ?)", (id, nickname, name, user_chat_id))

# Read
def get_all_users():
    return fetch_query("SELECT * FROM Players")

def get_user(nickname):
    return fetch_query("SELECT * FROM Players WHERE nickname = ?", (nickname,))

# Update
def update_user(nickname, name):
    execute_query("UPDATE Players SET name = ? WHERE nickname = ?", (name, nickname))

# Delete
def delete_user(id):
    execute_query("DELETE FROM Players WHERE player_id = ?", (id))
