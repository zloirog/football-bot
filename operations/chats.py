# Create
from operations.common import execute_query, fetch_one_query, fetch_query


def create_chat(chat_id, name, game_time, game_week_day, reg_time, reg_week_day):
    return execute_query("INSERT INTO Chats (chat_id, name, game_time, game_week_day, reg_time, reg_week_day) VALUES (?, ?, ?, ?, ?, ?)", (chat_id, name, game_time, game_week_day, reg_time, reg_week_day))

# Read
def get_chat(chat_id):
    return fetch_one_query("SELECT * FROM Chats WHERE chat_id = ?", ((chat_id,)))

def get_all_chats():
    return fetch_query("SELECT * FROM Chats")

# Update
def update_chat(chat_id, name, time, week_day):
    execute_query("UPDATE Chats SET name = ?, time = ?, week_day = ? WHERE chat_id = ?", (name, time, week_day, (chat_id,)))

# Delete
def delete_chat(chat_id):
    execute_query("DELETE FROM Chats WHERE chat_id = ?", (chat_id,))
