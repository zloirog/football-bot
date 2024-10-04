
-- Step 1: Create a new table for Chats with the desired schema
CREATE TABLE NewChats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id VARCHAR(255),
    name VARCHAR(255),
    game_time TIME,
    game_week_day VARCHAR(10),
    reg_time VARCHAR(10),
    reg_week_day VARCHAR(10)
);

-- Step 2: Insert data from the old Chats table into the new table
INSERT INTO NewChats (chat_id, name, game_time, game_week_day, reg_time, reg_week_day)
SELECT chat_id, name, game_time, game_week_day, reg_time, reg_week_day
FROM Chats;

-- Step 3: Now we need to update the Matches table
-- First, create a new Matches table with the correct foreign key constraint
CREATE TABLE NewMatches (
    match_id INTEGER PRIMARY KEY AUTOINCREMENT,
    datetime DATETIME,
    amount_per_person INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    chat_id VARCHAR(255),
    FOREIGN KEY (chat_id) REFERENCES Chats(id) ON DELETE CASCADE
);

-- Step 4: Insert data into the new Matches table, using the new chat_id mapping
INSERT INTO NewMatches (match_id, chat_id, datetime, amount_per_person, created_at)
SELECT Matches.match_id, NewChats.id, Matches.datetime, Matches.amount_per_person, Matches.created_at
FROM Matches
JOIN NewChats ON Matches.chat_id = NewChats.chat_id;

-- Step 5: Drop the old Matches table
DROP TABLE Matches;

-- Step 6: Rename NewMatches to Matches
ALTER TABLE NewMatches RENAME TO Matches;

-- Step 7: Drop the old Chats table
DROP TABLE Chats;

-- Step 8: Rename NewChats to Chats
ALTER TABLE NewChats RENAME TO Chats;
