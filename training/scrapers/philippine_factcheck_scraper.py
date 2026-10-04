"""Modular web scraper for Philippine fact-checking datasets.

This script is designed to collect false/misleading claims from:
- VERA Files (https://verafiles.org)
- Tsek.ph (https://tsek.ph)

IMPORTANT:
    Before running this against live pages, manually inspect each site's
    robots.txt and terms of service:
        - https://verafiles.org/robots.txt
        - https://tsek.ph/robots.txt
    and confirm that scraping the specific pages you target is permitted.

This is an academic/research scraper. It includes polite delays and a
User-Agent string to minimize server load.

NOTE:
    The CSS selectors below are placeholders. You must inspect the actual page
    HTML in browser DevTools for both sites and update the selectors to match
    the real structure of the live pages before using this scraper for real.
"""

import csv
import logging
import os
import time
from typing import Dict, Iterable, List, Optional, Set
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
# Add new sources here in the same format to reuse the same scraping flow.
# Each source has:
#   - base_url or listing_urls
#   - link_selectors: CSS selectors for article links on the listing/archive page
#   - title_selectors: CSS selectors for the article title on the detail page
#   - body_selectors: CSS selectors for paragraphs/text blocks on the detail page
#   - request_delay: polite wait between requests, in seconds
#
# IMPORTANT: these selectors are intentionally generic placeholders. The HTML of
# the live pages may differ, so you should inspect the actual site markup with
# browser DevTools and update these values before running the scraper.
SOURCES: Dict[str, dict] = {
    "verafiles": {
        "listing_urls": [
            "https://verafiles.org/fact-check/",
            "https://verafiles.org/fact-check"
        ],
        "link_selectors": [
            "article h2 a[href*='/articles/']",
            "article h3 a[href*='/articles/']",
            "article a[href*='/articles/']",
            "main a[href*='/articles/']",
            ".post-card a[href*='/articles/']",
            ".entry-title a[href*='/articles/']",
        ],
        "title_selectors": [
            "article h1",
            "h1.entry-title",
            "h1.post-title",
            "main h1",
        ],
        "body_selectors": [
            "article .entry-content p",
            "article .post-content p",
            "div.entry-content p",
            ".article-content p",
            "article p",
            "main p",
        ],
        "request_delay": 1.5,
    },
    "tsekph": {
        "listing_urls": [
            "https://www.tsek.ph/category/fact-checks/",
            "https://www.tsek.ph/category/fact-checks"
        ],
        "link_selectors": [
            "article h2 a[href]",
            "article h3 a[href]",
            "article .entry-title a[href]",
            "article a[href*='/']",
            "main article a[href]",
            ".post-card h2 a[href]",
        ],
        "title_selectors": [
            "article h1",
            "article .entry-header h1",
            "h1.entry-title",
            "h1.post-title",
            "main h1",
        ],
        "body_selectors": [
            "article .entry-content p",
            "article .post-content p",
            "div.entry-content p",
            ".article-content p",
            "article p",
            "main p",
        ],
        "request_delay": 1.5,
    },
}


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36 "
        "AcademicResearchBot/1.0 (research dataset collection; contact: researcher@example.com)"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

OUTPUT_CSV = "factcheck_dataset.csv"


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filename="factcheck_scraper.log",
    filemode="a",
)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------
def fetch_html(url: str, headers: Optional[dict] = None, timeout: int = 20) -> Optional[str]:
    """Fetch a page as HTML with error handling."""
    headers = headers or HEADERS
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response.text
    except requests.RequestException as exc:
        logging.warning("Failed to fetch %s: %s", url, exc)
        return None


def clean_text(value: str) -> str:
    """Normalize whitespace and strip empty lines from scraped text."""
    if not value:
        return ""
    return " ".join(value.split())


def first_matching_text(soup: BeautifulSoup, selectors: Iterable[str]) -> str:
    """Return the first matched text for a set of CSS selectors."""
    for selector in selectors:
        element = soup.select_one(selector)
        if element:
            text = clean_text(element.get_text(" ", strip=True))
            if text:
                return text
    return ""


def extract_text_blocks(soup: BeautifulSoup, selectors: Iterable[str]) -> List[str]:
    """Collect text blocks from a page using the given selectors."""
    blocks: List[str] = []
    for selector in selectors:
        for tag in soup.select(selector):
            text = clean_text(tag.get_text(" ", strip=True))
            if text:
                blocks.append(text)
    return blocks


def normalize_article_url(raw_url: str, page_url: str) -> str:
    """Convert relative article URLs to absolute URLs where needed."""
    if not raw_url:
        return ""
    cleaned = raw_url.strip()
    if cleaned.startswith("/"):
        return urljoin(page_url, cleaned)
    if cleaned.startswith("http://") or cleaned.startswith("https://"):
        return cleaned
    return urljoin(page_url, cleaned)


def extract_article_links(page_html: str, page_url: str, selectors: Iterable[str]) -> List[str]:
    """Extract unique article URLs from a listing page using the configured selectors."""
    soup = BeautifulSoup(page_html, "html.parser")
    links: Set[str] = set()

    for selector in selectors:
        for a_tag in soup.select(selector):
            href = a_tag.get("href")
            if not href:
                continue
            article_url = normalize_article_url(str(href), page_url)
            if article_url and "http" in article_url:
                links.add(article_url)

    return sorted(links)


def scrape_article_detail(article_url: str, config: dict, headers: Optional[dict] = None) -> Optional[dict]:
    """Scrape one article page and return {title, text, url}."""
    headers = headers or HEADERS
    article_html = fetch_html(article_url, headers=headers)
    if not article_html:
        return None

    soup = BeautifulSoup(article_html, "html.parser")

    title = first_matching_text(soup, config.get("title_selectors", []))
    body_paragraphs = extract_text_blocks(soup, config.get("body_selectors", []))
    body_text = "\n".join(body_paragraphs)

    if not title and not body_text:
        logging.warning("Article at %s returned no usable title/body content.", article_url)
        return None

    return {
        "url": article_url,
        "title": clean_text(title),
        "text": clean_text(body_text),
    }


def iter_listing_pages(source_name: str, config: dict) -> Iterable[str]:
    """Yield candidate listing URLs for a source."""
    for url in config.get("listing_urls", []):
        yield url


def scrape_source(source_name: str, config: dict, output_rows: List[dict], delay: float = 1.5) -> None:
    """Collect articles for a single source and append them to output_rows."""
    seen_urls: Set[str] = set()

    for listing_url in iter_listing_pages(source_name, config):
        logging.info("Scraping listing page: %s", listing_url)
        page_html = fetch_html(listing_url, headers=HEADERS)
        if not page_html:
            continue

        article_links = extract_article_links(page_html, listing_url, config.get("link_selectors", []))
        if not article_links:
            logging.warning("No article links extracted from listing %s using selectors: %s",
                            listing_url,
                            config.get("link_selectors", []))
            continue

        for article_url in article_links:
            if article_url in seen_urls:
                continue
            seen_urls.add(article_url)

            time.sleep(delay)
            article_data = scrape_article_detail(article_url, config, headers=HEADERS)
            if not article_data:
                logging.warning("Skipping article %s due to failed detail extraction.", article_url)
                continue

            row = {
                "source": source_name,
                "url": article_data["url"],
                "title": article_data["title"],
                "text": article_data["text"],
                "label": "misinformation",
            }
            output_rows.append(row)
            logging.info("Saved article: %s | %s", source_name, article_data["title"])


def save_rows_to_csv(rows: List[dict], output_path: str = OUTPUT_CSV) -> None:
    """Write collected rows to a combined CSV file."""
    fieldnames = ["source", "url", "title", "text", "label"]
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    with open(output_path, "w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({
                "source": row.get("source", ""),
                "url": row.get("url", ""),
                "title": row.get("title", ""),
                "text": row.get("text", ""),
                "label": row.get("label", ""),
            })

    logging.info("Wrote %d records to %s", len(rows), output_path)


def main() -> None:
    """Run the scraper for all configured sources and save a combined CSV."""
    all_rows: List[dict] = []

    for source_name, config in SOURCES.items():
        try:
            logging.info("Starting scrape for source: %s", source_name)
            scrape_source(source_name, config, all_rows, delay=config.get("request_delay", 1.5))
        except Exception as exc:
            logging.exception("Unexpected failure while scraping %s: %s", source_name, exc)
            continue

    save_rows_to_csv(all_rows, OUTPUT_CSV)
    print(f"Scraping complete. Saved {len(all_rows)} records to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
