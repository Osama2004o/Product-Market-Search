"""CrewAI Crew wiring for Product Market Search."""

import json
import logging
from typing import Any

from crewai import Crew, Process

try:
    from crew.agents import (
        create_amazon_agent,
        create_jumia_agent,
        create_noon_agent,
        create_normalizer_agent,
        create_ranking_agent,
    )
    from crew.tasks import (
        create_normalize_task,
        create_ranking_task,
        create_scrape_amazon_task,
        create_scrape_jumia_task,
        create_scrape_noon_task,
    )
    from models.schemas import Product
except ImportError:
    from backend.crew.agents import (
        create_amazon_agent,
        create_jumia_agent,
        create_noon_agent,
        create_normalizer_agent,
        create_ranking_agent,
    )
    from backend.crew.tasks import (
        create_normalize_task,
        create_ranking_task,
        create_scrape_amazon_task,
        create_scrape_jumia_task,
        create_scrape_noon_task,
    )
    from backend.models.schemas import Product

logger = logging.getLogger(__name__)


async def run_product_search(query: str) -> dict[str, Any]:
    """
    Kick off the full crew pipeline for a product search query.

    Returns dict with 'results' (list[Product dicts]) and 'warnings' (list[str]).
    """
    warnings: list[str] = []

    # Create agents
    amazon_agent = create_amazon_agent()
    noon_agent = create_noon_agent()
    jumia_agent = create_jumia_agent()
    normalizer_agent = create_normalizer_agent()
    ranking_agent = create_ranking_agent()

    # Create tasks — scraper tasks run first, then normalize, then rank
    scrape_amazon = create_scrape_amazon_task(amazon_agent, query)
    scrape_noon = create_scrape_noon_task(noon_agent, query)
    scrape_jumia = create_scrape_jumia_task(jumia_agent, query)
    normalize = create_normalize_task(normalizer_agent)
    rank = create_ranking_task(ranking_agent)

    # Normalize task needs context from all 3 scrapers
    normalize.context = [scrape_amazon, scrape_noon, scrape_jumia]
    # Ranking task needs context from normalizer
    rank.context = [normalize]

    # Build crew — sequential process
    crew = Crew(
        agents=[amazon_agent, noon_agent, jumia_agent, normalizer_agent, ranking_agent],
        tasks=[scrape_amazon, scrape_noon, scrape_jumia, normalize, rank],
        process=Process.sequential,
        verbose=True,
    )

    # Kick off asynchronously (required when running inside FastAPI's event loop)
    try:
        result = await crew.kickoff_async()
        raw_output = result.raw if hasattr(result, "raw") else str(result)
    except Exception as e:
        logger.error(f"Crew execution failed: {e}")
        return {"results": [], "warnings": [f"Crew execution failed: {str(e)}"]}

    # Parse the final output into Product objects
    products = _parse_crew_output(raw_output, warnings)

    return {"results": products, "warnings": warnings}


def _parse_crew_output(raw_output: str, warnings: list[str]) -> list[dict]:
    """Parse the ranking agent's JSON output into Product dicts."""
    try:
        # Try to extract JSON array from the output
        # The LLM might wrap it in markdown code blocks
        text = raw_output.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        # Find the JSON array
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
                logger.warning(f"Failed to parse product: {e}")
                warnings.append(f"Skipped malformed product entry")
                continue
        return products

    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"Failed to parse crew output as JSON: {e}")
        warnings.append("Failed to parse ranking results. Returning raw output.")
        return []
