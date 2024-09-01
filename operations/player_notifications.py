# Create
from operations.common import execute_query, fetch_query


def create_player_notification(nickname, chat_id):
    return execute_query("INSERT INTO Players_Notifications (nickname, chat_id) VALUES (?, ?)", (nickname, chat_id))

# Read
def get_player_notification(id):
    return fetch_query("SELECT * FROM Players_Notifications WHERE id = ?", (id,))

# Update
def update_player_notification(id, nickname, chat_id):
    execute_query("UPDATE Players_Notifications SET nickname = ?, chat_id = ? WHERE id = ?", (nickname, chat_id, id))

# Delete
def delete_player_notification(id):
    execute_query("DELETE FROM Players_Notifications WHERE id = ?", (id,))
