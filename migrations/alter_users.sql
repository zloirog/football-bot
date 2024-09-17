-- Update the Players_Notifications table
UPDATE Players_Notifications
SET user_id = (SELECT user_id FROM Players WHERE Players.nickname = Players_Notifications.nickname);

ALTER TABLE Players_Notifications
DROP COLUMN nickname;

ALTER TABLE Players_Notifications
ADD CONSTRAINT fk_players_notifications_user_id
FOREIGN KEY (user_id) REFERENCES Players(user_id);

-- Update the Match_Registration table
UPDATE Match_Registration
SET user_id = (SELECT user_id FROM Players WHERE Players.nickname = Match_Registration.nickname);

UPDATE Match_Registration
SET registered_by_id = (SELECT user_id FROM Players WHERE Players.nickname = Match_Registration.registered_by);

ALTER TABLE Match_Registration
DROP COLUMN nickname;

ALTER TABLE Match_Registration
DROP COLUMN registered_by;

ALTER TABLE Match_Registration
ADD COLUMN user_id INTEGER;

ALTER TABLE Match_Registration
ADD COLUMN registered_by_id INTEGER;

ALTER TABLE Match_Registration
ADD CONSTRAINT fk_match_registration_user_id
FOREIGN KEY (user_id) REFERENCES Players(user_id);

ALTER TABLE Match_Registration
ADD CONSTRAINT fk_match_registration_registered_by_id
FOREIGN KEY (registered_by_id) REFERENCES Players(user_id);

-- Update the Bans table
UPDATE Bans
SET user_id = (SELECT user_id FROM Players WHERE Players.nickname = Bans.nickname);

ALTER TABLE Bans
DROP COLUMN nickname;

ALTER TABLE Bans
ADD CONSTRAINT fk_bans_user_id
FOREIGN KEY (user_id) REFERENCES Players(user_id);
