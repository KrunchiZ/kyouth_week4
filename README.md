# KadPilot — AI-Powered Malaysian Credit Card Advisor

KadPilot is an intelligent credit card comparison and recommendation platform tailored for Malaysian consumers. It aggregates credit card offerings from major Malaysian banks, processes them through a structured ETL pipeline, and surfaces them via a browsable dashboard and an AI chatbot powered by Retrieval-Augmented Generation (RAG).

<br>

## Project Overview

### Problem Statement

Malaysian consumers face a fragmented landscape when comparing credit cards. Card details are scattered across multiple bank websites, presented in inconsistent formats, and laden with technical terms that make it difficult for everyday users to evaluate which card best suits their spending habits, income level, and lifestyle needs.

### Target Users

- **Malaysian consumers** seeking to choose or compare credit cards
- **Financially conscious shoppers** looking for optimal cashback, rewards, and fee structures
- **Students and researchers** studying financial product data pipelines and RAG architectures

### System Goal

Provide a unified, searchable, and AI-assisted platform where users can:

1. Browse and filter credit cards from multiple Malaysian banks
2. View detailed card information including fees, perks, and eligibility requirements
3. Ask natural-language questions and receive personalized, data-grounded recommendations

<br>

## System Architecture

### High-Level Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  Browser    │───▶│  Frontend    │───▶│  Backend    │
│ (Port 8000) │     │  (Jinja2)    │     │  (FastAPI)  │
└─────────────┘     └──────────────┘     └──────┬──────┘
                                                 │
                                    ┌────────────▼────────────┐
                                    │     RAG Engine          │
                                    │ (Gemini / Ollama LLMs)  │
                                    └────────────┬────────────┘
                                                 │
                                    ┌────────────▼────────────┐
                                    │  SQLite (Gold Layer)    │
                                    │  credit_cards.db        │
                                    └────────────┬────────────┘
                                                 │
                                    ┌────────────▼────────────┐
                                    │  ETL Pipeline           │
                                    │  (.mhtml → .html →      │
                                    │   .json → .db)          │
                                    └─────────────────────────┘
```

### Data Flow

1. **Ingest**: Raw `.mhtml` files (scraped from Malaysian bank websites) are extracted into `.html` files (bronze layer)
2. **Process**: BeautifulSoup parses the HTML, extracting 10+ fields per card into structured `.json` files (silver layer)
3. **Load**: JSON files are loaded into a SQLite database with SHA-256 content hashing for deduplication (gold layer)
4. **Retrieve**: At query time, SentenceTransformers embeddings enable semantic search across card features
5. **Generate**: Retrieved context is passed to an LLM (Gemini or Ollama) which generates a natural-language answer grounded in the database

### Module Breakdown

| Module | Location | Responsibility |
|--------|----------|----------------|
| **Backend API** | `backend/src/api/` | FastAPI REST endpoints (`/cards`, `/banks`, `/ask`, `/health`) |
| **ETL Pipeline** | `backend/src/etl/` | Ingest, process, load, and profile credit card data |
| **RAG Engine** | `backend/src/rag/` | Semantic retrieval, LLM prompting, rate throttling |
| **MCP Server** | `backend/src/db_server.py` | FastMCP server exposing SQLite queries as tools |
| **Data Tagging** | `backend/src/tag_data.py` | LLM-assisted enrichment of missing fields |
| **Frontend** | `frontend/src/` | Jinja2 templates, static assets, backend proxy |
| **SQL Queries** | `backend/sql/` | Parameterized queries for CRUD operations |

<br>

## Setup & Installation

### Prerequisites

- **Docker** and **Docker Compose** (v2)
- **Hugging Face token** (for downloading the SentenceTransformer model)
- **Google Gemini API key** (for cloud LLM inference)

### Quick Start

```bash
# 1. Clone and navigate
git clone <repo-url>
cd week4

# 2. Configure environment
cp .env.example .env
# Edit .env: set HF_TOKEN, OLLAMA_MODEL_PATH, and DEV="false" for docker, "true" for local dev

# 3. Place your Gemini API key and backend url
mkdir -p secrets
echo "YOUR_GEMINI_API_KEY" > secrets/gemini_api_key.txt
echo "YOUR_BACKEND_URL" > secrets/backend_url.txt

# 4. Start all services
docker compose up --build
```

The application will be available at:

- **Frontend**: http://localhost:8000
- **Backend API**: http://localhost:8001
- **Ollama**: http://localhost:11434

### Services

| Service | Port | Description |
|---------|------|-------------|
| Frontend | 8000 | Jinja2 templates, static assets, API proxy |
| Backend | 8001 | FastAPI REST API, RAG engine, MCP server |
| Ollama | 11434 | Local LLM inference (optional, for offline mode) |

### Running Without Docker

```bash
# Backend
# make sure you have set the api key in the secret file.
# unset GEMINI_API_KEY after you're done with the session.
export GEMINI_API_KEY="$(cat secrets/gemini_api_key.txt)"
cd backend
uv sync
uv run uvicorn --app-dir src --host 0.0.0.0 --port 8001 app:app

# Frontend
cd frontend
uv sync
uv run uvicorn --app-dir src --host 0.0.0.0 --port 8000 app:app
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DEV` | Development mode (uses local paths) | `false` |
| `HF_TOKEN` | Hugging Face token for model downloads | — |
| `OLLAMA_HOST` | Ollama server URL | `http://localhost:11434` |
| `OLLAMA_MODEL_PATH` | Persistent volume path for Ollama models | `/usr/share/ollama` |

<br>

## Features

### Card Browsing & Filtering

- **Dashboard** with paginated card grid displaying all available credit cards
- **Filter by bank** (Alliance Bank, AmBank, Maybank, Hong Leong Bank)
- **Filter by minimum annual income** brackets
- **Full-text search** across card titles
- **Bank distribution chart** powered by Chart.js

### Detailed Card Views

- Click any card to view its full details page
- Displays all 10+ feature categories: cashback, petrol rewards, travel benefits, premium perks, balance transfer, easy payment plans, fees, requirements, and more
- Tables and structured data preserved from original bank pages

### AI Chatbot (RAG-Powered)

- **Natural language questions**: "Which card has the best cashback for online shopping?"
- **Income-aware recommendations**: Select your income bracket for personalized suggestions
- **Grounded responses**: Answers cite specific cards with match scores
- **Multiple LLM backends**: Choose from Gemini (3.1 Flash Lite, 2.5 Flash Lite, 3.5 Flash) or local Ollama models (Llama 3.2, Gemma 3 1B)
- **Session management**: Chat history with session download as JSON

### Data Pipeline

- **ETL automation**: Single command to run the full pipeline (`uv run python -m src.etl.main all`)
- **Bronze → Silver → Gold** layered architecture with progressive structuring
- **Content-hash deduplication**: SHA-256 based dedup prevents duplicate card entries
- **Data profiling**: Built-in quality metrics on the gold database
- **LLM-assisted tagging**: Automatically enriches missing data fields (e.g., minimum annual income)

### REST API

- **Health check** endpoint for monitoring
- **Paginated card listing** with lightweight summary responses
- **Full card detail** endpoint by title
- **Bank enumeration** endpoint
- **RAG chat** endpoint with configurable top-k and LLM provider

<br>

## Technical Decisions

### Architecture Choices

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Framework** | FastAPI (backend) + Jinja2 (frontend) | FastAPI provides automatic OpenAPI docs and async support; Jinja2 avoids the overhead of a separate SPA build step |
| **Database** | SQLite | Zero configuration, embedded, perfect for the dataset scale (~22 cards); no external infrastructure needed |
| **Data Pipeline** | Three-layer ETL (bronze/silver/gold) | Separates raw extraction from cleaning and analysis; enables incremental reprocessing |
| **RAG Retrieval** | SentenceTransformers + cosine similarity | Pre-computed embeddings at startup enable fast, deterministic retrieval without per-query model loading |
| **LLM Orchestration** | Model Context Protocol (MCP) | Standardized interface between the RAG engine and SQLite queries; decouples data access from generation logic |
| **Containerization** | Docker Compose | Reproducible environments; isolates backend, frontend, and Ollama services |

### Trade-offs Made

- **SQLite over PostgreSQL**: Chose simplicity and zero-dependency deployment over horizontal scalability. Acceptable for the current dataset size but would need migration for production-scale data.
- **Pre-computed embeddings over on-demand**: Embeddings are computed once at startup rather than per-query. This eliminates latency at query time but increases initial boot time and memory usage.
- **Frontend proxy over direct browser-to-API**: The frontend proxies all API calls to keep the Gemini API key server-side. This adds a hop but maintains security. CORS and cookie-based auth would be needed for a direct browser approach.
- **Gemini + Ollama dual support**: Cloud LLMs offer better quality; local Ollama offers privacy and no API costs. Supporting both maximizes accessibility but doubles the testing surface.

<br>

## Limitations

### Known Issues

- **Dataset scope**: Currently covers only ~21 cards from a handful of Malaysian banks. Coverage is not comprehensive across the full Malaysian market.
- **Static source data**: The ETL pipeline must be manually re-run when new cards are added or existing cards change. There is no automated web scraping scheduled.
- **RAG retrieval quality**: Cosine similarity on sentence embeddings captures topical relevance but may miss nuanced comparisons (e.g., specific fee structures or promotional periods).
- **Missing field imputation**: The LLM-based tagging script (`tag_data.py`) fills NULL `min_annual_income` values but can produce inconsistent results across different model versions.
- **No authentication**: The system has no user authentication or rate limiting on the frontend. The backend RAG endpoint has throttling, but the browsing endpoints are unrestricted.
- **Single-language**: The interface and responses are English-only; no localization for Bahasa Malaysia or Chinese.

### Future Improvements

- Expand the card database to cover all major Malaysian banks and card types
- Implement automated periodic scraping and incremental ETL updates
- Add user accounts with saved card comparisons and watchlists
- Introduce multi-language support (Bahasa Malaysia, Mandarin)
- Migrate to a production-grade database (PostgreSQL) with connection pooling
- Add WebSocket support for real-time chat streaming responses
- Implement A/B testing for recommendation quality evaluation
- Add a mobile-responsive PWA frontend

<br>

## Project Structure

```
├── docker-compose.yml          # Service orchestration
├── .env.example                # Environment template
├── secrets/                    # Docker secrets (API keys)
├── backend/
│   ├── src/
│   │   ├── app.py              # FastAPI entrypoint + RAG lifespan
│   │   ├── api/                # REST routes & schemas
│   │   ├── etl/                # Data pipeline (ingest/process/load/profiler)
│   │   ├── rag/                # Retriever, prompt model, throttler
│   │   ├── config/             # Settings & paths
│   │   └── db_server.py        # FastMCP server
│   ├── sql/                    # Parameterized SQL queries
│   └── data/                   # ETL layers (0_source → 3_gold)
└── frontend/
    ├── src/
    │   ├── app.py              # FastAPI frontend server
    │   ├── routes/             # Page handlers
    │   ├── services/           # Backend API client
    │   ├── templates/          # Jinja2 HTML templates
    │   └── static/             # CSS, JS, icons
```
