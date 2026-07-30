"""Pydantic schemas for Product Market Search."""

from pydantic import BaseModel, Field
from typing import Optional


class SearchRequest(BaseModel):
    """Incoming search request from frontend."""
    query: str = Field(..., min_length=1, max_length=200, description="Product search query")


class RawProduct(BaseModel):
    """Raw scraped product before normalization."""
    site: str
    title: str
    price: Optional[float] = None
    currency: Optional[str] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    description: Optional[str] = None
    url: Optional[str] = None
    image_url: Optional[str] = None


class Product(BaseModel):
    """Normalized product with computed score."""
    site: str
    title: str
    price: Optional[float] = None
    currency: str = "EGP"
    rating: Optional[float] = None
    review_count: Optional[int] = None
    description: Optional[str] = None
    url: Optional[str] = None
    image_url: Optional[str] = None
    score: Optional[float] = None
    rank: Optional[int] = None
    justification: Optional[str] = None


class SearchResponse(BaseModel):
    """Response returned to frontend."""
    query: str
    results: list[Product] = []
    warnings: list[str] = []
    total_results: int = 0
