"""Jumia scraper tool using Playwright (Chromium) + HTTP fallback + BeautifulSoup."""

import json
import logging
import re
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup
from crewai.tools import BaseTool
from playwright.sync_api import sync_playwright

try:
    from config import (
        HEADLESS,
        JUMIA_BASE_URL,
        MAX_PRODUCTS_PER_SITE,
        SELECTORS,
        USER_AGENT,
    )
    from models.schemas import RawProduct
except ImportError:
    from backend.config import (
        HEADLESS,
        JUMIA_BASE_URL,
        MAX_PRODUCTS_PER_SITE,
        SELECTORS,
        USER_AGENT,
    )
    from backend.models.schemas import RawProduct

logger = logging.getLogger(__name__)
sel = SELECTORS["jumia"]


def _scrape_jumia(query: str) -> list[dict]:
    """Search Jumia using Playwright Chromium with HTTP fallback."""
    url = f"{JUMIA_BASE_URL}/catalog/?q={quote_plus(query)}"
    products = []
    html = ""

    # 1. Try fetching via Playwright to bypass Cloudflare 403 Forbidden
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=HEADLESS,
                args=[
                    "--disable-http2",
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                ],
            )
            context = browser.new_context(
                user_agent=USER_AGENT,
                viewport={"width": 1400, "height": 900},
                locale="en-US",
                extra_http_headers={
                    "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                },
            )
            page = context.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=20000)
            page.wait_for_timeout(2000)
            html = page.content()
            browser.close()
    except Exception as e:
        logger.warning(f"Jumia Playwright error: {e}. Trying HTTP fallback...")
        try:
            headers = {
                "User-Agent": USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
                "Sec-Ch-Ua": '"Chromium";v="125", "Not.A/Brand";v="24"',
                "Sec-Ch-Ua-Mobile": "?0",
                "Sec-Ch-Ua-Platform": '"Windows"',
                "Upgrade-Insecure-Requests": "1",
            }
            response = requests.get(url, headers=headers, timeout=12)
            if response.status_code == 200:
                html = response.text
        except Exception as http_err:
            logger.error(f"Jumia HTTP request error: {http_err}")

    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select(sel["product_card"])
    if not cards:
        cards = soup.select("article.prd")
    cards = cards[:MAX_PRODUCTS_PER_SITE]

    for card in cards:
        try:
            # Title
            title_el = card.select_one(sel["title"]) or card.select_one("h3.name") or card.select_one("h3")
            title = title_el.get_text(strip=True) if title_el else None
            if not title:
                continue

            # Price
            price = None
            price_el = card.select_one(sel["price"]) or card.select_one("div.prc")
            if price_el:
                price_text = price_el.get_text(strip=True).replace(",", "")
                match = re.search(r"([\d.]+)", price_text)
                if match:
                    price = float(match.group(1))

            # Rating
            rating = None
            rating_el = card.select_one(sel["rating"]) or card.select_one("div.stars")
            if rating_el:
                data_rating = rating_el.get("data-rating")
                if data_rating:
                    rating = float(data_rating)
                else:
                    match = re.search(r"([\d.]+)", rating_el.get_text())
                    if match:
                        rating = float(match.group(1))

            # Review count
            review_count = None
            rev_el = card.select_one(sel["review_count"]) or card.select_one("div.rev")
            if rev_el:
                text = rev_el.get_text(strip=True).replace(",", "")
                match = re.search(r"(\d+)", text)
                if match:
                    review_count = int(match.group(1))

            # URL
            url_el = card.select_one(sel["url"]) or card.select_one("a.core") or card.select_one("a")
            product_url = None
            if url_el and url_el.get("href"):
                href = url_el["href"]
                product_url = href if href.startswith("http") else f"{JUMIA_BASE_URL}{href}"

            # Image
            img_el = card.select_one(sel["image"]) or card.select_one("img")
            image_url = None
            if img_el:
                image_url = img_el.get("data-src") or img_el.get("src")

            products.append(
                RawProduct(
                    site="jumia",
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
            logger.warning(f"Failed to parse Jumia card: {e}")
            continue

    return products


class JumiaScraperTool(BaseTool):
    """CrewAI tool that scrapes Jumia product listings."""

    name: str = "scrape_jumia"
    description: str = (
        "Searches Jumia Egypt for a product query and returns "
        "a list of products with title, price, rating, review count, and URL."
    )

    def _run(self, query: str) -> str:
        """Run the Jumia scraper synchronously."""
        try:
            results = _scrape_jumia(query)
        except Exception as e:
            logger.error(f"Jumia scraper failed: {e}")
            results = []
        return json.dumps(results, ensure_ascii=False)
