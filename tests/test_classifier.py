from classifyArticle import (
    normalize_classification,
    validate_classification,
)


def valid_classification():
    return {
        "useArticle": True,
        "title": "China and the United States hold talks",
        "summary": "The countries discussed their diplomatic relationship.",
        "country": "China",
        "relatedCountry": "United States",
        "relationshipKey": "China-United States",
        "published": "2026-08-04",
    }


def test_valid_classification_is_accepted():
    classification = valid_classification()

    assert validate_classification(classification) is True


def test_missing_date_is_rejected():
    classification = valid_classification()
    classification["published"] = None

    assert validate_classification(classification) is False


def test_invalid_date_format_is_rejected():
    classification = valid_classification()
    classification["published"] = "August 4, 2026"

    assert validate_classification(classification) is False


def test_same_country_is_rejected():
    classification = valid_classification()
    classification["relatedCountry"] = "China"

    assert validate_classification(classification) is False


def test_relationship_is_normalized():
    classification = {
        "country": "Ukraine",
        "relatedCountry": "Russia",
    }

    result = normalize_classification(classification)

    assert result["country"] == "Russia"
    assert result["relatedCountry"] == "Ukraine"
    assert result["relationshipKey"] == "Russia-Ukraine"


def test_normalization_removes_extra_spaces():
    classification = {
        "country": "  United States ",
        "relatedCountry": " Canada  ",
    }

    result = normalize_classification(classification)

    assert result["country"] == "Canada"
    assert result["relatedCountry"] == "United States"
    assert result["relationshipKey"] == "Canada-United States"