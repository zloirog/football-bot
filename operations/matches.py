# Create
from operations.common import execute_query, fetch_one_query, fetch_query


def create_match(datetime, amount_per_person, chat_id):
    return execute_query("INSERT INTO Matches (datetime, amount_per_person, chat_id) VALUES (?, ?, ?)", (datetime, amount_per_person, chat_id))

# Read
def get_match(match_id):
    return fetch_one_query("SELECT * FROM Matches WHERE match_id = ?", (match_id,))

# Read
def get_last_match(chat_id):
    return fetch_query("""
WITH OrderedMatches AS (
    SELECT m.match_id, m.datetime, m.amount_per_person, m.chat_id,
           ROW_NUMBER() OVER (ORDER BY m.datetime DESC) AS rn
    FROM Matches m
    WHERE m.chat_id = ?
)
SELECT om.match_id, om.datetime, mr.user_id, mr.priority, u.nickname, u.name 
FROM OrderedMatches om
JOIN Match_Registration mr ON om.match_id = mr.match_id
JOIN Users u ON mr.user_id = u.user_id
WHERE om.rn = 2
ORDER BY mr.priority ASC, mr.registered_at;
                       """, ((chat_id,)))

def get_current_match(chat_id):
    return fetch_one_query("""
SELECT m.match_id, m.datetime, m.created_at
FROM Matches m
WHERE m.match_id = (SELECT MAX(match_id) FROM Matches mm WHERE mm.chat_id = ?)
                       """, ((chat_id,)))


def was_in_last_match(chat_id, user_id):
    data = fetch_one_query("""
WITH OrderedMatches AS (
    SELECT m.match_id,
           ROW_NUMBER() OVER (ORDER BY m.datetime DESC) AS rn
    FROM Matches m
    WHERE m.chat_id = ?
),
First14Registrations AS (
    SELECT mr.match_id,
           mr.user_id,
           ROW_NUMBER() OVER (PARTITION BY mr.match_id ORDER BY mr.priority) AS rn
    FROM Match_Registration mr
)
SELECT f14r.user_id
FROM First14Registrations f14r
JOIN OrderedMatches om ON f14r.match_id = om.match_id
WHERE om.rn = 2
AND f14r.rn <= 14
AND f14r.user_id = ?;
                           """, (chat_id, user_id))
    if data is None:
        return False
    else:
        return True


# Update
def update_match(match_id, date, time, amount_per_person, chat_id):
    execute_query("UPDATE Matches SET date = ?, time = ?, amount_per_person = ?, chat_id = ? WHERE match_id = ?", (date, time, amount_per_person, chat_id, match_id))

def get_last_5_matches_with_players(chat_id):
    return fetch_query("""
WITH Last5Matches AS (
    SELECT m.match_id, m.datetime,
           ROW_NUMBER() OVER (ORDER BY m.datetime DESC) AS rn
    FROM Matches m
    WHERE m.chat_id = ?
)
SELECT l5m.match_id, l5m.datetime, mr.user_id, mr.priority, u.nickname, u.name
FROM Last5Matches l5m
JOIN Match_Registration mr ON l5m.match_id = mr.match_id
JOIN Users u ON mr.user_id = u.user_id
WHERE l5m.rn <= 5 AND mr.priority <= 14
ORDER BY l5m.datetime DESC, mr.priority ASC;
                       """, (chat_id,))

# Delete
def delete_match(match_id):
    execute_query("DELETE FROM Matches WHERE match_id = ?", (match_id,))
