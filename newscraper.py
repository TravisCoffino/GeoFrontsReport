import json
import os
import time
import xml.etree.ElementTree as ElementTree
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from classifyArticle import (
    classify_article as classifyArticle,
    validate_classification as validateClassification,
)


requestHeaders = {
    "User-Agent": "GeoFrontsReport/1.0 (geopolitical news aggregator)"
}

outputPath = Path(__file__).parent / "static" / "articles.json"
backupPath = Path(__file__).parent / "static" / "articles_backup.json"


# Sources are interleaved below, so no publisher consumes the check budget.
sourceLimits = {
    "AP News": 30,
    "Reuters": 40,
    "New York Times": 25,
    "Wall Street Journal": 25,
    "The Diplomat": 35,
    "BBC News": 50,
    "Al Jazeera": 50,
    "Deutsche Welle": 40,
    "France 24": 40,
    "Voice of America": 60,
    "Politico Europe": 35,
    "UN News": 35,
    "ReliefWeb": 40,
    "GDELT": 60,
    "Council on Foreign Relations": 25,
}


def cleanLink(link, baseUrl):
    if not link:
        return None
    if link.startswith(("http://", "https://")):
        return link
    if link.startswith("/"):
        return urljoin(baseUrl, link)
    return None


def addArticleLink(articleLinks, title, link, source):
    if not title or not link:
        return

    title = " ".join(title.split())
    if len(title) < 20:
        return
    if any(article["url"] == link for article in articleLinks):
        return

    articleLinks.append({
        "title": title,
        "url": link,
        "source": source,
    })


def elementName(element):
    return element.tag.rsplit("}", 1)[-1].lower()


def childText(element, acceptedNames):
    for child in element:
        if elementName(child) in acceptedNames and child.text:
            return child.text.strip()
    return None


def scrapeRssFeed(feedUrl, source):
    response = requests.get(feedUrl, headers=requestHeaders, timeout=15)
    response.raise_for_status()
    root = ElementTree.fromstring(response.content)
    articleLinks = []

    for entry in root.iter():
        if elementName(entry) not in {"item", "entry"}:
            continue

        title = childText(entry, {"title"})
        link = childText(entry, {"link"})

        if not link:
            for child in entry:
                if elementName(child) == "link" and child.get("href"):
                    link = child.get("href")
                    break

        addArticleLink(articleLinks, title, cleanLink(link, feedUrl), source)

    return articleLinks


def scrapeMultipleFeeds(feedUrls, source):
    articleLinks = []

    for feedUrl in feedUrls:
        try:
            for article in scrapeRssFeed(feedUrl, source):
                addArticleLink(
                    articleLinks,
                    article["title"],
                    article["url"],
                    source,
                )
        except (requests.RequestException, ElementTree.ParseError) as error:
            print("Feed failed:", feedUrl)
            print("Error:", error)

    return articleLinks


def scrapeHtmlListing(url, source, allowedPathParts):
    response = requests.get(url, headers=requestHeaders, timeout=15)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    articleLinks = []
    sourceHost = urlparse(url).netloc

    for linkElement in soup.find_all("a"):
        title = linkElement.get_text(" ", strip=True)
        link = cleanLink(linkElement.get("href"), url)

        if not link or urlparse(link).netloc != sourceHost:
            continue
        if allowedPathParts and not any(
            pathPart in urlparse(link).path for pathPart in allowedPathParts
        ):
            continue

        addArticleLink(articleLinks, title, link, source)

    return articleLinks


def scrapeApWorld():
    print("Scraping AP News...")
    return scrapeHtmlListing(
        "https://apnews.com/hub/international-relations",
        "AP News",
        ["/article/"],
    )


def scrapeReutersWorld():
    print("Scraping Reuters...")
    return scrapeHtmlListing(
        "https://www.reuters.com/world/", "Reuters", ["/world/"]
    )


def scrapeNytWorld():
    print("Scraping New York Times...")
    return scrapeRssFeed(
        "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
        "New York Times",
    )


def scrapeWsjWorld():
    print("Scraping Wall Street Journal...")
    return scrapeRssFeed(
        "https://feeds.a.dj.com/rss/RSSWorldNews.xml",
        "Wall Street Journal",
    )


def scrapeDiplomat():
    print("Scraping The Diplomat...")
    return scrapeHtmlListing(
        "https://thediplomat.com/", "The Diplomat", ["/20"]
    )


def scrapeBbcWorld():
    print("Scraping BBC News...")
    return scrapeRssFeed(
        "https://feeds.bbci.co.uk/news/world/rss.xml", "BBC News"
    )


def scrapeAlJazeera():
    print("Scraping Al Jazeera...")
    return scrapeRssFeed(
        "https://www.aljazeera.com/xml/rss/all.xml", "Al Jazeera"
    )


def scrapeDeutscheWelle():
    print("Scraping Deutsche Welle...")
    return scrapeRssFeed(
        "https://rss.dw.com/rdf/rss-en-top", "Deutsche Welle"
    )


def scrapeFrance24():
    print("Scraping France 24...")
    return scrapeRssFeed("https://www.france24.com/en/rss", "France 24")


def scrapeVoiceOfAmerica():
    print("Scraping Voice of America...")
    feedUrls = [
        "https://www.voanews.com/api/z-botl-vomx-tpertmq",  # Africa
        "https://www.voanews.com/api/zobo_l-vomx-tpepvmv",  # East Asia
        "https://www.voanews.com/api/zmjuqtl-vomx-tpey_jqq",  # China
        "https://www.voanews.com/api/z_-mqyl-vomx-tpevyvqv",  # S/C Asia
        "https://www.voanews.com/api/zrbopl-vomx-tpeovm_",  # Middle East
        "https://www.voanews.com/api/zvgmqil-vomx-tpeumvqm",  # Iran
        "https://www.voanews.com/api/zjbovl-vomx-tpebvmr",  # Europe
        "https://www.voanews.com/api/zt_rqyl-vomx-tpekboq_",  # Ukraine
        "https://www.voanews.com/api/zoripl-vomx-tpeptmm",  # Americas
    ]
    return scrapeMultipleFeeds(feedUrls, "Voice of America")


def scrapePoliticoEurope():
    print("Scraping Politico Europe...")
    return scrapeRssFeed(
        "https://www.politico.eu/feed/", "Politico Europe"
    )


def scrapeUnNews():
    print("Scraping UN News...")
    return scrapeRssFeed(
        "https://news.un.org/feed/subscribe/en/news/all/rss.xml", "UN News"
    )


def scrapeReliefWeb():
    print("Scraping ReliefWeb...")
    appName = os.getenv("RELIEFWEB_APP_NAME")
    if not appName:
        print(
            "Skipping ReliefWeb: set RELIEFWEB_APP_NAME to an approved "
            "ReliefWeb app name."
        )
        return []

    response = requests.get(
        "https://api.reliefweb.int/v2/reports",
        params={
            "appname": appName,
            "limit": 100,
            "profile": "list",
            "sort[]": "date:desc",
        },
        headers=requestHeaders,
        timeout=20,
    )
    response.raise_for_status()
    articleLinks = []

    for result in response.json().get("data", []):
        fields = result.get("fields", {})
        link = fields.get("url_alias") or fields.get("url")
        if link and link.startswith("/"):
            link = urljoin("https://reliefweb.int", link)
        addArticleLink(
            articleLinks, fields.get("title"), link, "ReliefWeb"
        )

    return articleLinks


def scrapeGdelt():
    print("Scraping GDELT...")
    query = (
        '(diplomacy OR sanctions OR military OR conflict OR treaty OR NATO '
        'OR "foreign policy" OR "international relations")'
    )
    requestParams = {
        "query": query,
        "mode": "artlist",
        "maxrecords": 250,
        "timespan": "3d",
        "sort": "datedesc",
        "format": "json",
    }

    for attempt in range(3):
        response = requests.get(
            "https://api.gdeltproject.org/api/v2/doc/doc",
            params=requestParams,
            headers=requestHeaders,
            timeout=30,
        )
        if response.status_code != 429 or attempt == 2:
            break

        retryDelay = min(5 * (attempt + 1), 10)
        print("GDELT rate limited; retrying in", retryDelay, "seconds...")
        time.sleep(retryDelay)

    response.raise_for_status()
    articleLinks = []

    for result in response.json().get("articles", []):
        if result.get("language", "").lower() not in {"", "english"}:
            continue
        addArticleLink(
            articleLinks,
            result.get("title"),
            result.get("url"),
            "GDELT",
        )

    return articleLinks


def scrapeCouncilOnForeignRelations():
    print("Scraping Council on Foreign Relations...")
    return scrapeHtmlListing(
        "https://www.cfr.org/",
        "Council on Foreign Relations",
        ["/article", "/backgrounder", "/expert-brief", "/blog/"],
    )


def repairText(value):
    if not isinstance(value, str):
        return value
    try:
        return value.encode("windows-1252").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return value


def interleaveSourceArticles(sourceBatches):
    interleavedArticles = []
    longestBatch = max((len(batch) for batch in sourceBatches), default=0)

    for articleIndex in range(longestBatch):
        for batch in sourceBatches:
            if articleIndex < len(batch):
                interleavedArticles.append(batch[articleIndex])

    return interleavedArticles


def main():
    print("RUNNING MULTI-SOURCE GEMINI SCRAPER")
    print("This script is located at:", Path(__file__).resolve())
    print("Current working folder:", Path.cwd())

    if outputPath.exists():
        with outputPath.open("r", encoding="utf-8") as file:
            savedArticles = json.load(file)
        with backupPath.open("w", encoding="utf-8") as file:
            json.dump(savedArticles, file, indent=4, ensure_ascii=False)
        print("Loaded old articles:", len(savedArticles))
    else:
        savedArticles = []
        print("No old articles file found.")

    retentionDays = 30
    cutoffDate = date.today() - timedelta(days=retentionDays)
    recentArticles = []

    for article in savedArticles:
        try:
            articleDate = datetime.strptime(
                article["published"], "%Y-%m-%d"
            ).date()
            if articleDate >= cutoffDate:
                recentArticles.append(article)
            else:
                print("Removed old article:", article.get("title", "No title"))
        except (KeyError, TypeError, ValueError):
            print(
                "Kept article with bad/missing date:",
                article.get("title", "No title"),
            )
            recentArticles.append(article)

    savedArticles = recentArticles
    seenLinks = {
        article["url"] for article in savedArticles if article.get("url")
    }
    print("Existing articles kept:", len(savedArticles))

    sourceCollectors = [
        ("AP News", scrapeApWorld),
        ("Reuters", scrapeReutersWorld),
        ("New York Times", scrapeNytWorld),
        ("Wall Street Journal", scrapeWsjWorld),
        ("The Diplomat", scrapeDiplomat),
        ("BBC News", scrapeBbcWorld),
        ("Al Jazeera", scrapeAlJazeera),
        ("Deutsche Welle", scrapeDeutscheWelle),
        ("France 24", scrapeFrance24),
        ("Voice of America", scrapeVoiceOfAmerica),
        ("Politico Europe", scrapePoliticoEurope),
        ("UN News", scrapeUnNews),
        ("ReliefWeb", scrapeReliefWeb),
        ("GDELT", scrapeGdelt),
        ("Council on Foreign Relations", scrapeCouncilOnForeignRelations),
    ]

    sourceBatches = []
    sourceCounts = {}

    for sourceName, scrapeFunction in sourceCollectors:
        try:
            sourceArticles = scrapeFunction()
            limitedArticles = sourceArticles[:sourceLimits[sourceName]]
            sourceBatches.append(limitedArticles)
            sourceCounts[sourceName] = len(limitedArticles)
            print(
                "Found from source:", len(sourceArticles),
                "using:", len(limitedArticles),
            )
        except Exception as error:
            sourceCounts[sourceName] = 0
            print("Source failed:", scrapeFunction.__name__)
            print("Error:", error)

    allScrapedLinks = interleaveSourceArticles(sourceBatches)
    print("Total scraped links after per-source limits:", len(allScrapedLinks))
    print("Links going to Gemini pool:", sourceCounts)

    badKeywords = [
        "fifa", "uefa", "world cup", "sports", "archaeological",
        "gold rings", "celebrity", "movie", "music", "recipe",
        "fashion", "weather", "lottery", "nfl", "nba", "mlb",
        "soccer", "tennis",
    ]

    checkedCount = 0
    maxGeminiChecks = 30
    sourceResults = {
        source: {
            "candidates": count,
            "duplicates": 0,
            "keywordSkips": 0,
            "checked": 0,
            "openFailures": 0,
            "geminiFailures": 0,
            "rejected": 0,
            "accepted": 0,
        }
        for source, count in sourceCounts.items()
    }

    for scrapedArticle in allScrapedLinks:
        title = scrapedArticle["title"]
        link = scrapedArticle["url"]
        source = scrapedArticle["source"]

        if link in seenLinks:
            sourceResults[source]["duplicates"] += 1
            print("Already saved:", title)
            continue
        if any(keyword in title.lower() for keyword in badKeywords):
            sourceResults[source]["keywordSkips"] += 1
            print("Skipped before Gemini:", title)
            continue

        print("Opening article:", title)
        print("Source:", source)

        try:
            articleResponse = requests.get(
                link, headers=requestHeaders, timeout=15
            )
            articleResponse.raise_for_status()
        except requests.RequestException as error:
            sourceResults[source]["openFailures"] += 1
            print("Failed to open article:", title)
            print("Error:", error)
            continue

        articleSoup = BeautifulSoup(articleResponse.text, "html.parser")
        pageText = articleSoup.get_text(" ", strip=True)

        if len(pageText) < 300:
            sourceResults[source]["openFailures"] += 1
            print("Skipped because article text was too short:", title)
            continue
        if checkedCount >= maxGeminiChecks:
            print("Reached Gemini check limit.")
            break

        checkedCount += 1
        sourceResults[source]["checked"] += 1
        print("Asking Gemini:", title)

        try:
            classification = classifyArticle(title, link, pageText)
            print("Gemini result:", classification)
        except KeyboardInterrupt:
            print("Stopped by user. Saving what we have so far...")
            break
        except Exception as error:
            sourceResults[source]["geminiFailures"] += 1
            print("Gemini failed on:", title)
            print("Error:", error)
            continue

        if classification.get("useArticle") is not True:
            sourceResults[source]["rejected"] += 1
            print("Rejected:", title)
            continue
        if not validateClassification(classification):
            sourceResults[source]["rejected"] += 1
            print("Rejected invalid classification:", title)
            continue

        article = {
            "relationshipKey": classification["relationshipKey"],
            "title": repairText(classification["title"]),
            "summary": repairText(classification["summary"]),
            "url": link,
            "country": classification["country"],
            "relatedCountry": classification["relatedCountry"],
            "published": classification["published"],
            "source": source,
        }

        savedArticles.append(article)
        seenLinks.add(link)
        sourceResults[source]["accepted"] += 1

        with outputPath.open("w", encoding="utf-8") as file:
            json.dump(savedArticles, file, indent=4, ensure_ascii=False)
        print("Accepted and saved:", article["title"])

        if len(savedArticles) >= 100:
            print("Reached saved article limit.")
            break

    with outputPath.open("w", encoding="utf-8") as file:
        json.dump(savedArticles, file, indent=4, ensure_ascii=False)

    print("Saved articles.json at:", outputPath)
    print("Backup saved at:", backupPath)
    print("Total articles kept:", len(savedArticles))
    print("Retention window (days):", retentionDays)
    print("\nPer-source results:")

    for source, results in sourceResults.items():
        print(source + ":")
        for resultName, resultCount in results.items():
            print("  " + resultName + ":", resultCount)


# Compatibility for older imports and existing tests.
clean_link = cleanLink
add_article_link = addArticleLink
repair_text = repairText


if __name__ == "__main__":
    main()
