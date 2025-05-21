-- Ensure the database uses UTF-8 encoding
PRAGMA encoding = 'UTF-8';

-- Drop all tables if they exist
DROP TABLE IF EXISTS joke_reactions;
DROP TABLE IF EXISTS joke_tags;
DROP TABLE IF EXISTS preferred_tags;
DROP TABLE IF EXISTS reactions;
DROP TABLE IF EXISTS tags;
DROP TABLE IF EXISTS jokes;
DROP TABLE IF EXISTS settings;
DROP TABLE IF EXISTS chats;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS languages;

-- Table: languages
CREATE TABLE languages (
    code TEXT PRIMARY KEY,       -- Language code (e.g., 'en', 'fr')
    name TEXT NOT NULL           -- Language name (e.g., 'English', 'French')
);




-- Table: users
CREATE TABLE users (
    id INTEGER PRIMARY KEY,                    -- Unique ID for each user
    username TEXT,                             -- Username (optional)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Timestamp when the user was added
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP  -- Timestamp when the user was last updated
);

-- Table: chats
CREATE TABLE chats (
    id INTEGER PRIMARY KEY,                    -- Unique ID for each chat
    type TEXT NOT NULL DEFAULT 'private', -- Could be 'private', 'groupowner', etc.
    username TEXT,                             -- Chat name or group/channel name
    last_message_id INTEGER DEFAULT NULL,     -- Last message ID in the chat
    user_id INTEGER NULL,                 -- Link to the user who owns the chat
    last_joke_sent_at INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Timestamp when the chat was added
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Timestamp when the chat was last updated
    FOREIGN KEY (user_id) REFERENCES users(id) -- Ensure the chat is linked to a valid user
);

-- Table: settings
CREATE TABLE settings (
    id INTEGER PRIMARY KEY,
    chat_id INTEGER NOT NULL UNIQUE,          -- One setting per chat
    preferred_language TEXT NOT NULL DEFAULT 'en', -- Preferred language for jokes
    schedule INTEGER DEFAULT 600,             -- Joke-sending interval in seconds
    sending_jokes TEXT NOT NULL DEFAULT 'off',-- Whether joke-sending is enabled
    delete_last_joke TEXT NOT NULL DEFAULT 'no', -- Whether the last joke should be deleted before sending a new one
    FOREIGN KEY (chat_id) REFERENCES chats(id), -- Ensure the setting is linked to a valid chat
    FOREIGN KEY (preferred_language) REFERENCES languages(code) -- Ensure the language exists
);

-- Table: jokes
CREATE TABLE jokes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,               -- Unique ID for each joke
    add_by INTEGER NOT NULL,                            -- User ID of the person who added the joke
    language_code TEXT NOT NULL DEFAULT 'en',           -- Language of the joke
    content TEXT NOT NULL,                              -- The joke text
    status TEXT NOT NULL DEFAULT 'pending',           -- Lifecycle status: 'draft', 'published', 'archived'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,     -- Timestamp when the joke was added
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,     -- Timestamp when the joke was last updated
    deleted_at TIMESTAMP DEFAULT NULL,                  -- Soft deletion timestamp
    FOREIGN KEY (add_by) REFERENCES users(id),          -- Ensure the joke is linked to a valid user
    FOREIGN KEY (language_code) REFERENCES languages(code), -- Ensure the language exists
    UNIQUE(content)                                    -- Ensure joke content is unique
);

-- Table: reactions
CREATE TABLE reactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,     -- Unique ID for each reaction type
    name TEXT NOT NULL UNIQUE,                -- Name of the reaction (e.g., 'like', 'laughing', 'dislike')
    emoji TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Timestamp when the reaction was added
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP  -- Timestamp when the reaction was last updated
);

-- Table: joke_reactions
CREATE TABLE joke_reactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,     -- Unique ID for each reaction record
    user_id INTEGER NOT NULL,                 -- User who reacted
    joke_id INTEGER NOT NULL,                 -- Joke that was reacted to
    reaction_id INTEGER NOT NULL,             -- Type of reaction (foreign key to reactions(id))
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Timestamp when the reaction was added
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Timestamp when the reaction was last updated
    FOREIGN KEY (reaction_id) REFERENCES reactions(id),
    FOREIGN KEY (joke_id) REFERENCES jokes(id),
    FOREIGN KEY (user_id) REFERENCES users(id), -- Link to the user who reacted
    UNIQUE(user_id, joke_id)                  -- Prevent duplicate reactions from the same user
);

-- Table: tags
CREATE TABLE tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,     -- Unique ID for each tag
    name TEXT NOT NULL UNIQUE,                -- Tag name (e.g., 'ar: Arabic', 'cs: Computer Science')
    created_by INTEGER NOT NULL,              -- User ID of the person who added the tag
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Timestamp when the tag was added
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Timestamp when the tag was last updated
    FOREIGN KEY (created_by) REFERENCES users(id) -- Link to the user who created the tag
);

-- Table: joke_tags
DROP TABLE IF EXISTS joke_tags;

CREATE TABLE joke_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    joke_id INTEGER NOT NULL,                  -- Joke associated with the tag
    tag_id INTEGER NOT NULL,                   -- Tag associated with the joke
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Timestamp when the association was added
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Timestamp when the association was last updated
    FOREIGN KEY (joke_id) REFERENCES jokes(id), -- Ensure the joke exists
    FOREIGN KEY (tag_id) REFERENCES tags(id),   -- Ensure the tag exists
    UNIQUE(joke_id, tag_id)                    -- Prevent duplicate joke-tag associations
);

-- Table: preferred_tags
CREATE TABLE preferred_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,     -- Unique ID for each record
    chat_id INTEGER NOT NULL,                 -- Chat that prefers the tag
    tag_id INTEGER NOT NULL,                  -- Tag that the chat prefers
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Timestamp when the preference was added
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Timestamp when the preference was last updated
    FOREIGN KEY (chat_id) REFERENCES chats(id), -- Ensure the chat exists
    FOREIGN KEY (tag_id) REFERENCES tags(id),  -- Ensure the tag exists
    UNIQUE(chat_id, tag_id)                   -- Prevent duplicate preferences for the same chat and tag
);

-- Indexes for performance optimization
CREATE INDEX idx_chats_user_id ON chats(user_id);
CREATE INDEX idx_settings_chat_id ON settings(chat_id);
CREATE INDEX idx_jokes_add_by ON jokes(add_by);
CREATE INDEX idx_jokes_language_code ON jokes(language_code);
CREATE INDEX idx_jokes_status ON jokes(status);
CREATE INDEX idx_joke_reactions_joke_id ON joke_reactions(joke_id);
CREATE INDEX idx_joke_reactions_user_id ON joke_reactions(user_id);
CREATE INDEX idx_joke_tags_tag_id ON joke_tags(tag_id);
CREATE INDEX idx_preferred_tags_chat_id ON preferred_tags(chat_id);

-- Insert default reactions
DELETE FROM reactions ;
INSERT INTO reactions (id, name, emoji) VALUES (1, 'laughing','🤣');
INSERT INTO reactions (id, name, emoji) VALUES (0, 'thinking', '🤔');  
INSERT INTO reactions (id, name, emoji) VALUES (-1, 'dislike','👎');

-- Trigger to update `updated_at` automatically for jokes
CREATE TRIGGER update_joke_updated_at
AFTER UPDATE ON jokes
FOR EACH ROW
BEGIN
    UPDATE jokes SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;


