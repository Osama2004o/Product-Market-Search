"""Noon scraper tool using Playwright with HTTP/2 disabled to prevent network errors."""

import json
import logging
import re
from urllib.parse import quote_plus

from bs4 import BeautifulSoup
from crewai.tools import BaseTool
from playwright.sync_api import sync_playwright

try:
    from config import HEADLESS, MAX_PRODUCTS_PER_SITE, NOON_BASE_URL, SCRAPER_PROXY_URL, USER_AGENT
    from models.schemas import RawProduct
except ImportError:
    from backend.config import HEADLESS, MAX_PRODUCTS_PER_SITE, NOON_BASE_URL, SCRAPER_PROXY_URL, USER_AGENT
    from backend.models.schemas import RawProduct

logger = logging.getLogger(__name__)


def _scrape_noon(query: str) -> list[dict]:
    """Launch lightweight Chromium with HTTP/1.1 forced to avoid ERR_HTTP2_PROTOCOL_ERROR."""
    url = f"{NOON_BASE_URL}/search?q={quote_plus(query)}"
    products = []
    html = ""

    try:
        with sync_playwright() as p:
            launch_kwargs = {
                "headless": HEADLESS,
                "args": [
                    "--disable-gpu",
                    "--disable-dev-shm-usage",
                    "--no-sandbox",
                    "--disable-http2",  # Fixes ERR_HTTP2_PROTOCOL_ERROR
                    "--js-flags=--max-old-space-size=64",
                ],
            }
            if SCRAPER_PROXY_URL:
                launch_kwargs["proxy"] = {"server": SCRAPER_PROXY_URL}

            browser = p.chromium.launch(**launch_kwargs)
            context = browser.new_context(
                user_agent=USER_AGENT,
                viewport={"width": 1280, "height": 720},
                locale="en-US",
            )
            page = context.new_page()

            # Abort heavy assets (images/media) but keep scripts/styles for DOM stability
            page.route(
                "**/*",
                lambda route: route.abort()
                if route.request.resource_type in ["image", "font", "media"]
                else route.continue_(),
            )

            page.goto(url, wait_until="domcontentloaded", timeout=7000)
            html = page.content()
            browser.close()
    except Exception as e:
        logger.error(f"Noon Playwright error: {e}")
        return []

    soup = BeautifulSoup(html, "html.parser")
    links = soup.select("a[href*='/p/']") or soup.select("div[data-qa='product-item']") or soup.select("a")
    seen_urls = set()

    for link in links:
        if len(products) >= MAX_PRODUCTS_PER_SITE:
            break
        try:
            a_tag = link if link.name == "a" else link.find_parent("a")
            href = a_tag.get("href", "") if a_tag else ""

            if not href or "/p/" not in href or href in seen_urls:
                continue
            seen_urls.add(href)

            product_url = href if href.startswith("http") else f"https://www.noon.com{href}"
            text = a_tag.get_text(" ", strip=True) if a_tag else ""
            if not text or len(text) < 5:
                continue

            title_el = (
                a_tag.select_one("div[data-qa='product-name']")
                or a_tag.select_one("h2")
                or a_tag.select_one("span")
            )
            title = title_el.get_text(strip=True) if title_el else text.split("EGP")[0].strip()
            if not title or len(title) < 3:
                continue

            price = None
            price_match = re.search(r"EGP\s*([\d,.]+)", text) or re.search(r"([\d,.]+)\s*EGP", text)
            if price_match:
                try:
                    price = float(price_match.group(1).replace(",", ""))
                except ValueError:
                    pass

            rating = None
            rating_match = re.search(r"([\d.]+)\s*(?:★|\(\d+\))", text)
            if rating_match:
                try:
                    r_val = float(rating_match.group(1))
                    if 0 <= r_val <= 5:
                        rating = r_val
                except ValueError:
                    pass

            img_el = a_tag.select_one("img") if a_tag else None
            image_url = img_el.get("src") or img_el.get("data-src") if img_el else None

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
        try:
            results = _scrape_noon(query)
        except Exception as e:
            logger.error(f"Noon scraper failed: {e}")
            results = []
        return json.dumps(results, ensure_ascii=False)
