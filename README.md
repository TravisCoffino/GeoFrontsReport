# The Geo Fronts Report

The Geo Fronts Report is a website used to scrape articles from multiple renowed news sources, filter them and classify them based on a two-country relationship to see current geopolitical news stories on an interactive map.

## Features

* Scrapes articles from multiple sources, such as the Wall Street Journal and Reuters
* Filters unrelated stories, ensuring only geopolitical articles appear
* Classifies geopolitical relationships in each article using Gemini
* Validates and normalizes article data (Denmark-Germany = Germany-Denmark)
* Displays accepted articles on open source maps
* Groups recent articles by country relationship pair
* Automation for cleaning data found in articles (repairing text, normalizing classifications, etc.)

## Technologies Used

* Python
* Flask
* Beautiful Soup
* Google Gemini API
* JavaScript
* Leaflet / Carto / OpenStreetMap
* Pytest

## Setup

Clone the repository and enter the project's directory:

```python
git clone <repo-url>
cd GeoMap
```

Create and activate a virtual environment:

```python
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install all dependencies:

```python
pip install -r requirements.txt
```

Create an .env file in the project directory (don't commit it)

```python
GEMINI_API_KEY=your_api_key_here
```

## Running the website

```python
py flaskstuff.py
```

Then, open httpL//127.0.0.1:5000 in a browser.

## Running the news scraper

```python
py newscraper.py
```

This scrapes and verifies articles, sends to Gemini, checks results and saves them to articles.json. You can check its progress in the terminal.

## Checking for errors

```python
pytest -v
```

## Acknowledgements

Thank you to Leaflet, CARTO, and OpenStreetMap for the open-source maps used to visualize articles on maps of the world.

## License

[MIT](https://choosealicense.com/licenses/mit/)