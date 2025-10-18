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

# 🏀 Fantasy NBA Advisor

Lightweight RAG (retrieval-augmented generation) demo that provides fantasy basketball draft advice.

Live demo: https://fantasy-nba-advisor.streamlit.app/ (Streamlit)

Overview
--------
- Purpose: help fantasy managers pick better in drafts by combining a knowledge base of NBA player data with an AI assistant and fantasy points context.
- Retrieval approach: semantic vector search combined with keyword re-ranking. Recommendations are filtered by draft pick range so results stay relevant to your pick.

Reviewer note: reviewers — see the top-level `SETUP_GUIDE.md` for run instructions and check `src/rag.py`, `src/data_ingestion.py`, and `monitoring/` when evaluating.

Quick links
-----------
- Data sources: `DATA_SOURCES.md`
- Setup guide (detailed): `SETUP_GUIDE.md`
- Code: `app.py`, `src/` (core modules)

Project structure (high level)
-----------------------------
```
fantasy_nba_advisor/
├── app.py                     # Streamlit UI entry
├── src/
│   ├── __init__.py
│   ├── rag.py                 # Retrieval + prompt builder
│   ├── realtime_monitoring.py # Logging & hit-rate computation
│   ├── data_ingestion.py      # Scrapers / ingestion scripts
│   ├── retrieval_evaluator.py # Evaluation helpers
│   └── nba_players.db         # small local DB used by scripts
├── data/                      # Materialized embeddings & metadata (in .gitignore)
├── monitoring/                # JSONL logs for queries and feedback
├── .env.example               # Example env vars
├── DATA_SOURCES.md            # Data source documentation
├── docker-compose.yml
├── Dockerfile
├── Makefile
├── requirements.txt
├── requirements_docker.txt
├── requirements_streamlit.txt
└── SETUP_GUIDE.md
```

Quick start (recommended: Docker)
---------------------------------
1) Clone the repo:

```bash
git clone https://github.com/idalbo/fantasy_nba_advisor.git
cd fantasy_nba_advisor
```

2) Make a local `.env` (never commit your keys):

```bash
cp .env.example .env
# Edit .env and set GROQ_API_KEY (or other LLM provider keys)
```

3) Build and run everything (ingest data first time):

```bash
make ingest-data   # populates Qdrant with player vectors (one-time)
make project-run   # start Streamlit + services
```

4) Open the app at http://localhost:8504

Run locally without Docker
--------------------------
1) Create a virtualenv and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2) Set LLM API key and run the app:

```bash
export GROQ_API_KEY=your_key_here
streamlit run app.py
```

Monitoring & feedback
---------------------
- Logs: `monitoring/realtime_metrics.jsonl` (query logs) and `monitoring/user_feedback.jsonl` (feedback entries).
- Dashboard: open the Monitoring page in the Streamlit app to view hit-rate, latency, and top queries.

Where to look for the core pieces
---------------------------------
- Retrieval logic: `src/rag.py` (query expansion, vector search, keyword re-ranking, prompt builder).
- Ingestion: `src/data_ingestion.py` and the `make ingest-data` target in the Makefile.
- Evaluation helpers: `src/retrieval_evaluator.py` and `evaluation/` folder.

Contact & issues
-----------------
If you find problems, open an issue at https://github.com/idalbo/fantasy_nba_advisor/issues
