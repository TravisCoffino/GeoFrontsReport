from google import genai
from dotenv import load_dotenv
from pathlib import Path
import os
import json
from datetime import datetime

# Load .env from the same folder as this file
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

api_key = os.getenv("GEMINI_API_KEY")

if api_key is None:
    raise ValueError("GEMINI_API_KEY was not found. Check your .env file.")

client = genai.Client(api_key=api_key)

def validate_classification(classification):
    if not isinstance(classification, dict):
        return False

    if classification.get("useArticle") is not True:
        return False

    required_text_fields = [
        "title",
        "summary",
        "country",
        "relatedCountry",
        "relationshipKey",
        "published",
    ]

    if any(
        not isinstance(classification.get(field), str)
        or not classification[field].strip()
        for field in required_text_fields
    ):
        return False

    if classification["country"] == classification["relatedCountry"]:
        return False

    try:
        datetime.strptime(classification["published"], "%Y-%m-%d")
    except ValueError:
        return False

    return True

def normalize_classification(classification): #Russia-Ukraine and Ukraine-Russia now the same
    country=classification.get("country")
    related_country=classification.get("relatedCountry")

    if not country or not related_country:
        return classification
    country, related_country=sorted(
        [country.strip(), related_country.strip()],
        key=str.casefold,
    )

    classification["country"]=country
    classification["relatedCountry"] = related_country
    classification["relationshipKey"] = f"{country}-{related_country}"
    return classification

def classify_article(title, url, article_text):
    prompt = f"""
You are helping build an interactive world geopolitics relationship map.

Only accept articles that are useful international geopolitical stories.

Accept:
- war between countries
- military conflict
- sanctions
- diplomacy
- international trade disputes
- alliances
- foreign policy
- cross-border tensions
- major international leadership events
- relations between two or more countries

Reject:
- sports
- archaeology
- entertainment
- domestic crime
- domestic elections unless clearly foreign-policy related
- local US politics
- celebrity news
- weather
- lifestyle
- random historical discoveries
- generic website navigation pages
- newsletter signup pages
- homepage text
- category pages

Return ONLY valid JSON.

If useful, return:
{{
  "useArticle": true,
  "title": "Clean actual article title",
  "summary": "One short sentence explaining the geopolitical relationship.",
  "country": "Country A",
  "relatedCountry": "Country B",
  "relationshipKey": "Country A-Country B",
  "published": "YYYY-MM-DD"
}}

If not useful, return:
{{
  "useArticle": false,
  "title": null,
  "summary": null,
  "country": null,
  "relatedCountry": null,
  "relationshipKey": null,
  "published": null
}}

Rules:
- For "title", return the clean actual article title only.
- Remove dates, section names, author names, duplicate text, summaries, and website text from the title.
- For "published", return the actual article published date in YYYY-MM-DD format.
- Do not use today's date unless the article page clearly says that is the published date.
- If the published date is unclear, return null.
- Use full country names, not abbreviations. Use "United States", not "US".
- For relationshipKey, use the same full country names as country and relatedCountry.
- Example: "Iran-United States", not "Iran-US".
- Reject the article if you cannot identify two meaningful geopolitical countries or entities.


Scraped title:
{title}

Article URL:
{url}

Article text:
{article_text[:5000]}
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    text = response.text.strip()

    # Remove markdown formatting if Gemini accidentally adds it
    text = text.replace("```json", "")
    text = text.replace("```", "")
    text = text.strip()

    classification = json.loads(text)
    return normalize_classification(classification)