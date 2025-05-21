-- Insert the user
INSERT INTO users (id, username, created_at, updated_at)
VALUES 
    (6038394083, 'groot_n', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

-- Create tags
INSERT INTO tags (name, created_by, created_at, updated_at)
VALUES 
    ('Funny', 6038394083, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('Programming', 6038394083, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('Science', 6038394083, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

-- Insert jokes
INSERT INTO jokes (add_by, language_code, content, status, created_at, updated_at)
VALUES 
    (6038394083, 'en', 'Why don’t skeletons fight each other? They don’t have the guts!', 'published', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    (6038394083, 'en', 'Why did the scarecrow win an award? Because he was outstanding in his field!', 'published', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    (6038394083, 'fr', 'Pourquoi les fantômes n’ont pas d’amis ? Parce qu’ils font peur !', 'published', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

-- Link jokes to tags
INSERT INTO joke_tags (joke_id, tag_id, created_at, updated_at)
VALUES 
    (1, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP), -- First joke tagged as "Funny"
    (2, 2, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP), -- Second joke tagged as "Programming"
    (3, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP); -- Third joke tagged as "Funny"

-- Predefined reactions (already exist in your database)
-- No need to re-insert them unless missing:
-- INSERT INTO reactions (id, name) VALUES (1, 'laughing'), (0, 'thinking'), (-1, 'dislike');

-- Simulate reactions to jokes
INSERT INTO joke_reactions (user_id, joke_id, reaction_id, created_at, updated_at)
VALUES 
    (6038394083, 1, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP), -- User reacts with "laughing" (ID: 1) to the first joke
    (6038394083, 2, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP), -- User reacts with "thinking" (ID: 0) to the second joke
    (6038394083, 3, -1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP); -- User reacts with "dislike" (ID: -1) to the third joke

INSERT INTO preferred_tags (chat_id, tag_id, created_at, updated_at)
VALUES 
    (1, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP), -- Chat 1 prefers "Funny"
    (2, 2, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP); -- Chat 2 prefers "Programming"