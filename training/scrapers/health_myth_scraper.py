"""Targeted health-myth search scraper for VERA Files and Tsek.ph.

This version searches each site using health-vaccine medicine keywords and then
only keeps pages whose article text matches explicit medical myth markers.
"""

import csv
import logging
import time
from typing import Dict, Iterable, List, Optional, Set
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

OUTPUT_CSV = "health_myth_factchecks.csv"

SOURCES: Dict[str, dict] = {
    "verafiles": {
        "search_terms": [
            "vaccine",
            "covid",
            "medicine",
            "medical misinformation",
            "fake vaccine",
            "miracle cure",
            "health scam",
            "booster",
            "bakuna",
            "public health",
        ],
        "search_url_template": "https://verafiles.org/?s={term}",
        "link_selectors": [
            "article h2 a[href]",
            "article h3 a[href]",
            "main article a[href]",
            "article a[href*='/articles/']",
            "a[href*='/articles/']",
        ],
        "title_selectors": ["article h1", "main h1", "h1.entry-title", "h1"],
        "body_selectors": ["article .entry-content p", "article p", "main p"],
        "request_delay": 1.5,
    },
    "tsekph": {
        "search_terms": [
            "vaccine",
            "covid",
            "medicine",
            "health",
            "bakuna",
            "doctor",
            "medical misinformation",
            "miracle cure",
        ],
        "search_url_template": "https://www.tsek.ph/?s={term}",
        "link_selectors": [
            "article h2 a[href]",
            "article h3 a[href]",
            "main article a[href]",
            "article a[href]",
            "a[href*='/']",
        ],
        "title_selectors": ["article h1", "main h1", "h1.entry-title", "h1"],
        "body_selectors": ["article .entry-content p", "article p", "main p"],
        "request_delay": 1.5,
    },
}

MYTH_MARKERS = [
    "miracle cure", "miraculous cure", "guaranteed cure", "instant cure",
    "natural cure", "cure-all", "cure all", "fake vaccine", "vaccine scam",
    "bakuna scam", "booster scam", "covid cure", "health scam",
    "medical scam", "doctor don't want you to know", "hidden cure",
    "secret ingredient", "no side effects", "walang side effects",
    "replace medicine", "kapalit ng gamot", "miracle drug", "works for everything",
    "treats all diseases", "public health hoax", "medical misinformation",
]

HEALTH_CONTEXT = [
    "vaccine", "bakuna", "covid", "medicine", "gamot", "doctor", "doktor",
    "hospital", "ospital", "health", "medical", "clinic", "patient",
    "pasyente", "disease", "sakit", "cure", "lunas", "remedy", "symptom",
    "treatment", "therapy", "public health", "nurse", "flu", "booster",
    "pandemic", "immunization", "antivax", "anti-vax",
]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filename="health_myth_scraper.log",
    filemode="a",
)


def clean_text(value: str) -> str:
    if not value:
        return ""
    return " ".join(value.split())


def fetch_html(url: str, timeout: int = 25) -> Optional[str]:
    try:
        response = requests.get(url, headers=HEADERS, timeout=timeout)
        response.raise_for_status()
        return response.text
    except requests.RequestException as exc:
        logging.warning("Failed to fetch %s: %s", url, exc)
        return None


def normalize_url(raw_url: str, page_url: str) -> str:
    if not raw_url:
        return ""
    href = raw_url.strip()
    if href.startswith("/"):
        return urljoin(page_url, href)
    if href.startswith("http://") or href.startswith("https://"):
        return href
    return urljoin(page_url, href)


def first_text(soup: BeautifulSoup, selectors: Iterable[str]) -> str:
    for selector in selectors:
        found = soup.select_one(selector)
        if found:
            text = clean_text(found.get_text(" ", strip=True))
            if text:
                return text
    return ""


def collect_paragraphs(soup: BeautifulSoup, selectors: Iterable[str]) -> List[str]:
    paragraphs: List[str] = []
    for selector in selectors:
        for tag in soup.select(selector):
            text = clean_text(tag.get_text(" ", strip=True))
            if text:
                paragraphs.append(text)
    return paragraphs


def extract_candidate_links(page_html: str, page_url: str, selectors: Iterable[str]) -> List[str]:
    soup = BeautifulSoup(page_html, "html.parser")
    seen: Set[str] = set()
    links: List[str] = []
    for selector in selectors:
        for tag in soup.select(selector):
            href = tag.get("href")
            if not href:
                continue
            normalized = normalize_url(str(href), page_url)
            if normalized.startswith("http") and normalized not in seen:
                seen.add(normalized)
                links.append(normalized)
    return links


def is_health_myth_article(title: str, text: str) -> bool:
    combined = (title or "") + " " + (text or "")
    combined = combined.lower()
    if not combined.strip():
        return False

    has_myth = any(marker in combined for marker in MYTH_MARKERS)
    has_health = any(context in combined for context in HEALTH_CONTEXT)
    return has_myth and has_health


def scrape_article(article_url: str, config: dict) -> Optional[dict]:
    html = fetch_html(article_url)
    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")
    title = first_text(soup, config.get("title_selectors", []))
    paragraphs = collect_paragraphs(soup, config.get("body_selectors", []))
    body = "\n".join(paragraphs)

    if not title and not body:
        return None

    if not is_health_myth_article(title, body):
        return None

    return {"url": article_url, "title": clean_text(title), "text": clean_text(body)}


def scrape_source(source_name: str, config: dict, rows: List[dict]) -> None:
    seen_articles: Set[str] = set()
    for term in config.get("search_terms", []):
        search_url = config["search_url_template"].format(term=term)
        logging.info("Searching %s for %s", source_name, term)
        page_html = fetch_html(search_url)
        if not page_html:
            continue

        for candidate_url in extract_candidate_links(page_html, search_url, config.get("link_selectors", [])):
            if candidate_url in seen_articles:
                continue
            seen_articles.add(candidate_url)

            if "/?s=" in candidate_url or "search" in candidate_url.lower() or "page/" in candidate_url.lower():
                continue

            time.sleep(config.get("request_delay", 1.5))
            article = scrape_article(candidate_url, config)
            if not article:
                continue

            rows.append({
                "source": source_name,
                "url": article["url"],
                "title": article["title"],
                "text": article["text"],
                "label": "misinformation",
            })
            logging.info("Saved %s: %s", source_name, article["title"])


def save_rows(rows: List[dict], output_path: str = OUTPUT_CSV) -> None:
    with open(output_path, "w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=["source", "url", "title", "text", "label"])
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main() -> None:
    rows: List[dict] = []
    for source_name, config in SOURCES.items():
        try:
            scrape_source(source_name, config, rows)
        except Exception as exc:
            logging.exception("Unexpected error while scraping %s: %s", source_name, exc)

    save_rows(rows)
    print(f"Scraping complete. Saved {len(rows)} health-myth records to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
