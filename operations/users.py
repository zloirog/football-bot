# Create
from operations.common import execute_query, fetch_query


def create_user(id, nickname, name, user_chat_id):
    return execute_query("INSERT INTO Users (player_id, nickname, name, user_chat_id) VALUES (?, ?, ?, ?)", (id, nickname, name, user_chat_id))

# Read
def get_all_users_from_db():
    return fetch_query("SELECT * FROM Users")

def get_user(id):
    return fetch_query("SELECT * FROM Users WHERE id = ?", (id,))

# Update
def update_user(nickname, name):
    execute_query("UPDATE Users SET name = ? WHERE nickname = ?", (name, nickname))

# Delete
def delete_user(id):
    execute_query("DELETE FROM Users WHERE player_id = ?", (id))
