-- CREATE TABLE Players (
--     nickname VARCHAR(255) PRIMARY KEY,
--     name VARCHAR(255)
-- );

CREATE TABLE Players_Notifications (
    notification_id INTEGER PRIMARY KEY,
    nickname VARCHAR(255),
    chat_id VARCHAR(255),
    -- FOREIGN KEY (nickname) REFERENCES Players(nickname),
    FOREIGN KEY (chat_id) REFERENCES Chats(chat_id)
);

CREATE TABLE Chats (
    chat_id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255),
    game_time TIME,
    game_week_day VARCHAR(10),
    reg_time VARCHAR(10),
    reg_week_day VARCHAR(10)
);

CREATE TABLE Matches (
    match_id INTEGER PRIMARY KEY,
    datetime DATETIME,
    amount_per_person INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    chat_id VARCHAR(255),
    FOREIGN KEY (chat_id) REFERENCES Chats(chat_id)
);

CREATE TABLE Match_Registration (
    registration_id INTEGER PRIMARY KEY,
    match_id INT,
    nickname VARCHAR(255),
    registered_by VARCHAR(255),
    is_plus BOOLEAN, 
    confirmed BOOLEAN,
    priority INT,
    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- FOREIGN KEY (nickname) REFERENCES Players(nickname),
    -- FOREIGN KEY (registered_by) REFERENCES Players(nickname),
    FOREIGN KEY (match_id) REFERENCES Matches(match_id)
);

CREATE TABLE Bans (
    ban_id INTEGER PRIMARY KEY,
    nickname VARCHAR(255),
    until TIMESTAMP
    -- FOREIGN KEY (nickname) REFERENCES Players(nickname)
);