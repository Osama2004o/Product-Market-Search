"""CrewAI task definitions for Product Market Search."""

from crewai import Task, Agent


def create_scrape_amazon_task(agent: Agent, query: str) -> Task:
    return Task(
        description=(
            f"Search Amazon Egypt for: '{query}'. "
            "Use the scrape_amazon tool with this exact query. "
            "Return the raw JSON output from the tool as-is."
        ),
        expected_output="A JSON array of product objects from Amazon with title, price, rating, url fields.",
        agent=agent,
    )


def create_scrape_noon_task(agent: Agent, query: str) -> Task:
    return Task(
        description=(
            f"Search Noon Egypt for: '{query}'. "
            "Use the scrape_noon tool with this exact query. "
            "Return the raw JSON output from the tool as-is."
        ),
        expected_output="A JSON array of product objects from Noon with title, price, rating, url fields.",
        agent=agent,
    )


def create_scrape_jumia_task(agent: Agent, query: str) -> Task:
    return Task(
        description=(
            f"Search Jumia Egypt for: '{query}'. "
            "Use the scrape_jumia tool with this exact query. "
            "Return the raw JSON output from the tool as-is."
        ),
        expected_output="A JSON array of product objects from Jumia with title, price, rating, url fields.",
        agent=agent,
    )


def create_normalize_task(agent: Agent) -> Task:
    return Task(
        description=(
            "You will receive raw product data from Amazon, Noon, and Jumia scrapers. "
            "Normalize all products into a unified format:\n"
            "- Ensure all prices are in EGP\n"
            "- Ensure ratings are on a 0-5 scale\n"
            "- Keep full product titles intact (DO NOT shorten, summarize, or truncate product titles)\n"
            "- Clean up titles (remove excessive whitespace, line breaks)\n"
            "- Remove duplicate/junk entries with no title\n"
            "- Keep all other fields (url, image_url, review_count) intact\n\n"
            "Return a JSON array of normalized product objects."
        ),
        expected_output=(
            "A JSON array where each object has: site, title, price (float in EGP), "
            "currency ('EGP'), rating (0-5 float), review_count (int or null), "
            "description, url, image_url."
        ),
        agent=agent,
    )


def create_ranking_task(agent: Agent) -> Task:
    return Task(
        description=(
            "You will receive a normalized list of products from multiple sites. "
            "Score and rank them by best value:\n\n"
            "1. Filter out products with no price AND no rating (keep if at least one exists)\n"
            "2. For remaining products, compute score using min-max normalization:\n"
            "   - rating_norm = (rating - min_rating) / (max_rating - min_rating)\n"
            "   - price_norm = (price - min_price) / (max_price - min_price)\n"
            "   - score = rating_norm * 0.6 - price_norm * 0.4\n"
            "   - If only 1 product or all same price/rating, set score to 0.5\n"
            "3. Sort by score descending\n"
            "4. Add a 'rank' field (1 = best) and a 'justification' field (1 line explaining the ranking)\n\n"
            "Return the final JSON array with score, rank, and justification added to each product."
        ),
        expected_output=(
            "A JSON array sorted by score descending. Each object has all normalized fields "
            "plus: score (float), rank (int), justification (string)."
        ),
        agent=agent,
    )
