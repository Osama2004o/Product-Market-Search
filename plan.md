# Product Market Analysis Tool — Implementation Plan

## 1. What this is

A tool where a user types in a product they're considering buying (e.g. "iPhone 15 128GB"), and the system:
1. Searches Amazon, Noon, and Jumia for that product
2. Scrapes price, rating, and description for the top matches on each site
3. Scores and sorts everything by **best price-to-rating value**
4. Returns a ranked list to the user

**Stack**
- Agents/orchestration: CrewAI
- LLM: Gemini API (via `google-generativeai` / LangChain Gemini wrapper)
- Scraping: Playwright (primary) + BeautifulSoup (HTML parsing on captured pages)
- Backend: FastAPI
- Frontend: React
- Fetching: always live, no caching layer for v1

---

## 2. High-level architecture

```
┌─────────────┐      POST /search        ┌──────────────────┐
│   React     │ ───────────────────────▶ │     FastAPI       │
│  Frontend   │ ◀─────────────────────── │     Backend       │
└─────────────┘      JSON results         └────────┬──────────┘
                                                    │
                                                    ▼
                                          ┌────────────────────┐
                                          │   CrewAI Crew      │
                                          │  (kickoff per req) │
                                          └────────┬───────────┘
                     ┌──────────────────┬──────────┴───────────┬──────────────────┐
                     ▼                  ▼                      ▼                  ▼
             ┌──────────────┐   ┌──────────────┐      ┌──────────────┐   ┌──────────────────┐
             │ Amazon Scraper│   │ Noon Scraper │      │ Jumia Scraper│   │  Ranking Agent    │
             │    Agent      │   │    Agent     │      │    Agent     │   │ (Gemini-powered)  │
             └──────┬───────┘   └──────┬───────┘      └──────┬───────┘   └─────────┬─────────┘
                    │ Playwright        │ Playwright           │ Playwright         │
                    ▼                   ▼                      ▼                    │
              amazon.com            noon.com                jumia.com               │
                    └──────────────────┴──────────────────────┴────────────────────┘
                                     raw product data → normalized → scored → sorted
```

---

## 3. CrewAI agent design

Use **one crew per search request**, kicked off synchronously by the FastAPI endpoint.

### Agents

| Agent | Role | Tools |
|---|---|---|
| `AmazonScraperAgent` | Searches Amazon for the query, extracts top N product cards (title, price, rating, review count, URL, short description) | Custom Playwright tool: `scrape_amazon(query)` |
| `NoonScraperAgent` | Same for Noon | Custom Playwright tool: `scrape_noon(query)` |
| `JumiaScraperAgent` | Same for Jumia | Custom Playwright tool: `scrape_jumia(query)` |
| `NormalizerAgent` | Takes raw scraped output from all 3 (different currencies/formats/fields) and normalizes into one common schema | Gemini LLM (no external tool) |
| `RankingAgent` | Computes/validates a price-to-value score per product, filters obvious junk (no rating, no price), sorts final list, writes 1-line justification per item | Gemini LLM |

Each scraper agent should have its task **return structured JSON** (Pydantic-validated), not free text — this keeps the pipeline reliable and avoids the LLM having to parse messy scraped HTML itself. The LLM's job is normalization/ranking/reasoning, not scraping — Playwright + BeautifulSoup do the scraping deterministically inside the tool, and only the extracted structured snippets go to the agent.

### Process flow (CrewAI `Process.sequential` or `Process.hierarchical`)

1. Kick off 3 scraper agents (can run as parallel tasks if using async crew execution, or sequential if keeping it simple for v1)
2. Feed all 3 raw outputs into `NormalizerAgent` → unified list of `Product` objects
3. Feed normalized list into `RankingAgent` → scored + sorted list
4. Return final list to FastAPI

### Suggested scoring formula (starting point, tune later)

```
score = rating_normalized * w1 - price_normalized * w2
```
Where `rating_normalized` and `price_normalized` are both scaled 0–1 across the current result set (min-max scaling), so the score is always relative to what's actually available in that search, not a fixed universal scale. Let the Ranking Agent use this as a baseline and allow it to note tie-breakers (review count, free shipping if that data is available).

---

## 4. Backend (FastAPI)

```
backend/
├── main.py                  # FastAPI app, CORS, routes
├── api/
│   └── search.py            # POST /search endpoint
├── crew/
│   ├── crew.py              # Crew + Process definition
│   ├── agents.py            # Agent definitions
│   └── tasks.py             # Task definitions
├── tools/
│   ├── amazon_scraper.py    # Playwright scraping logic
│   ├── noon_scraper.py
│   └── jumia_scraper.py
├── models/
│   └── schemas.py           # Pydantic: SearchRequest, Product, SearchResponse
├── config.py                 # env vars, Gemini API key, site selectors
└── requirements.txt
```

**Endpoint**

```
POST /search
Body: { "query": "iPhone 15 128GB" }
Response: {
  "query": "...",
  "results": [
    {
      "site": "amazon",
      "title": "...",
      "price": 799.0,
      "currency": "EGP",
      "rating": 4.5,
      "review_count": 1200,
      "description": "...",
      "url": "...",
      "score": 0.87
    },
    ...
  ]
}
```

Since scraping takes real time (several seconds per site), consider:
- Running the endpoint as `async def` and running scrapers concurrently with `asyncio.gather`
- Adding a simple in-memory request timeout (e.g. 25–30s) so one slow site doesn't hang the whole response
- Returning partial results with a `warnings` field if one site's scraper fails, rather than failing the whole request

---

## 5. Scraping layer (Playwright + BeautifulSoup)

- Playwright launches a headless browser, navigates to each site's search results page for the query, waits for product cards to render (many of these sites are JS-heavy), then grabs the page HTML
- BeautifulSoup then parses that HTML to pull out title/price/rating/link text using CSS selectors specific to each site
- Keep selectors in a small config/mapping per site so they're easy to update when a site changes its markup (this will happen — build for it)

**Practical challenges to plan for from day one:**
- Bot detection / CAPTCHAs — headless browsers get flagged more than real ones; consider `playwright-stealth` and setting a realistic user-agent/viewport
- Rate limiting — don't hammer the same site with parallel requests across many users; add small delays
- Site structure changes — selectors will break periodically; wrap each scraper in a try/except that returns an empty/partial result instead of crashing the whole crew
- Terms of Service — Amazon, Noon, and Jumia all have ToS around automated scraping; worth being aware of this as you move from a personal/portfolio project toward anything public-facing or at scale

---

## 6. Frontend (React)

```
frontend/
├── src/
│   ├── App.jsx
│   ├── components/
│   │   ├── SearchBar.jsx
│   │   ├── ResultCard.jsx        # site badge, title, price, rating, description, link
│   │   ├── ResultsList.jsx       # sorted list + loading skeleton
│   │   └── SiteFilterToggle.jsx  # optional: filter by site
│   ├── api/
│   │   └── searchApi.js          # calls POST /search
│   └── index.jsx
├── package.json
```

- Simple flow: search bar → loading state (scraping takes a few seconds, show a spinner/progress text) → sorted result cards
- Each `ResultCard` shows: site logo/badge, title, price, rating (stars), short description, "View on site" link, and the computed score/rank
- Consider a per-site loading indicator ("Amazon ✓, Noon ⏳, Jumia ✓") since sites will finish scraping at different times if you go the concurrent route

---

## 7. Build phases

**Phase 1 — Scraping foundations**
- Set up Playwright, get one working scraper per site returning raw structured data for a hardcoded query (no CrewAI/Gemini yet)
- Validate selectors work and handle "no results" / blocked-request cases

**Phase 2 — CrewAI + Gemini wiring**
- Wrap each scraper as a CrewAI tool
- Build the 5 agents and wire the sequential process
- Test the full crew end-to-end from a script (no API yet), tune the Normalizer/Ranking prompts

**Phase 3 — Backend API**
- Wrap the crew kickoff in the `/search` FastAPI endpoint
- Add error handling, partial-result support, request timeout

**Phase 4 — Frontend**
- Search bar + results list hitting the FastAPI endpoint
- Loading/error states, basic styling

**Phase 5 — Polish**
- Tune the scoring formula with real data
- Add filtering/sorting controls on the frontend (by site, by price, by rating)
- Add logging around scraper failures so you can see which site/selector breaks first

---

## 8. Environment variables

```
GEMINI_API_KEY=
AMAZON_BASE_URL=
NOON_BASE_URL=
JUMIA_BASE_URL=
REQUEST_TIMEOUT_SECONDS=30
```

---

## 9. Open items to decide as you build

- Exact number of products to pull per site (e.g. top 5 vs top 10)
- Currency handling if Amazon returns USD while Noon/Jumia return EGP — normalize to one currency for fair comparison
- What counts as a "match" across sites (same product, different listing titles) — for v1, treat each scraped listing independently rather than trying to de-duplicate across sites