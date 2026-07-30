"""Search API endpoint."""

import logging
from fastapi import APIRouter, HTTPException

try:
    from crew.crew import run_product_search
    from models.schemas import SearchRequest, SearchResponse
except ImportError:
    from backend.crew.crew import run_product_search
    from backend.models.schemas import SearchRequest, SearchResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/search", response_model=SearchResponse)
async def search_products(request: SearchRequest):
    """
    Search Amazon, Noon, and Jumia for a product query.
    Returns ranked results sorted by best price-to-rating value.
    """
    logger.info(f"Search request: {request.query}")

    try:
        result = await run_product_search(request.query)
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

    return SearchResponse(
        query=request.query,
        results=result["results"],
        warnings=result.get("warnings", []),
        total_results=len(result["results"]),
    )
