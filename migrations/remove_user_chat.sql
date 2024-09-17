-- Migration to drop user_chat_id property from Users table
ALTER TABLE Users
DROP COLUMN user_chat_id;