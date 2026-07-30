"""CrewAI agent definitions for Product Market Search."""

from crewai import Agent

try:
    from config import GEMINI_API_KEY, GEMINI_MODEL
    from tools.amazon_scraper import AmazonScraperTool
    from tools.noon_scraper import NoonScraperTool
    from tools.jumia_scraper import JumiaScraperTool
except ImportError:
    from backend.config import GEMINI_API_KEY, GEMINI_MODEL
    from backend.tools.amazon_scraper import AmazonScraperTool
    from backend.tools.noon_scraper import NoonScraperTool
    from backend.tools.jumia_scraper import JumiaScraperTool


def _llm_config():
    """Return the LLM identifier string for CrewAI (Gemini)."""
    return GEMINI_MODEL


def create_amazon_agent() -> Agent:
    return Agent(
        role="Amazon Product Scraper",
        goal="Search Amazon Egypt for the given product query and extract structured product data.",
        backstory=(
            "You are a specialist at finding products on Amazon Egypt. "
            "You use the scrape_amazon tool to search and return structured results. "
            "Always call the tool with the exact user query."
        ),
        tools=[AmazonScraperTool()],
        llm=_llm_config(),
        verbose=True,
        allow_delegation=False,
    )


def create_noon_agent() -> Agent:
    return Agent(
        role="Noon Product Scraper",
        goal="Search Noon Egypt for the given product query and extract structured product data.",
        backstory=(
            "You are a specialist at finding products on Noon. "
            "You use the scrape_noon tool to search and return structured results. "
            "Always call the tool with the exact user query."
        ),
        tools=[NoonScraperTool()],
        llm=_llm_config(),
        verbose=True,
        allow_delegation=False,
    )


def create_jumia_agent() -> Agent:
    return Agent(
        role="Jumia Product Scraper",
        goal="Search Jumia Egypt for the given product query and extract structured product data.",
        backstory=(
            "You are a specialist at finding products on Jumia. "
            "You use the scrape_jumia tool to search and return structured results. "
            "Always call the tool with the exact user query."
        ),
        tools=[JumiaScraperTool()],
        llm=_llm_config(),
        verbose=True,
        allow_delegation=False,
    )


def create_normalizer_agent() -> Agent:
    return Agent(
        role="Product Data Normalizer",
        goal=(
            "Take raw product data from Amazon, Noon, and Jumia scrapers "
            "and normalize them into a unified format with consistent currency (EGP), "
            "clean titles, and valid numeric fields."
        ),
        backstory=(
            "You are a data analyst who specializes in cleaning and normalizing "
            "product data from different e-commerce sources. You ensure all prices "
            "are in EGP, ratings are on a 0-5 scale, and missing fields are handled gracefully."
        ),
        llm=_llm_config(),
        verbose=True,
        allow_delegation=False,
    )


def create_ranking_agent() -> Agent:
    return Agent(
        role="Product Ranking Specialist",
        goal=(
            "Score and rank products by best price-to-rating value. "
            "Filter out products missing price or rating. "
            "Provide a 1-line justification for each product's rank."
        ),
        backstory=(
            "You are a value-analysis expert. You compute a score for each product "
            "using min-max normalized rating and price: score = rating_norm * 0.6 - price_norm * 0.4. "
            "Higher score = better value. You also note tie-breakers like review count."
        ),
        llm=_llm_config(),
        verbose=True,
        allow_delegation=False,
    )
