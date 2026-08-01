"""Noon scraper — pure HTTP via curl_cffi. No Playwright, no browser, zero RAM."""

import json
import logging
import re
from urllib.parse import quote_plus

from bs4 import BeautifulSoup
from crewai.tools import BaseTool
from curl_cffi import requests as crequests

try:
    from config import MAX_PRODUCTS_PER_SITE, NOON_BASE_URL
    from models.schemas import RawProduct
except ImportError:
    from backend.config import MAX_PRODUCTS_PER_SITE, NOON_BASE_URL
    from backend.models.schemas import RawProduct

logger = logging.getLogger(__name__)


def _scrape_noon(query: str) -> list[dict]:
    """Fetch Noon search page via curl_cffi and extract products from __NEXT_DATA__ or HTML."""
    url = f"{NOON_BASE_URL}/search?q={quote_plus(query)}"
    products = []

    try:
        session = crequests.Session(impersonate="chrome120")
        response = session.get(url, timeout=7)
        if response.status_code != 200:
            logger.warning(f"Noon returned HTTP {response.status_code}")
            return []
        html = response.text
    except Exception as e:
        logger.error(f"Noon HTTP request failed: {e}")
        return []

    # ── Strategy 1: Parse __NEXT_DATA__ JSON (structured, reliable) ──
    soup = BeautifulSoup(html, "html.parser")
    next_data_tag = soup.select_one("script#__NEXT_DATA__")
    if next_data_tag:
        try:
            data = json.loads(next_data_tag.string)
            # Navigate to the product hits inside Noon's Next.js page props
            props = data.get("props", {}).get("pageProps", {})
            # Noon stores search results under different keys depending on version
            catalog = (
                props.get("catalog", {})
                or props.get("searchResult", {})
                or props
            )
            hits = catalog.get("hits", []) or catalog.get("products", []) or []

            for item in hits[:MAX_PRODUCTS_PER_SITE]:
                try:
                    title = item.get("name") or item.get("title") or item.get("name_en", "")
                    if not title or len(title) < 3:
                        continue

                    price = None
                    price_val = item.get("sale_price") or item.get("price") or item.get("offer", {}).get("sale_price")
                    if price_val:
                        try:
                            price = float(price_val)
                        except (ValueError, TypeError):
                            pass

                    rating = None
                    rating_val = item.get("rating") or item.get("avg_rating")
                    if rating_val:
                        try:
                            r = float(rating_val)
                            if 0 <= r <= 5:
                                rating = r
                        except (ValueError, TypeError):
                            pass

                    sku = item.get("sku") or item.get("product_sku") or ""
                    product_url = f"https://www.noon.com/egypt-en/p/{sku}" if sku else None

                    image_url = item.get("image_url") or item.get("image_key")
                    if image_url and not image_url.startswith("http"):
                        image_url = f"https://f.nooncdn.com/p/{image_url}.jpg"

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
                    logger.warning(f"Failed to parse Noon JSON item: {e}")
                    continue

            if products:
                return products
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.warning(f"Noon __NEXT_DATA__ parse failed, falling back to HTML: {e}")

    # ── Strategy 2: Fallback to HTML scraping ──
    links = soup.select("a[href*='/p/']") or soup.select("a")
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
            logger.warning(f"Failed to parse Noon HTML item: {e}")
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
