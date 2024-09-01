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
SELECT om.match_id, om.datetime, mr.nickname, mr.priority
FROM OrderedMatches om
JOIN Match_Registration mr ON om.match_id = mr.match_id
WHERE om.rn = 2
ORDER BY mr.priority ASC;
                       """, ((chat_id,)))

def get_current_match(chat_id):
    return fetch_query("""
SELECT *
FROM Matches m
WHERE m.match_id = (SELECT MAX(match_id) FROM Matches m WHERE m.chat_id = ?)
                       """, ((chat_id,)))


def was_in_last_match(chat_id, nickname):
    data = fetch_one_query("""
WITH OrderedMatches AS (
    SELECT m.match_id,
           ROW_NUMBER() OVER (ORDER BY m.datetime DESC) AS rn
    FROM Matches m
    WHERE m.chat_id = ?
)
SELECT mr.nickname
FROM Match_Registration mr
JOIN OrderedMatches om ON mr.match_id = om.match_id
WHERE om.rn = 2
AND mr.nickname = ?;
                           """, (chat_id, nickname))
    if data is None:
        return False
    else: 
        return True
    

# Update
def update_match(match_id, date, time, amount_per_person, chat_id):
    execute_query("UPDATE Matches SET date = ?, time = ?, amount_per_person = ?, chat_id = ? WHERE match_id = ?", (date, time, amount_per_person, chat_id, match_id))

# Delete
def delete_match(match_id):
    execute_query("DELETE FROM Matches WHERE match_id = ?", (match_id,))