# 🛍️ Product Market Search — MarketLens

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev)
[![CrewAI](https://img.shields.io/badge/CrewAI-Multi--Agent-blueviolet?style=for-the-badge)](https://www.crewai.com)
[![Gemini](https://img.shields.io/badge/Google_Gemini-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev)
[![Playwright](https://img.shields.io/badge/Playwright-2EAD33?style=for-the-badge&logo=playwright&logoColor=white)](https://playwright.dev)

> **An AI-powered multi-agent system that searches Amazon, Noon & Jumia in real time, normalizes product data, and ranks the best deals — so you don't have to.**

---

## ✨ Features

| Feature                          | Description                                                                                                                        |
| -------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| 🕵️ **Live Web Scraping**         | Real-time scraping of product listings from **Amazon Egypt**, **Noon Egypt**, and **Jumia Egypt** using Playwright + BeautifulSoup |
| 🤖 **5 Specialized AI Agents**   | CrewAI-orchestrated agents — 3 scrapers, 1 data normalizer, 1 ranking analyst — each with a focused role                           |
| 📊 **Smart Value Scoring**       | Min-max normalization of rating vs. price across all results, producing a relative value score per product                         |
| ⚡ **Async FastAPI Backend**     | Non-blocking REST API with partial-result fallbacks and per-site error isolation                                                   |
| 🎨 **Glassmorphism React UI**    | Modern dark-mode interface with animated blobs, site-colored badges, star ratings, and direct product links                        |
| 🔗 **Cross-Platform Comparison** | Unified currency (EGP), consistent schema, and AI-generated justification for each product's ranking                               |

---

## 🧠 How It Works

```
1️⃣  User enters a product query (e.g. "iPhone 15 128GB")
         │
         ▼
2️⃣  FastAPI receives the request and kicks off a CrewAI Crew
         │
         ▼
3️⃣  Three Scraper Agents (Amazon, Noon, Jumia) launch headless
     browsers via Playwright and extract structured product data
         │
         ▼
4️⃣  Normalizer Agent (Gemini-powered) unifies currencies, cleans
     titles, and standardizes all fields into a common schema
         │
         ▼
5️⃣  Ranking Agent computes a value score per product using
     relative min-max scaling and adds a 1-line justification
         │
         ▼
6️⃣  Sorted results are returned to the React UI as ranked cards
```

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

## 🛠️ Tech Stack

| Layer                | Technology                     | Purpose                                                      |
| -------------------- | ------------------------------ | ------------------------------------------------------------ |
| **AI Orchestration** | CrewAI                         | Multi-agent pipeline with sequential task execution          |
| **LLM**              | Google Gemini (2.0 Flash Lite) | Normalization reasoning & value-score justifications         |
| **Web Scraping**     | Playwright + BeautifulSoup     | Headless browser rendering + HTML parsing                    |
| **Backend API**      | FastAPI (async)                | REST endpoint with CORS, error handling, Pydantic validation |
| **Frontend**         | React + Vite                   | Glassmorphism UI with animated components                    |
| **Data Validation**  | Pydantic v2                    | Strict schema enforcement for product data flow              |

---

## 📁 Repository Structure

```
Product-Market-Search/
├── backend/
│   ├── api/                # API router endpoints (/search)
│   ├── crew/               # CrewAI agents, tasks, and crew orchestration
│   │   ├── agents.py       # 5 specialized agent definitions
│   │   ├── tasks.py        # Task prompts and expected outputs
│   │   └── crew.py         # Crew wiring, kickoff, and output parsing
│   ├── models/             # Pydantic schemas (SearchRequest, Product, etc.)
│   ├── tools/              # Playwright scraper tools per site
│   │   ├── amazon_scraper.py
│   │   ├── noon_scraper.py
│   │   └── jumia_scraper.py
│   ├── config.py           # Settings, selectors, environment loader
│   ├── main.py             # FastAPI entrypoint and CORS middleware
│   ├── requirements.txt    # Python dependencies
│   └── .env.example        # Environment variable template
│
├── frontend/
│   ├── src/
│   │   ├── api/            # API client service
│   │   ├── components/     # SearchBar, ResultCard, ResultsList
│   │   ├── App.jsx         # Main layout & state management
│   │   ├── index.css       # Design system (CSS variables, glassmorphism)
│   │   └── main.jsx        # React DOM entrypoint
│   ├── index.html          # HTML entrypoint
│   ├── package.json        # Frontend dependencies
│   └── vite.config.js      # Vite build configuration
│
├── plan.md                 # Detailed project specification & plan
├── .gitignore
└── README.md
```

---

## ⚙️ Prerequisites

| Requirement           | Version                                      |
| --------------------- | -------------------------------------------- |
| Python                | 3.10+                                        |
| Node.js               | v18.0.0+                                     |
| npm                   | v9.0.0+                                      |
| Google Gemini API Key | [Get one here](https://aistudio.google.com/) |

---

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/Osama2004o/Product-Market-Search.git
cd Product-Market-Search
```

### 2. Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv venv

# Windows (PowerShell)
.\venv\Scripts\Activate

# macOS/Linux
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browser binaries
playwright install chromium

# Configure environment variables
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

**`.env` configuration:**

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

**Start the backend:**

```bash
uvicorn main:app --reload --port 8000
```

> Backend API live at `http://localhost:8000`

### 3. Frontend Setup

```bash
cd ../frontend

# Install dependencies
npm install

# Start the dev server
npm run dev
```

> Frontend live at `http://localhost:5173`

### Run with Docker Compose

Copy `backend/.env.example` to `backend/.env` and set `GEMINI_API_KEY`, then run from the repository root:

```bash
docker compose up --build
```

Open the frontend at `http://localhost:8080`. Nginx serves the built frontend and proxies `/api` requests to FastAPI. The backend API is also available directly at `http://localhost:8000`; stop the stack with `docker compose down`.

---

## 📡 API Reference

### `POST /api/search`

Search across all three platforms with a single request.

**Request:**

```json
{
  "query": "iPhone 15 128GB"
}
```

**Response:**

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
      "justification": "Excellent rating with competitive local pricing."
    }
  ],
  "warnings": []
}
```

---

## 🤝 Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## ⭐ Show Your Support

If you found this project useful or interesting, please consider giving it a **star** ⭐ on GitHub!

---

## 🛡️ License

This project is open source and available under the [MIT License](LICENSE).
