# 🛍️ Product Market Search

An intelligent multi-agent product market research and deal comparison platform. Powered by **CrewAI**, **Google Gemini**, **Playwright**, **FastAPI**, and **React**, this system automatically searches multiple major e-commerce platforms (Amazon, Noon, Jumia), scrapes real-time listings, normalizes currency and attributes, and ranks products by a custom price-to-rating value score.

---

## ✨ Features

- 🕵️ **Automated Web Scraping**: Live scraping of product search results from Amazon Egypt, Noon Egypt, and Jumia Egypt using Playwright and BeautifulSoup.
- 🤖 **Multi-Agent Orchestration**: Powered by **CrewAI** with specialized agents:
  - `AmazonScraperAgent`, `NoonScraperAgent`, `JumiaScraperAgent`: Parallel live data extraction.
  - `NormalizerAgent`: Normalizes inconsistent site attributes, pricing formats, and currencies into a unified schema.
  - `RankingAgent`: Calculates a relative price-to-value score and generates concise justifications for top picks.
- 📊 **Smart Value Ranking**: Scores listings dynamically using relative min-max scaling of rating vs. price.
- ⚡ **FastAPI Backend**: Asynchronous REST endpoint with robust error handling and partial-result fallbacks.
- 🎨 **Modern React UI**: Sleek glassmorphism web app with real-time status indicators, interactive filters, sorting, and direct product links.

---

## 🏗️ System Architecture

```
┌─────────────────┐       POST /api/search       ┌──────────────────┐
│   React UI      │ ───────────────────────────> │  FastAPI Backend │
│ (Vite + Modern) │ <─────────────────────────── │                  │
└─────────────────┘        JSON Results          └────────┬─────────┘
                                                          │
                                                          ▼
                                                ┌────────────────────┐
                                                │    CrewAI Crew     │
                                                │ (Task Orchestrator)│
                                                └────────┬───────────┘
                    ┌──────────────────┬─────────────────┴──────────────────┬──────────────────┐
                    ▼                  ▼                                    ▼                  ▼
            ┌──────────────┐   ┌──────────────┐                     ┌──────────────┐   ┌──────────────────┐
            │Amazon Scraper│   │ Noon Scraper │                     │Jumia Scraper │   │  Ranking Agent   │
            │    Agent     │   │    Agent     │                     │    Agent     │   │ (Gemini-powered) │
            └──────┬───────┘   └──────┬───────┘                     └──────┬───────┘   └─────────┬────────┘
                   │ Playwright       │ Playwright                         │ Playwright          │
                   ▼                  ▼                                    ▼                     │
              amazon.eg            noon.com                              jumia.eg                │
                   └──────────────────┴────────────────────────────────────┴─────────────────────┘
                                    Raw Products -> Normalization -> Scored -> Sorted
```

---

## 📁 Repository Structure

```
Product Market Search/
├── backend/
│   ├── api/                # API router endpoints (/search)
│   ├── crew/               # CrewAI agents, tasks, and crew orchestration
│   ├── models/             # Pydantic schemas (SearchRequest, Product, etc.)
│   ├── tools/              # Playwright scraper tools (Amazon, Noon, Jumia)
│   ├── config.py           # Application settings & environment loader
│   ├── main.py             # FastAPI entrypoint and CORS middleware
│   ├── requirements.txt    # Python backend dependencies
│   ├── .env.example        # Environment variable template
│   └── venv/               # Virtual environment (ignored by git)
│
├── frontend/
│   ├── src/
│   │   ├── api/            # API client service
│   │   ├── components/     # React UI components (SearchBar, ResultCard, Filters)
│   │   ├── App.jsx         # Main application layout & state management
│   │   ├── index.css       # Design system & CSS variables
│   │   └── main.jsx        # React DOM entrypoint
│   ├── index.html          # HTML entrypoint
│   ├── package.json        # Frontend dependencies
│   └── vite.config.js      # Vite build configuration
│
├── plan.md                 # Detailed project specification & plan
├── .gitignore              # Git ignore rules
└── README.md               # Project documentation
```

---

## ⚙️ Prerequisites

Before running the application, ensure you have the following installed:

- **Python**: 3.10 or higher
- **Node.js**: v18.0.0 or higher
- **npm**: v9.0.0 or higher
- **Google Gemini API Key**: Obtain a key from [Google AI Studio](https://aistudio.google.com/)

---

## 🚀 Quick Start

### 1. Backend Setup

1. **Navigate to the backend directory**:
   ```bash
   cd backend
   ```

2. **Create and activate a virtual environment**:
   - **Windows (PowerShell)**:
     ```powershell
     python -m venv venv
     .\venv\Scripts\Activate
     ```
   - **macOS/Linux**:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. **Install backend dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Playwright browser binaries**:
   ```bash
   playwright install chromium
   ```

5. **Configure environment variables**:
   Copy `.env.example` to `.env` and insert your Gemini API Key:
   ```bash
   cp .env.example .env
   ```
   Edit `.env`:
   ```ini
   GEMINI_API_KEY=your_actual_gemini_api_key
   GEMINI_MODEL=gemini/gemini-2.0-flash-lite
   AMAZON_BASE_URL=https://www.amazon.eg
   NOON_BASE_URL=https://www.noon.com/egypt-en
   JUMIA_BASE_URL=https://www.jumia.com.eg
   REQUEST_TIMEOUT_SECONDS=30
   MAX_PRODUCTS_PER_SITE=5
   HEADLESS=true
   ```

6. **Start the FastAPI backend server**:
   ```bash
   uvicorn main:app --reload --port 8000
   ```
   The backend API will be live at `http://localhost:8000`.

---

### 2. Frontend Setup

1. **Navigate to the frontend directory**:
   ```bash
   cd ../frontend
   ```

2. **Install Node dependencies**:
   ```bash
   npm install
   ```

3. **Start the Vite development server**:
   ```bash
   npm run dev
   ```
   The frontend application will be live at `http://localhost:5173`.

---

## 📡 API Endpoint

### `POST /api/search`

Executes a live search across Amazon, Noon, and Jumia, running normalized agent evaluation.

#### Request Body
```json
{
  "query": "iPhone 15 128GB"
}
```

#### Sample Response
```json
{
  "query": "iPhone 15 128GB",
  "results": [
    {
      "site": "amazon",
      "title": "Apple iPhone 15 (128 GB) - Black",
      "price": 42500.0,
      "currency": "EGP",
      "rating": 4.6,
      "review_count": 340,
      "description": "Dynamic Island, 48MP Main camera, USB-C",
      "url": "https://www.amazon.eg/dp/...",
      "score": 0.92,
      "reasoning": "Excellent rating with competitive local pricing."
    }
  ],
  "warnings": []
}
```

---

## 🛡️ License

This project is open source and available under the [MIT License](LICENSE).
