import requests
from bs4 import BeautifulSoup
import re
from serpapi import GoogleSearch
from tavily import TavilyClient
import os
from dotenv import load_dotenv

load_dotenv()

SERP_API_KEY = os.getenv("SERP_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

tavily_client = TavilyClient(api_key=TAVILY_API_KEY)

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

# ---------- INPUT DETECTION ----------
def detect_input(user_input):
    url_pattern = re.compile(
        r'^(https?://)?(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}'
    )
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
        response = requests.get(url, headers=HEADERS, timeout=10)

        if response.status_code != 200:
            return [{"title": "Error", "content": f"Status {response.status_code}", "link": url}]

        soup = BeautifulSoup(response.text, "html.parser")

        title = soup.title.string if soup.title else "No Title"
        paragraphs = soup.find_all("p")

        content = " ".join([
            p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 30
        ])

        if not content:
            content = "Content not available"

        return [{
            "title": title,
            "content": content[:1500],
            "link": url
        }]

    except Exception as e:
        return [{"title": "Error", "content": str(e), "link": url}]


# ---------- SERPAPI ----------
def serp_search(query):
    params = {
        "q": query,
        "api_key": SERP_API_KEY,
        "num": 5
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


# ---------- BING ----------
def bing_search(query):
    try:
        url = f"https://www.bing.com/search?q={query}"
        response = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        links = soup.select("li.b_algo h2 a")[:5]

        data = []
        for item in links:
            data.append({
                "title": item.get_text(),
                "link": item.get("href"),
                "content": "From Bing search"
            })

        return data

    except Exception as e:
        return []


# ---------- TAVILY ----------
def tavily_search(query):
    try:
        res = tavily_client.search(query=query, search_depth="advanced")

        data = []
        for r in res["results"]:
            data.append({
                "title": r["title"],
                "link": r["url"],
                "content": r["content"]
            })

        return data

    except:
        return []


# ---------- FINAL MERGE ----------
def enhanced_scrape(query):
    data = []

    data += serp_search(query)
    data += tavily_search(query)
    data += bing_search(query)

    # remove duplicates
    unique = {item["link"]: item for item in data if item.get("link")}

    return list(unique.values())
