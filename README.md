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
- Purpose: help fantasy managers pick better in drafts by combining a knowledge base of NBA player data with an LLM-backed assistant.
- Key idea: hybrid retrieval (semantic vectors + keyword re-ranking) + rank-aware prompt filtering for pick-specific advice.

Core evaluation checklist (what reviewers look for)
--------------------------------------------------
Each reviewer should be able to verify these points quickly:

- Problem description: clear statement of what the app does and the dataset used.
- Retrieval flow: evidence that a knowledge base + LLM were used (code + short explanation).
- Retrieval evaluation: comparison or notes on at least two retrieval strategies (dense vs hybrid or other).
- LLM evaluation: simple ablation or prompt variants tested and results described.
- Interface: a working UI (Streamlit) or API to interact with the system.
- Ingestion: script or Makefile target that ingests the dataset into the KB.
- Monitoring & feedback: logs or dashboard that records user feedback and runtime metrics.
- Containerization & reproducibility: Docker/Docker Compose and clear setup instructions.

Quick links
-----------
- Setup guide (detailed): `SETUP_GUIDE.md`
- Reviewer guide: `REVIEWER_GUIDE.md`
- Code: `app.py`, `src/` (core modules)

Project structure (high level)
-----------------------------
```
fantasy_nba_advisor/
├── app.py                     # Streamlit UI
├── src/
│   ├── rag.py                 # Retrieval + prompt builder
│   ├── realtime_monitoring.py # Logging & hit-rate computation
│   ├── data_ingestion.py      # Scrapers / ingestion scripts
│   └── retrieval_evaluator.py # Retrieval/LLM evaluation helpers
├── data/                      # Materialized embeddings & metadata
├── monitoring/                # JSONL logs for queries and feedback
├── docker-compose.yml
├── Dockerfile
├── Makefile
├── requirements.txt
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

---
Short and focused — the detailed setup is in `SETUP_GUIDE.md` and reviewer instructions in `REVIEWER_GUIDE.md`.
