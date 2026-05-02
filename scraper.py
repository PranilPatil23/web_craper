import requests
from bs4 import BeautifulSoup
import urllib.parse
import re
from serpapi import GoogleSearch
from tavily import TavilyClient
import os
from dotenv import load_dotenv

load_dotenv()

SERP_API_KEY = os.getenv("SERP_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

# ---------- INPUT DETECTION ----------
def detect_input(user_input):
    url_pattern = re.compile(r'^(https?://)?(www\.)?\S+\.\S+')
    if url_pattern.match(user_input.strip()):
        return "url"
    return "keyword"

def fix_url(url):
    if not url.startswith("http"):
        return "https://" + url
    return url

# ---------- URL SCRAPER ----------
def scrape_static(url):
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")

        title = soup.title.string if soup.title else "No Title"
        paragraphs = soup.find_all("p")

        content = " ".join([p.get_text() for p in paragraphs[:10]])

        return [{
            "title": title,
            "content": content if content else "No content",
            "link": url
        }]

    except Exception as e:
        return [{"title": "Error", "content": str(e), "link": url}]

# ---------- BING ----------
def scrape_by_bing(query):
    url = f"https://www.bing.com/search?q={urllib.parse.quote(query)}"
    res = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(res.text, "html.parser")

    data = []
    for item in soup.select("li.b_algo h2 a")[:5]:
        data.append({
            "title": item.get_text(),
            "link": item.get("href"),
            "content": "Bing result"
        })
    return data

# ---------- SERPAPI ----------
def serp_search(query):
    params = {
        "q": query,
        "api_key": SERP_API_KEY
    }

    search = GoogleSearch(params)
    results = search.get_dict()

    data = []
    for r in results.get("organic_results", []):
        data.append({
            "title": r.get("title"),
            "link": r.get("link"),
            "content": r.get("snippet")
        })

    return data

# ---------- TAVILY ----------
tavily_client = TavilyClient(api_key=TAVILY_API_KEY)

def tavily_search(query):
    res = tavily_client.search(query=query)

    data = []
    for r in res["results"]:
        data.append({
            "title": r["title"],
            "link": r["url"],
            "content": r["content"]
        })

    return data

# ---------- MAIN ----------
def enhanced_scrape(query, engine="bing"):
    if engine == "bing":
        return scrape_by_bing(query)

    elif engine == "serpapi":
        return serp_search(query)

    elif engine == "tavily":
        return tavily_search(query)

    return scrape_by_bing(query)
