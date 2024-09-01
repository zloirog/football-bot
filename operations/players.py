# Create
from operations.common import execute_query, fetch_query


def create_player(nickname, name):
    return execute_query("INSERT INTO Players (nickname, name) VALUES (?, ?)", (nickname, name))

# Read
def get_player(nickname):
    return fetch_query("SELECT * FROM Players WHERE nickname = ?", (nickname,))

# Update
def update_player(nickname, name):
    execute_query("UPDATE Players SET name = ? WHERE nickname = ?", (name, nickname))

# Delete
def delete_player(nickname):
    execute_query("DELETE FROM Players WHERE nickname = ?", (nickname,))
