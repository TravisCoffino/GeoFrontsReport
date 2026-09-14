CREATE TABLE articles(
	relKey VARCHAR(60) PRIMARY KEY,
    articleName VARCHAR(200),
    publish DATE,
    articleLink BLOB

);

DESCRIBE relKey