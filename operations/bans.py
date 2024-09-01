# Create
from operations.common import execute_query, fetch_query


def create_ban(nickname, until):
    existing_record = fetch_query("SELECT 1 FROM Bans WHERE nickname = ? AND until = ?", (nickname, until))
    if not existing_record:
        return execute_query("INSERT INTO Bans (nickname, until) VALUES (?, ?)", (nickname, until))

# Read
def get_players_ban(nickname):
    return fetch_query("SELECT * FROM Bans WHERE nickname = ?", (nickname,))

# Update
def update_ban(ban_id, nickname, until):
    execute_query("UPDATE Bans SET nickname = ?, until = ? WHERE ban_id = ?", (nickname, until, ban_id))

# Delete
def delete_ban(nickname):
    execute_query("DELETE FROM Bans WHERE nickname = ?", (nickname,))
