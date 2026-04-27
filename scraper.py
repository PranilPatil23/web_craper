import requests
from bs4 import BeautifulSoup
import urllib.parse

HEADERS = {"User-Agent": "Mozilla/5.0"}

# ---------- URL SCRAPER ----------
def scrape_static(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        data = []

        for tag in soup.find_all(["h1", "h2", "h3", "p", "a"]):
            text = tag.get_text(strip=True)
            link = tag.get("href") if tag.name == "a" else ""

            data.append({
                "tag": tag.name,
                "text": text,
                "link": link
            })

        return data

    except Exception as e:
        return {"error": str(e)}


# ---------- KEYWORD SCRAPER ----------
def scrape_by_keyword(keyword):
    try:
        import urllib.parse

        query = urllib.parse.quote(keyword)
        url = f"https://www.bing.com/search?q={query}"

        response = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(response.text, "html.parser")

        data = []

        for item in soup.select("li.b_algo h2 a"):
            data.append({
                "tag": "result",
                "text": item.get_text(),
                "link": item.get("href")
            })

        return data

    except Exception as e:
        return {"error": str(e)}