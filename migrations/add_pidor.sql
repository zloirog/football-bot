-- Create the Random_Selections table
CREATE TABLE IF NOT EXISTS Random_Selections (
    selection_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    chat_id INTEGER,
    selected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES Users(user_id)
);

-- Create an index for faster queries
CREATE INDEX idx_random_selections_chat_user
ON Random_Selections (chat_id, user_id);

-- Create an index for date-based queries
CREATE INDEX idx_random_selections_date
ON Random_Selections (chat_id, selected_at);