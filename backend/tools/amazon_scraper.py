"""Amazon scraper tool using Playwright (sync) + BeautifulSoup."""

import json
import logging
import re
from typing import Optional
from urllib.parse import quote_plus

from bs4 import BeautifulSoup
from crewai.tools import BaseTool
from playwright.sync_api import sync_playwright

try:
    from config import (
        AMAZON_BASE_URL,
        HEADLESS,
        MAX_PRODUCTS_PER_SITE,
        SELECTORS,
        USER_AGENT,
    )
    from models.schemas import RawProduct
except ImportError:
    from backend.config import (
        AMAZON_BASE_URL,
        HEADLESS,
        MAX_PRODUCTS_PER_SITE,
        SELECTORS,
        USER_AGENT,
    )
    from backend.models.schemas import RawProduct

logger = logging.getLogger(__name__)
sel = SELECTORS["amazon"]


def _scrape_amazon(query: str) -> list[dict]:
    """Launch headless browser, search Amazon, parse product cards."""
    url = f"{AMAZON_BASE_URL}/s?k={quote_plus(query)}"
    products = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=HEADLESS,
                args=[
                    "--disable-gpu",
                    "--disable-dev-shm-usage",
                    "--disable-setuid-sandbox",
                    "--no-sandbox",
                    "--no-zygote",
                    "--disable-accelerated-2d-canvas",
                    "--no-first-run",
                    "--js-flags=--max-old-space-size=128",
                ],
            )
            context = browser.new_context(
                user_agent=USER_AGENT,
                viewport={"width": 1920, "height": 1080},
                locale="en-US",
                extra_http_headers={
                    "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                },
            )
            page = context.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=20000)
            page.wait_for_timeout(2500)
            html = page.content()
            browser.close()
    except Exception as e:
        logger.error(f"Amazon Playwright error: {e}")
        return []

    soup = BeautifulSoup(html, "html.parser")
    # Amazon search result cards can be div[data-component-type='s-search-result'] or div.s-result-item
    cards = soup.select("div[data-component-type='s-search-result']")
    if not cards:
        cards = [
            c for c in soup.select("div.s-result-item")
            if c.get("data-sku") or c.select_one("h2")
        ]
    cards = cards[:MAX_PRODUCTS_PER_SITE]

    for card in cards:
        try:
            # Title — extract full text from h2 tag or img alt attribute
            title_el = card.select_one("h2") or card.select_one("a.a-link-normal")
            title = title_el.get_text(" ", strip=True) if title_el else None
            if (not title or title.lower() in ("samsung", "apple", "xiaomi")) and card.select_one("img.s-image"):
                alt = card.select_one("img.s-image").get("alt")
                if alt:
                    title = alt
            if not title or len(title) < 3:
                continue

            # Price
            price = _parse_amazon_price(card)

            # Rating
            rating = None
            rating_el = card.select_one(sel["rating"]) or card.select_one("i.a-icon-star")
            if rating_el:
                match = re.search(r"([\d.]+)", rating_el.get_text())
                if match:
                    rating = float(match.group(1))

            # Review count
            review_count = None
            rev_el = card.select_one(sel["review_count"]) or card.select_one("span.a-size-base")
            if rev_el:
                text = rev_el.get_text(strip=True).replace(",", "").replace("(", "").replace(")", "")
                match = re.search(r"(\d+)", text)
                if match:
                    review_count = int(match.group(1))

            # URL
            url_el = card.select_one(sel["url"]) or card.select_one("h2 a") or card.select_one("a.a-link-normal")
            product_url = None
            if url_el and url_el.get("href"):
                href = url_el["href"]
                product_url = href if href.startswith("http") else f"{AMAZON_BASE_URL}{href}"

            # Image
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
    """Extract price from Amazon card (whole + fraction)."""
    whole_el = card.select_one(sel["price_whole"]) or card.select_one("span.a-price-whole")
    if not whole_el:
        # Fallback to general price class
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
        """Run the Amazon scraper synchronously."""
        try:
            results = _scrape_amazon(query)
        except Exception as e:
            logger.error(f"Amazon scraper failed: {e}")
            results = []
        return json.dumps(results, ensure_ascii=False)
