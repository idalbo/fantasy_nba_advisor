# 🏀 Fantasy NBA Advisor

AI-powered fantasy basketball draft assistant using real NBA data and hybrid search (RAG application).

**[🚀 Try it Live](https://fantasy-nba-advisor.streamlit.app/)**

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/streamlit-1.28+-red.svg)](https://streamlit.io)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)

## Features

- **Real NBA Data**: 450+ players with 2024-25 season stats from Basketball Reference
- **Hybrid Search**: Vector embeddings + keyword matching for accurate retrieval
- **League-Aware**: Adjusts recommendations for 8-20 team leagues
- **Draft Intelligence**: Pick-specific advice with rank-based filtering
- **Fast Performance**: 0.2s average response time

## Quick Start

### Run with Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/idalbo/fantasy_nba_advisor.git
cd fantasy_nba_advisor

# Add your Groq API key to .env
echo "GROQ_API_KEY=your_key_here" > .env

# Start the app
docker-compose up
```

Access at `http://localhost:8504`

### Run Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Set your API key
export GROQ_API_KEY=your_key_here

# Run the app
streamlit run app.py
```

## Project Structure

```
### 3. RAG Pipeline
3. Rank-based filtering (±5 range)
# 🏀 Fantasy NBA Advisor

Lightweight Streamlit app that provides fantasy basketball draft assistance using a vector search backend.

Live demo: https://fantasy-nba-advisor.streamlit.app/

Key components
---------------
- `app.py` — Streamlit UI and navigation
- `src/rag.py` — Retrieval + ranking (hybrid vector + keyword search)
- `src/realtime_monitoring.py` — Real-time metrics logger
- `src/data_ingestion.py` — Scrapers / data loaders
- `data/` — Materialized embeddings and metadata (`player_embeddings.pkl`, `player_metadata.json`)
- `monitoring/` — Interaction and feedback logs
- `docker-compose.yml`, `Dockerfile` — Docker deployment
- `requirements*.txt` — Python dependencies

Quick start (Docker)
---------------------
1. Create a local `.env` with your Groq API key:

```bash
GROQ_API_KEY=your_groq_api_key
QDRANT_HOST=localhost
QDRANT_PORT=6335
```

2. Start services:

```bash
docker-compose up --build
```

The app will be available at `http://localhost:8504` (configured in `docker-compose.yml`).

Run locally (no Docker)
-----------------------
Install dependencies and run:

```bash
pip install -r requirements.txt
export GROQ_API_KEY=your_groq_api_key
streamlit run app.py
```

Monitoring and metrics
----------------------
- The app logs query-level metrics to `monitoring/realtime_metrics.jsonl` and user feedback to `monitoring/user_feedback.jsonl`.
- Real-time hit-rate calculation is inferred from draft/round queries when possible.

Project notes
-------------
- Hybrid scoring combines semantic vector similarity with keyword matching (weights are in `src/rag.py`).
- League size can be configured in the sidebar (affects draft round logic).
- If you deploy to Streamlit Cloud, the app will use an in-memory Qdrant fallback unless a hosted Qdrant is provided.

Makefile
--------
Common `make` targets are provided for convenience. Run from the project root:

- `make help` — Show available targets
- `make build` — Build Docker images (`docker-compose build`)
- `make ingest-data` — Start Qdrant and run the ingestion script (uses Docker)
- `make project-run` — Start the app via `docker-compose up -d`
- `make stop` — Stop running containers (`docker-compose down`)
- `make clean` — Remove containers and prune Docker system

Example:

```bash
make ingest-data
```

Contact
-------
Repository: https://github.com/idalbo/fantasy_nba_advisor
