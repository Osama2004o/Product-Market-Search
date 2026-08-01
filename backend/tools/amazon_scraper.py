"""Amazon scraper tool using high-performance HTTP Session + BeautifulSoup."""

import json
import logging
import re
from typing import Optional
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup
from crewai.tools import BaseTool

try:
    from config import AMAZON_BASE_URL, MAX_PRODUCTS_PER_SITE, SELECTORS, USER_AGENT
    from models.schemas import RawProduct
except ImportError:
    from backend.config import AMAZON_BASE_URL, MAX_PRODUCTS_PER_SITE, SELECTORS, USER_AGENT
    from backend.models.schemas import RawProduct

logger = logging.getLogger(__name__)
sel = SELECTORS["amazon"]


def _scrape_amazon(query: str) -> list[dict]:
    """Search Amazon Egypt using HTTP GET request (fast & low RAM)."""
    url = f"{AMAZON_BASE_URL}/s?k={quote_plus(query)}"
    products = []

    session = requests.Session()
    session.headers.update({
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Sec-Ch-Ua": '"Chromium";v="125", "Not.A/Brand";v="24"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
    })

    try:
        response = session.get(url, timeout=8)
        if response.status_code != 200:
            logger.warning(f"Amazon returned HTTP {response.status_code}")
            return []
        html = response.text
    except Exception as e:
        logger.error(f"Amazon HTTP request failed: {e}")
        return []

    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select("div[data-component-type='s-search-result']")
    if not cards:
        cards = [
            c for c in soup.select("div.s-result-item")
            if c.get("data-sku") or c.select_one("h2")
        ]
    cards = cards[:MAX_PRODUCTS_PER_SITE]

    for card in cards:
        try:
            title_el = card.select_one("h2") or card.select_one("a.a-link-normal")
            title = title_el.get_text(" ", strip=True) if title_el else None
            if (not title or title.lower() in ("samsung", "apple", "xiaomi")) and card.select_one("img.s-image"):
                alt = card.select_one("img.s-image").get("alt")
                if alt:
                    title = alt
            if not title or len(title) < 3:
                continue

            price = _parse_amazon_price(card)

            rating = None
            rating_el = card.select_one(sel["rating"]) or card.select_one("i.a-icon-star")
            if rating_el:
                match = re.search(r"([\d.]+)", rating_el.get_text())
                if match:
                    rating = float(match.group(1))

            review_count = None
            rev_el = card.select_one(sel["review_count"]) or card.select_one("span.a-size-base")
            if rev_el:
                text = rev_el.get_text(strip=True).replace(",", "").replace("(", "").replace(")", "")
                match = re.search(r"(\d+)", text)
                if match:
                    review_count = int(match.group(1))

            url_el = card.select_one(sel["url"]) or card.select_one("h2 a") or card.select_one("a.a-link-normal")
            product_url = None
            if url_el and url_el.get("href"):
                href = url_el["href"]
                product_url = href if href.startswith("http") else f"{AMAZON_BASE_URL}{href}"

            img_el = card.select_one(sel["image"]) or card.select_one("img.s-image") or card.select_one("img")
            image_url = img_el["src"] if img_el and img_el.get("src") else None

            products.append(
                RawProduct(
                    site="amazon",
                    title=title,
                    price=price,
                    currency="EGP",
                    rating=rating,
                    review_count=review_count,
                    url=product_url,
                    image_url=image_url,
                ).model_dump()
            )
        except Exception as e:
            logger.warning(f"Failed to parse Amazon card: {e}")
            continue

    return products


def _parse_amazon_price(card) -> Optional[float]:
    """Extract price from Amazon card."""
    whole_el = card.select_one(sel["price_whole"]) or card.select_one("span.a-price-whole")
    if not whole_el:
        price_el = card.select_one("span.a-price span.a-offscreen") or card.select_one("span.a-price")
        if price_el:
            text = price_el.get_text(strip=True).replace(",", "")
            match = re.search(r"([\d.]+)", text)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    pass
        return None
    whole = whole_el.get_text(strip=True).replace(",", "").replace(".", "")
    frac_el = card.select_one(sel["price_fraction"])
    fraction = frac_el.get_text(strip=True) if frac_el else "00"
    try:
        return float(f"{whole}.{fraction}")
    except ValueError:
        return None


class AmazonScraperTool(BaseTool):
    """CrewAI tool that scrapes Amazon product listings."""

    name: str = "scrape_amazon"
    description: str = (
        "Searches Amazon Egypt for a product query and returns "
        "a list of products with title, price, rating, review count, and URL."
    )

    def _run(self, query: str) -> str:
        try:
            results = _scrape_amazon(query)
        except Exception as e:
            logger.error(f"Amazon scraper failed: {e}")
            results = []
        return json.dumps(results, ensure_ascii=False)
