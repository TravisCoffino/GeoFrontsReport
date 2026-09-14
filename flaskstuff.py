from flask import Flask, render_template
import json
from pathlib import Path

app = Flask(__name__)

PROJECT_DIR = Path(__file__).resolve().parent
STATIC_DIR = PROJECT_DIR / "static"


@app.route("/")
def home():
    return render_template("index.html")

@app.route("/articles")
def get_articles():
    with (STATIC_DIR / "articles.json").open("r", encoding="utf-8") as file:
        articles = json.load(file)

    return articles


@app.route("/coords")
def get_coords():
    with (STATIC_DIR / "FixedGeoLoc.json").open("r", encoding="utf-8") as file:
        coords = json.load(file)

    return coords

if __name__ == "__main__":
    app.run(debug=True)
