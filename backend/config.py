"""Configuration for Product Market Search backend."""

import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini/gemini-3.5-flash-lite")

if GEMINI_API_KEY and not os.getenv("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = GEMINI_API_KEY


# Site base URLs
AMAZON_BASE_URL = os.getenv("AMAZON_BASE_URL", "https://www.amazon.eg")
NOON_BASE_URL = os.getenv("NOON_BASE_URL", "https://www.noon.com/egypt-en")
JUMIA_BASE_URL = os.getenv("JUMIA_BASE_URL", "https://www.jumia.com.eg")

# Scraping config
REQUEST_TIMEOUT_SECONDS = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "30"))
MAX_PRODUCTS_PER_SITE = int(os.getenv("MAX_PRODUCTS_PER_SITE", "5"))
SCRAPER_PROXY_URL = os.getenv("SCRAPER_PROXY_URL", "")

# Playwright settings
HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.0.0 Safari/537.36"
)

# CSS selectors per site — easy to update when markup changes
SELECTORS = {
    "amazon": {
        "search_url": "{base}/s?k={query}",
        "product_card": "div[data-component-type='s-search-result']",
        "title": "h2 a span",
        "price_whole": "span.a-price-whole",
        "price_fraction": "span.a-price-fraction",
        "rating": "span.a-icon-alt",
        "review_count": "span.a-size-base.s-underline-text",
        "url": "h2 a",
        "image": "img.s-image",
    },
    "noon": {
        "search_url": "{base}/search?q={query}",
        "product_card": "div[data-qa='product-item']",
        "title": "div[data-qa='product-name']",
        "price": "strong[data-qa='product-price']",
        "currency": "span[data-qa='product-currency']",
        "rating": "div.ratingStars",
        "url": "a[data-qa='product-click']",
        "image": "img[data-qa='product-image']",
    },
    "jumia": {
        "search_url": "{base}/catalog/?q={query}",
        "product_card": "article.prd._fb",
        "title": "h3.name",
        "price": "div.prc",
        "old_price": "div.old",
        "rating": "div.stars._s",
        "review_count": "div.rev",
        "url": "a.core",
        "image": "img.img",
    },
}

# Scoring weights
RATING_WEIGHT = 0.6
PRICE_WEIGHT = 0.4
