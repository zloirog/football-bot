# Create
from operations.common import connect_db, execute_query, fetch_one_query, fetch_query

def create_match_registration(user_id, registered_by_id, is_plus, confirmed, priority, match_id):

    results = fetch_one_query("""
        SELECT
            COALESCE(SUM(CASE WHEN user_id = registered_by_id AND is_plus = 0 THEN 1 ELSE 0 END), 0) AS self_reg,
            COALESCE(SUM(CASE WHEN user_id != registered_by_id AND is_plus = 0 THEN 1 ELSE 0 END), 0) AS other_chat_reg,
            COALESCE(SUM(CASE WHEN user_id != registered_by_id AND is_plus != 0 THEN 1 ELSE 0 END), 0) AS extra_reg
        FROM Match_Registration
        WHERE registered_by_id = ? AND match_id = ?
    """, (registered_by_id, match_id))

    self_reg = int(results['self_reg']) if results['self_reg'] is not None else 0
    other_chat_reg = int(results['other_chat_reg']) if results['other_chat_reg'] is not None else 0
    extra_reg = int(results['extra_reg']) if results['extra_reg'] is not None else 0

    if user_id == registered_by_id and is_plus == 0:
        if int(self_reg) > 0:
            return False

    elif user_id != registered_by_id and is_plus == 0:
        if int(other_chat_reg) > 0:
            return False

    elif user_id != registered_by_id and is_plus != 0:
        if int(extra_reg) > 0:
            return False

    return execute_query("INSERT INTO Match_Registration (user_id, registered_by_id, is_plus, confirmed, priority, match_id) VALUES (?, ?, ?, ?, ?, ?)", (user_id, registered_by_id, is_plus, confirmed, priority, match_id))

# Read
def get_match_registration(match_id):
    return fetch_query("SELECT * FROM Match_Registration WHERE match_id = ?", (match_id))

def get_current_match_registrations(chat_id):
    return fetch_query("""
WITH OrderedMatches AS (
    SELECT m.match_id, m.datetime, m.amount_per_person, m.chat_id
    FROM Matches m
    WHERE m.match_id = (SELECT MAX(match_id) FROM Matches m WHERE m.chat_id = ?)
)
SELECT om.match_id, om.datetime, mr.user_id, mr.priority, mr.is_plus, mr.confirmed, mr.registration_id
FROM OrderedMatches om
JOIN Match_Registration mr ON om.match_id = mr.match_id
ORDER BY mr.priority ASC, mr.registered_at;
                       """, ((chat_id,)))

def check_if_user_registered(match_id, user_id):
    return fetch_one_query("SELECT * FROM Match_Registration WHERE match_id = ? AND user_id = ?", (match_id, user_id))

# Update
def update_match_registration(registration_id, user_id, registered_by_id, is_plus, priority, match_id):
    execute_query("UPDATE Match_Registration SET user_id = ?, registered_by_id = ?, is_plus = ?, confirmed = ?, priority = ?, match_id = ? WHERE registration_id = ?", (user_id, registered_by_id, is_plus, priority, match_id, registration_id))

def confirm_user_registration(match_id, user_id):
    execute_query("""
UPDATE Match_Registration SET confirmed = 1
WHERE match_id = (SELECT MAX(match_id) FROM Match_Registration WHERE user_id = ? AND match_id = ?)
""", ((user_id, match_id)))

# Delete
# Delete
def delete_match_registration(match_id, user_id):
    execute_query("DELETE FROM Match_Registration WHERE user_id = ? AND match_id = ?", (user_id, match_id))

def delete_match_plus_one_registration(match_id, user_id):
    removed_user_id = fetch_one_query("SELECT user_id FROM Match_Registration WHERE registered_by_id = ? AND match_id = ? AND is_plus = 1", (user_id, match_id))
    execute_query("DELETE FROM Match_Registration WHERE registered_by_id = ? AND match_id = ? AND is_plus = 1", ((user_id, match_id)))
    return removed_user_id
