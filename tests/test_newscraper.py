from newscraper import add_article_link, clean_link, repair_text


def test_clean_link_accepts_absolute_url():
    result = clean_link(
        "https://example.com/article/123",
        "https://example.com",
    )

    assert result == "https://example.com/article/123"


def test_clean_link_combines_relative_url():
    result = clean_link(
        "/article/123",
        "https://example.com",
    )

    assert result == "https://example.com/article/123"


def test_clean_link_rejects_invalid_url():
    result = clean_link(
        "article/123",
        "https://example.com",
    )

    assert result is None


def test_add_article_link_adds_valid_article():
    articles = []

    add_article_link(
        articles,
        "A sufficiently long geopolitical article title",
        "https://example.com/article",
        "Example News",
    )

    assert len(articles) == 1
    assert articles[0]["source"] == "Example News"


def test_add_article_link_rejects_short_title():
    articles = []

    add_article_link(
        articles,
        "Short title",
        "https://example.com/article",
        "Example News",
    )

    assert articles == []


def test_repair_text_leaves_normal_text_unchanged():
    text = "China and the United States hold diplomatic talks"

    assert repair_text(text) == text


def test_repair_text_repairs_corrupted_dash():
    result = repair_text("China â€“ United States")

    assert result == "China – United States"