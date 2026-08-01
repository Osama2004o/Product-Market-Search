"""FastAPI application entry point for Product Market Search."""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

try:
    from api.search import router as search_router
except ImportError:
    from backend.api.search import router as search_router

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

app = FastAPI(
    title="Product Market Search",
    description="Search Amazon, Noon, and Jumia — get ranked results by best value.",
    version="1.0.0",
)

# CORS — allow React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(search_router, prefix="/api")


@app.get("/")
async def root():
    return {"status": "ok", "message": "Product Market Search Backend API"}


@app.get("/health")
async def health():
    return {"status": "ok"}

