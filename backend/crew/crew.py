"""CrewAI Crew wiring and parallel execution pipeline for Product Market Search."""

import asyncio
import json
import logging
from typing import Any

from crewai import Crew, Process, Task

try:
    from crew.agents import create_normalizer_agent, create_ranking_agent
    from crew.tasks import create_normalize_task, create_ranking_task
    from models.schemas import Product
    from tools.amazon_scraper import _scrape_amazon
    from tools.noon_scraper import _scrape_noon
    from tools.jumia_scraper import _scrape_jumia
except ImportError:
    from backend.crew.agents import create_normalizer_agent, create_ranking_agent
    from backend.crew.tasks import create_normalize_task, create_ranking_task
    from backend.models.schemas import Product
    from backend.tools.amazon_scraper import _scrape_amazon
    from backend.tools.noon_scraper import _scrape_noon
    from backend.tools.jumia_scraper import _scrape_jumia

logger = logging.getLogger(__name__)


async def run_product_search(query: str) -> dict[str, Any]:
    """
    Kick off parallel product search across Amazon, Noon, and Jumia.
    Processes products using Normalizer & Ranking Agents.
    """
    warnings: list[str] = []

    # 1. Scrape all 3 e-commerce platforms concurrently in parallel threads
    logger.info(f"Starting parallel scraping for query: '{query}'")
    scraped_results = await asyncio.gather(
        asyncio.to_thread(_scrape_amazon, query),
        asyncio.to_thread(_scrape_noon, query),
        asyncio.to_thread(_scrape_jumia, query),
        return_exceptions=True,
    )

    all_raw_products: list[dict] = []
    site_names = ["amazon", "noon", "jumia"]

    for idx, res in enumerate(scraped_results):
        site = site_names[idx]
        if isinstance(res, Exception):
            logger.error(f"Scraper error on {site}: {res}")
            warnings.append(f"Failed to fetch products from {site.capitalize()}")
        elif isinstance(res, list):
            logger.info(f"Fetched {len(res)} products from {site}")
            all_raw_products.extend(res)

    if not all_raw_products:
        return {"results": [], "warnings": warnings + ["No products found matching your search query."]}

    # 2. Python fallback normalization and scoring (ensures zero downtime)
    fallback_ranked = _compute_python_ranking(all_raw_products)

    # 3. Pass to CrewAI agents for LLM ranking & justification
    try:
        ranking_agent = create_ranking_agent()
        raw_json_input = json.dumps(all_raw_products, ensure_ascii=False)
        
        ranking_task = Task(
            description=(
                f"You are evaluating product search results for query: '{query}'.\n"
                f"Raw Product Data:\n{raw_json_input}\n\n"
                "Task:\n"
                "1. Clean product titles and ensure currency is EGP.\n"
                "2. Score products from 0 to 1 based on price-to-rating ratio (higher rating & lower price = higher score).\n"
                "3. Sort products descending by score.\n"
                "4. Assign rank (1, 2, 3...) and write a concise 1-sentence justification for each product.\n\n"
                "Return ONLY a valid JSON array of objects with fields: site, title, price, currency, rating, review_count, description, url, image_url, score, rank, justification."
            ),
            expected_output="A JSON array of ranked products with scores, ranks, and justifications.",
            agent=ranking_agent,
        )

        crew = Crew(
            agents=[ranking_agent],
            tasks=[ranking_task],
            process=Process.sequential,
            verbose=True,
        )

        result = await crew.kickoff_async()
        raw_output = result.raw if hasattr(result, "raw") else str(result)
        llm_products = _parse_crew_output(raw_output, warnings)

        if llm_products:
            return {"results": llm_products, "warnings": warnings}
    except Exception as e:
        logger.warning(f"LLM ranking agent failed: {e}. Falling back to Python algorithm.")
        warnings.append("Used automatic algorithmic ranking fallback.")

    return {"results": fallback_ranked, "warnings": warnings}


def _compute_python_ranking(raw_products: list[dict]) -> list[dict]:
    """Calculate price-to-rating value scores deterministically in Python."""
    valid_items = []

    for item in raw_products:
        p = item.get("price")
        r = item.get("rating")
        valid_items.append(item)

    prices = [i["price"] for i in valid_items if i.get("price") is not None]
    ratings = [i["rating"] for i in valid_items if i.get("rating") is not None]

    min_p, max_p = (min(prices), max(prices)) if prices else (1, 1)
    min_r, max_r = (min(ratings), max(ratings)) if ratings else (1, 5)

    ranked = []
    for item in valid_items:
        price = item.get("price") or max_p
        rating = item.get("rating") or min_r

        p_norm = (price - min_p) / (max_p - min_p) if max_p > min_p else 0.5
        r_norm = (rating - min_r) / (max_r - min_r) if max_r > min_r else 0.5

        score = round(max(0.0, min(1.0, (r_norm * 0.6) + ((1.0 - p_norm) * 0.4))), 2)

        product_dict = {
            "site": item.get("site", "unknown"),
            "title": item.get("title", "Product"),
            "price": price,
            "currency": "EGP",
            "rating": rating,
            "review_count": item.get("review_count"),
            "description": item.get("description", f"Listing on {item.get('site', '').capitalize()}"),
            "url": item.get("url", "#"),
            "image_url": item.get("image_url"),
            "score": score,
            "justification": f"Rated {rating}/5 with competitive pricing at {price:,.0f} EGP.",
        }
        ranked.append(product_dict)

    ranked.sort(key=lambda x: x["score"], reverse=True)
    for idx, item in enumerate(ranked, 1):
        item["rank"] = idx

    return ranked


def _parse_crew_output(raw_output: str, warnings: list[str]) -> list[dict]:
    """Parse the ranking agent's JSON output into Product dicts."""
    try:
        text = raw_output.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        start = text.index("[")
        end = text.rindex("]") + 1
        json_str = text[start:end]

        raw_list = json.loads(json_str)
        products = []
        for item in raw_list:
            try:
                product = Product(**item)
                products.append(product.model_dump())
            except Exception as e:
                logger.warning(f"Failed to parse product item: {e}")
                continue
        return products

    except Exception as e:
        logger.error(f"Failed to parse crew output as JSON: {e}")
        return []
