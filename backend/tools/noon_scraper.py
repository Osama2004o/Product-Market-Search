"""Noon scraper tool using Playwright (Chromium) + BeautifulSoup."""

import json
import logging
import re
from urllib.parse import quote_plus

from bs4 import BeautifulSoup
from crewai.tools import BaseTool
from playwright.sync_api import sync_playwright

try:
    from config import (
        HEADLESS,
        MAX_PRODUCTS_PER_SITE,
        NOON_BASE_URL,
        USER_AGENT,
    )
    from models.schemas import RawProduct
except ImportError:
    from backend.config import (
        HEADLESS,
        MAX_PRODUCTS_PER_SITE,
        NOON_BASE_URL,
        USER_AGENT,
    )
    from backend.models.schemas import RawProduct

logger = logging.getLogger(__name__)


def _scrape_noon(query: str) -> list[dict]:
    """Launch Chromium browser, search Noon, parse product cards."""
    url = f"{NOON_BASE_URL}/search?q={quote_plus(query)}"
    products = []
    html = ""

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
                    "--single-process",
                    "--disable-accelerated-2d-canvas",
                    "--no-first-run",
                    "--js-flags=--max-old-space-size=128",
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
            page.goto(url, wait_until="domcontentloaded", timeout=25000)
            page.wait_for_timeout(2500)
            html = page.content()
            browser.close()
    except Exception as e:
        logger.error(f"Noon Playwright error: {e}")
        return []

    soup = BeautifulSoup(html, "html.parser")
    # Select Noon product links or container elements
    links = soup.select("a[href*='/p/']") or soup.select("div[data-qa='product-name']") or soup.select("a")
    seen_urls = set()

    for link in links:
        if len(products) >= MAX_PRODUCTS_PER_SITE:
            break
        try:
            # If element is not an <a> tag, find parent <a>
            a_tag = link if link.name == "a" else link.find_parent("a")
            href = a_tag.get("href", "") if a_tag else ""
            
            if not href or "/p/" not in href or href in seen_urls:
                continue
            seen_urls.add(href)

            product_url = href if href.startswith("http") else f"https://www.noon.com{href}"

            text = a_tag.get_text(" ", strip=True) if a_tag else ""
            if not text or len(text) < 5:
                continue

            # Title
            title_el = (a_tag.select_one("div[data-qa='product-name']") or 
                        a_tag.select_one("h2") or 
                        a_tag.select_one("span"))
            title = title_el.get_text(strip=True) if title_el else text.split("EGP")[0].strip()
            if not title or len(title) < 3:
                continue

            # Price
            price = None
            price_match = re.search(r"EGP\s*([\d,.]+)", text) or re.search(r"([\d,.]+)\s*EGP", text)
            if price_match:
                try:
                    price = float(price_match.group(1).replace(",", ""))
                except ValueError:
                    pass

            # Rating
            rating = None
            rating_match = re.search(r"([\d.]+)\s*(?:★|\(\d+\))", text)
            if rating_match:
                try:
                    r_val = float(rating_match.group(1))
                    if 0 <= r_val <= 5:
                        rating = r_val
                except ValueError:
                    pass

            # Image
            img_el = a_tag.select_one("img") if a_tag else None
            image_url = None
            if img_el:
                image_url = img_el.get("src") or img_el.get("data-src")

            products.append(
                RawProduct(
                    site="noon",
                    title=title[:150],
                    price=price,
                    currency="EGP",
                    rating=rating,
                    url=product_url,
                    image_url=image_url,
                ).model_dump()
            )
        except Exception as e:
            logger.warning(f"Failed to parse Noon item: {e}")
            continue

    return products


class NoonScraperTool(BaseTool):
    """CrewAI tool that scrapes Noon product listings."""

    name: str = "scrape_noon"
    description: str = (
        "Searches Noon Egypt for a product query and returns "
        "a list of products with title, price, rating, and URL."
    )

    def _run(self, query: str) -> str:
        """Run the Noon scraper synchronously."""
        try:
            results = _scrape_noon(query)
        except Exception as e:
            logger.error(f"Noon scraper failed: {e}")
            results = []
        return json.dumps(results, ensure_ascii=False)
