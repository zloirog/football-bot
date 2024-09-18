-- Migration to drop user_chat_id property from Users table
ALTER TABLE Users
DROP COLUMN user_chat_id;

-- Rename the player_id column to user_id in the Users table
ALTER TABLE Users
RENAME COLUMN player_id TO user_id;

Add the user_id column to the Players_Notifications table with a foreign key constraint
ALTER TABLE Players_Notifications
ADD COLUMN user_id INTEGER REFERENCES Users(user_id);

Update the user_id column in the Players_Notifications table
UPDATE Players_Notifications
SET user_id = (SELECT user_id FROM Users WHERE Users.nickname = Players_Notifications.nickname);

-- Drop the nickname column from the Players_Notifications table
ALTER TABLE Players_Notifications
DROP COLUMN nickname;

-- Add the user_id and registered_by_id columns to the Match_Registration table with foreign key constraints
ALTER TABLE Match_Registration
ADD COLUMN user_id INTEGER REFERENCES Users(user_id);

ALTER TABLE Match_Registration
ADD COLUMN registered_by_id INTEGER REFERENCES Users(user_id);

-- Update the user_id and registered_by_id columns in the Match_Registration table
UPDATE Match_Registration
SET user_id = (SELECT user_id FROM Users WHERE Users.nickname = Match_Registration.nickname);

UPDATE Match_Registration
SET registered_by_id = (SELECT user_id FROM Users WHERE Users.nickname = Match_Registration.registered_by);

-- Drop the nickname and registered_by columns from the Match_Registration table
ALTER TABLE Match_Registration
DROP COLUMN nickname;

ALTER TABLE Match_Registration
DROP COLUMN registered_by;

-- Add the user_id column to the Bans table with a foreign key constraint
ALTER TABLE Bans
ADD COLUMN user_id INTEGER REFERENCES Users(user_id);

-- Update the user_id column in the Bans table
UPDATE Bans
SET user_id = (SELECT user_id FROM Users WHERE Users.nickname = Bans.nickname);

-- Drop the nickname column from the Bans table
ALTER TABLE Bans
DROP COLUMN nickname;
