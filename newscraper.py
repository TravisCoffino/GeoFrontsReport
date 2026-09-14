import requests
from bs4 import BeautifulSoup
from datetime import date, datetime, timedelta
import json
from pathlib import Path
from classifyArticle import classify_article, validate_classification

headers = {
    "User-Agent": "Mozilla/5.0"
}

output_path = Path(__file__).parent / "static" / "articles.json"
backup_path = Path(__file__).parent / "static" / "articles_backup.json"


# -------------------------
# Helper functions
# -------------------------

def clean_link(link, base_url):
    if link.startswith("http"):
        return link

    if link.startswith("/"):
        return base_url + link

    return None


def add_article_link(article_links, title, link, source):
    if not title or not link:
        return

    title = " ".join(title.split())

    if len(title) < 20:
        return

    article = {
        "title": title,
        "url": link,
        "source": source
    }

    article_links.append(article)


# -------------------------
# Source scrapers
# -------------------------

def scrape_ap_world():
    print("Scraping AP News...")

    article_links = []
    url = "https://apnews.com/hub/international-relations"

    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    links = soup.find_all("a")

    for link_element in links:
        title = link_element.get_text(strip=True)
        link = link_element.get("href")

        if not link:
            continue

        if "/article/" not in link:
            continue

        link = clean_link(link, "https://apnews.com")

        if link:
            add_article_link(article_links, title, link, "AP News")

    return article_links


def scrape_reuters_world():
    print("Scraping Reuters...")

    article_links = []
    url = "https://www.reuters.com/world/"

    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    links = soup.find_all("a")

    for link_element in links:
        title = link_element.get_text(strip=True)
        link = link_element.get("href")

        if not link:
            continue

        if "/world/" not in link:
            continue

        link = clean_link(link, "https://www.reuters.com")

        if link:
            add_article_link(article_links, title, link, "Reuters")

    return article_links


def scrape_nyt_world():
    print("Scraping New York Times...")

    article_links = []
    url = "https://www.nytimes.com/topic/subject/international-relations?eafs_enabled=false"

    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    links = soup.find_all("a")

    for link_element in links:
        title = link_element.get_text(strip=True)
        link = link_element.get("href")

        if not link:
            continue

        if "/202" not in link:
            continue

        link = clean_link(link, "https://www.nytimes.com")

        if link:
            add_article_link(article_links, title, link, "New York Times")

    return article_links


def scrape_wsj_world():
    print("Scraping Wall Street Journal...")

    article_links = []
    url = "https://www.wsj.com/world"

    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    links = soup.find_all("a")

    for link_element in links:
        title = link_element.get_text(strip=True)
        link = link_element.get("href")

        if not link:
            continue

        if "wsj.com" not in link and not link.startswith("/"):
            continue

        link = clean_link(link, "https://www.wsj.com")

        if link:
            add_article_link(article_links, title, link, "Wall Street Journal")

    return article_links


def scrape_diplomat():
    print("Scraping The Diplomat...")

    article_links = []
    url = "https://thediplomat.com/"

    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    links = soup.find_all("a")

    for link_element in links:
        title = link_element.get_text(strip=True)
        link = link_element.get("href")

        if not link:
            continue

        link = clean_link(link, "https://thediplomat.com")

        if not link:
            continue

        if "thediplomat.com" not in link:
            continue

        add_article_link(article_links, title, link, "The Diplomat")

    return article_links


def repair_text(value):
    if not isinstance(value, str):
        return value

    try:
        return value.encode("windows-1252").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return value


def main():
    print("RUNNING MULTI-SOURCE GEMINI SCRAPER")
    print("This script is located at:", Path(__file__).resolve())
    print("Current working folder:", Path.cwd())

    if output_path.exists():
        with open(output_path, "r", encoding="utf-8") as file:
            saved_articles = json.load(file)

        with open(backup_path, "w", encoding="utf-8") as file:
            json.dump(saved_articles, file, indent=4, ensure_ascii=False)

        print("Loaded old articles:", len(saved_articles))
    else:
        saved_articles = []
        print("No old articles file found.")

    retention_days = 60
    cutoff_date = date.today() - timedelta(days=retention_days)
    recent_articles = []

    for article in saved_articles:
        try:
            article_date = datetime.strptime(
                article["published"], "%Y-%m-%d"
            ).date()

            if article_date >= cutoff_date:
                recent_articles.append(article)
            else:
                print("Removed old article:", article.get("title", "No title"))
        except (KeyError, TypeError, ValueError):
            print(
                "Kept article with bad/missing date:",
                article.get("title", "No title"),
            )
            recent_articles.append(article)

    saved_articles = recent_articles
    seen_links = {
        article["url"]
        for article in saved_articles
        if article.get("url")
    }

    print("Existing articles kept:", len(saved_articles))

    all_scraped_links = []
    source_functions = [
        scrape_ap_world,
        scrape_reuters_world,
        scrape_nyt_world,
        scrape_wsj_world,
        scrape_diplomat,
    ]
    max_links_per_source = 20

    for scrape_function in source_functions:
        try:
            source_articles = scrape_function()
            print("Found from source:", len(source_articles))
            all_scraped_links.extend(source_articles[:max_links_per_source])
        except Exception as error:
            print("Source failed:", scrape_function.__name__)
            print("Error:", error)

    print(
        "Total scraped links after per-source limit:",
        len(all_scraped_links),
    )

    source_counts = {}
    for article in all_scraped_links:
        source = article["source"]
        source_counts[source] = source_counts.get(source, 0) + 1

    print("Links going to Gemini pool:", source_counts)

    bad_keywords = [
        "fifa", "uefa", "world cup", "sports", "archaeological",
        "gold rings", "celebrity", "movie", "music", "recipe",
        "fashion", "weather", "lottery", "nfl", "nba", "mlb",
        "soccer", "tennis",
    ]

    checked_count = 0
    max_gemini_checks = 40
    source_results = {
        source: {
            "candidates": count,
            "duplicates": 0,
            "keyword_skips": 0,
            "checked": 0,
            "open_failures": 0,
            "gemini_failures": 0,
            "rejected": 0,
            "accepted": 0,
        }
        for source, count in source_counts.items()
    }

    for scraped_article in all_scraped_links:
        title = scraped_article["title"]
        link = scraped_article["url"]
        source = scraped_article["source"]

        if link in seen_links:
            source_results[source]["duplicates"] += 1
            print("Already saved:", title)
            continue

        if any(keyword in title.lower() for keyword in bad_keywords):
            source_results[source]["keyword_skips"] += 1
            print("Skipped before Gemini:", title)
            continue

        

        print("Opening article:", title)
        print("Source:", source)

        try:
            article_response = requests.get(link, headers=headers, timeout=10)
            article_response.raise_for_status()
        except requests.RequestException as error:
            source_results[source]["open_failures"] += 1
            print("Failed to open article:", title)
            print("Error:", error)
            continue

        article_soup = BeautifulSoup(article_response.text, "html.parser")
        page_text = article_soup.get_text(" ", strip=True)

        if len(page_text) < 300:
            print("Skipped because article text was too short:", title)
            continue

        if checked_count >= max_gemini_checks:
            print("Reached Gemini check limit.")
            break

        checked_count += 1
        source_results[source]["checked"] += 1
        
        print("Asking Gemini:", title)

        try:
            classification = classify_article(title, link, page_text)
            print("Gemini result:", classification)
        except KeyboardInterrupt:
            print("Stopped by user. Saving what we have so far...")
            break
        except Exception as error:
            source_results[source]["gemini_failures"] += 1
            print("Gemini failed on:", title)
            print("Error:", error)
            continue

        if classification.get("useArticle") is not True:
            source_results[source]["rejected"] += 1
            print("Rejected:", title)
            continue

        if not validate_classification(classification):
            source_results[source]["rejected"] += 1
            print("Rejected invalid classification:", title)
            continue

        article = {
            "relationshipKey": classification["relationshipKey"],
            "title": repair_text(classification["title"]),
            "summary": repair_text(classification["summary"]),
            "url": link,
            "country": classification["country"],
            "relatedCountry": classification["relatedCountry"],
            "published": classification["published"],
            "source": source,
        }

        saved_articles.append(article)
        seen_links.add(link)
        source_results[source]["accepted"] += 1

        with open(output_path, "w", encoding="utf-8") as file:
            json.dump(saved_articles, file, indent=4, ensure_ascii=False)

        print("Accepted and saved:", article["title"])

        if len(saved_articles) >= 100:
            print("Reached saved article limit.")
            break

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(saved_articles, file, indent=4, ensure_ascii=False)

    print("Saved articles.json at:", output_path)
    print("Backup saved at:", backup_path)
    print("Total articles kept:", len(saved_articles))
    print("Retention window (days):", retention_days)
    print("\nPer-source results:")

    for source, results in source_results.items():
        print(source + ":")
        for result_name, result_count in results.items():
            print("  " + result_name + ":", result_count)


if __name__ == "__main__":
    main()
