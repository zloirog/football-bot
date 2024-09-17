# Create
from operations.common import execute_query, fetch_query


def create_user_notification(user_id, chat_id):
    return execute_query("INSERT INTO Players_Notifications (user_id, chat_id) VALUES (?, ?)", (user_id, chat_id))

# Read
def get_user_notification(id):
    return fetch_query("SELECT * FROM Players_Notifications WHERE id = ?", (id,))

# Update
def update_user_notification(id, user_id, chat_id):
    execute_query("UPDATE Players_Notifications SET user_id = ?, chat_id = ? WHERE id = ?", (user_id, chat_id, id))

# Delete
def delete_user_notification(id):
    execute_query("DELETE FROM Players_Notifications WHERE id = ?", (id,))
