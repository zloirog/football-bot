# Create
from operations.common import execute_query, fetch_query

def create_ban(user_id, until):
    existing_record = fetch_query("SELECT 1 FROM Bans WHERE user_id = ? AND until = ?", (user_id, until))
    if not existing_record:
        return execute_query("INSERT INTO Bans (user_id, until) VALUES (?, ?)", (user_id, until))
    
def ban_forever(user_id):
    return execute_query("INSERT INTO Bans (user_id, until) VALUES (?, ?)", (user_id, '2099-11-05 09:30:00+02:00'))


# Read
def get_players_ban(user_id):
    return fetch_query("SELECT * FROM Bans WHERE user_id = ?", (user_id,))

def get_all_bans():
    return fetch_query("SELECT * FROM Bans")

# Update
def update_ban(ban_id, user_id, until):
    execute_query("UPDATE Bans SET user_id = ?, until = ? WHERE ban_id = ?", (user_id, until, ban_id))

# Delete
def delete_ban(user_id):
    execute_query("DELETE FROM Bans WHERE user_id = ?", (user_id,))
