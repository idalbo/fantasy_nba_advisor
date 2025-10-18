---
# Fantasy NBA Advisor — Setup Guide

This guide walks you through running the project locally (Docker and non-Docker workflows), ingesting data, and troubleshooting the most common issues. It assumes no prior knowledge of the course material.

Prerequisites
-------------
- Git
- Docker & Docker Compose (recommended) OR Python 3.10+ and pip
- Internet access (for initial data ingestion)
- LLM API key (Groq by default; you can swap for another provider — see notes)

Before you start
-----------------
1) Create a Groq API key

  - Visit https://console.groq.com and create an account (if you don't have one).
  - Generate an API key and copy it.
  - Create a local `.env` file from `.env.example` and add:

```bash
GROQ_API_KEY=your_groq_api_key_here
```

  Keep `.env` local and never commit it to the repository.

Quick start — Docker (recommended)
---------------------------------
1. Clone and prepare:

```bash
git clone https://github.com/idalbo/fantasy_nba_advisor.git
cd fantasy_nba_advisor
cp .env.example .env
# Edit .env and set GROQ_API_KEY (do NOT commit your .env)
```

2. Ingest data (one-time) and start the app:

```bash
make ingest-data   # starts Qdrant and populates the vector DB
make project-run   # starts Streamlit and supporting services
```

3. Open the app: http://localhost:8504

Run without Docker (developer mode)
----------------------------------
1. Create a venv and install deps:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# set GROQ_API_KEY in .env or export as env var
```

2. Run the app:

```bash
streamlit run app.py
```

Ingestion details
-----------------
- `make ingest-data` orchestrates starting Qdrant (docker-compose) and running the ingestion script that:
  - scrapes Basketball Reference for player stats and metadata
  - computes embeddings and fantasy features
  - indexes vectors and payloads into Qdrant
- Manual ingestion: `python src/data_ingestion.py --help` (see script flags)

Configuration
-------------
- `.env` (local only): set `GROQ_API_KEY`, `QDRANT_HOST`, `QDRANT_PORT`, `DEBUG`, and `LOG_LEVEL`.
- Makefile targets: `ingest-data`, `project-run`, `stop`, `clean`, `build`.

Monitoring & feedback
---------------------
- Query logs: `monitoring/realtime_metrics.jsonl`
- Feedback: `monitoring/user_feedback.jsonl`
- Use the Monitoring page in the Streamlit app to visualize hit rates, latencies, and top queries.

Troubleshooting (common)
------------------------
- App not reachable: check `docker-compose ps` and open `http://localhost:8504`.
- Ingestion fails: restart Qdrant (`docker-compose up -d qdrant`) and run `make ingest-data` again.
- No AI responses: confirm `GROQ_API_KEY` is set and valid.

Success checklist
-----------------
- [ ] App runs at `http://localhost:8504`
- [ ] Data ingestion completed and vectors indexed
- [ ] Retrieval returns sensible players for draft queries
- [ ] Monitoring logs populated with queries and feedback

Where to look in the code
-------------------------
- Retrieval & prompts: `src/rag.py`
- Data ingestion: `src/data_ingestion.py`
- Monitoring & logging: `src/realtime_monitoring.py` and `monitoring/` files

If you hit blockers, please open an issue on the repository or contact the maintainer via the Issues page.
```
#### 2. Data Ingestion Fails
**Problem:** Qdrant connection issues
```bash
# Solution: Restart Docker services
docker-compose down
docker-compose up -d qdrant
sleep 10
make ingest-data
```

#### 3. No AI Responses
**Problem:** Invalid Groq API key
- **Solution:** Verify API key at [console.groq.com](https://console.groq.com)
- **Alternative:** Enter API key in sidebar

#### 4. Search Issues
**Problem:** Player names not found
- **Expected:** System handles special characters automatically
- **Check:** Player names like "Jokić" should work correctly

### Performance Issues

```bash
# Check container status
docker-compose ps

# View application logs
docker-compose logs fantasy-nba

# View Qdrant logs
docker-compose logs qdrant

# Restart if needed
docker-compose restart
```

## 🎯 Success Criteria

Your setup is successful when:

✅ **Application loads** at http://localhost:8501  
✅ **Data ingestion completes** with 450+ players indexed  
✅ **Draft position queries work** (returns appropriate rank ranges)  
✅ **Player filtering works** (removes "already taken" players)  
✅ **AI responses generate** with valid Groq API key  
✅ **Sub-1 second response times** for all queries  

## 📞 Support

### Documentation References
- **User Guide:** README.md
- **Data Sources:** DATA_SOURCES.md

### Resources
- **Issues:** [GitHub Issues](https://github.com/idalbo/fantasy_nba_advisor/issues)
- **API Documentation:** [Groq Documentation](https://docs.groq.com)
- **Vector Database:** [Qdrant Documentation](https://qdrant.tech/documentation)

### Quick Help
- **Application not working?** Check logs with `docker-compose logs`
- **Need API key?** Get free key at [console.groq.com](https://console.groq.com)
- **Port conflicts?** Use `docker-compose down` then restart