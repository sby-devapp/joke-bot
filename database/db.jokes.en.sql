
-- Insert jokes in English with user_id= 6038394083 

    -- Format: 
    -- {question}?(🤔/😳/😑)\n
    -- {answer}! (😂/😅/😅/😂/🤣/🥲/😜)
    --
    -- if in the question/answer there is a word that similare to an emoji put the emoji beside it Example: ... book 📚 ... school 🏫 ... laptop 💻 ... 
    -- joke example: 
    --      Why don’t skeletons☠️ fight⚔️ each other? 🤔\n
    --      They don’t have the  gits🍖! 😂\n

INSERT INTO jokes (add_by, language_code, content, status, created_at, updated_at) 
VALUES
    (6038394083, 'en', 'Why don’t skeletons☠️ fight⚔️ each other? 🤔\nThey don’t have the  gits🍖! 😂\n', 'published', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    (6038394083, 'en', 'Why did the scarecrow🏫 win an award🏆? 🤔\nBecause he was outstanding in his field! 😂\n', 'published', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    (6038394083, 'en', 'Why did the computer💻 go to the doctor? 🤔\nBecause it had a virus🦠! 😂\n', 'published', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    (6038394083, 'en', 'Why was the math book📚 sad? 🤔\nBecause it had too many problems! 😂\n', 'published', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    (6038394083, 'en', 'Why did the bicycle🚲 fall over? 🤔\nBecause it was two-tired! 😂\n', 'published', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    (6038394083, 'en', 'Why don’t scientists trust atoms? 🤔\nBecause they make up everything! 😂\n', 'published', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    (6038394083, 'en', 'What do you call fake spaghetti? 🤔\nAn impasta! 😂\n', 'published', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    (6038394083, 'en', 'Why did the golfer🏌️‍♂️ bring two pairs of pants👖? 🤔\nIn case he got a hole in one! 😂\n', 'published', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    (6038394083, 'en', 'What do you call cheese that isn’t yours? 🤔\nNacho cheese! 😂\n', 'published', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    (6038394083, 'en', 'Why did the coffee☕️ file a police report? 🤔\nIt got mugged! 😂\n', 'published', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

