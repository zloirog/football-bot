-- Create the Players table
CREATE TABLE Players (
    player_id INTEGER PRIMARY KEY,
    nickname VARCHAR(255) UNIQUE,
    name VARCHAR(255)
);