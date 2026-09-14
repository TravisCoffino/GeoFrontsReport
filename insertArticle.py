import mysql.connector


def insert_article(article):
    connection = mysql.connector.connect(
        host="localhost",
        user="geoUser",
        password="geoPassword123",
        database="geonewsmap"
    )

    cursor = connection.cursor()

    sql = """
    INSERT INTO articles (
        relationshipKey,
        title,
        summary,
        url,
        country,
        relatedCountry,
        published
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    """

    values = (
        article["relationshipKey"],
        article["title"],
        article["summary"],
        article["url"],
        article["country"],
        article["relatedCountry"],
        article["published"]
    )

    try:
        cursor.execute(sql, values)
        connection.commit()
        print("Article inserted successfully.")
    except mysql.connector.errors.IntegrityError:
        print("Duplicate article. Skipping.")

    cursor.close()
    connection.close()