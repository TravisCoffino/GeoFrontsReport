USE geonewsmap;

DROP TABLE IF EXISTS articles;

CREATE TABLE articles(
    id INT AUTO_INCREMENT PRIMARY KEY,
    relationshipKey VARCHAR(60) NOT NULL,
    title VARCHAR(200) NOT NULL,
    summary TEXT NOT NULL,
    url TEXT NOT NULL,
    country VARCHAR(100) NOT NULL,
    relatedCountry VARCHAR(100) NOT NULL,
    published DATE NOT NULL
);

DESCRIBE articles;

INSERT INTO articles(
    relationshipKey,
    title,
    summary,
    url,
    country,
    relatedCountry,
    published
)
VALUES
(
    'Finland-Russia',
    'Finnish border closed to Russians with tourist visas',
    'Finland’s border with Russia was closed to Russians with tourist visas Friday',
    'https://apnews.com/article/russia-ukraine-travel-denmark-international-relations-e6a9905a4b6a12b565a86aff803799d9',
    'Finland',
    'Russia',
    '2026-07-04'
),
(
    'Finland-Russia',
    'Finland keeps eastern border closed as risk of instrumentalised migration "remains likely"',
    'The border was shut in late 2023',
    'https://yle.fi/a/74-20229880',
    'Finland',
    'Russia',
    '2026-07-03'
),
(
    'United States-Taiwan',
    'USA renews Taiwan Chip Deal',
    'The United States has renewed a $400 Chip Deal with TSMC',
    'https://www.cfr.org/articles/new-us-taiwan-trade-and-chip-deal-announced',
    'United States',
    'Taiwan',
    '2026-05-31'
);

SELECT * FROM articles;