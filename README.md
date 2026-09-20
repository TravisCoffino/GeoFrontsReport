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

Geo Fronts is now hosted on Vercel! Visit: https://geofrontsreport.vercel.app to view it!

## Acknowledgements

Thank you to Leaflet, CARTO, and OpenStreetMap for the open-source maps used to visualize articles on maps of the world.

## License

[MIT](https://choosealicense.com/licenses/mit/)
