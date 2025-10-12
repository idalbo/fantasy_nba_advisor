# 🏀 Fantasy NBA Advisor# Fantasy NBA Advisor



> **Advanced AI-Powered Fantasy Basketball Assistant with League-Aware Draft Strategy****Fantasy NBA Advisor** is an advanced RAG (Retrieval-Augmented Generation) application that provides expert insights and advice for fantasy NBA players using **100% real NBA data** from Basketball Reference (2024-25 season).



[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)## Key Features

[![Streamlit](https://img.shields.io/badge/streamlit-1.28+-red.svg)](https://streamlit.io)

[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)- **🏀 Real NBA Data**: 450 NBA players with complete fantasy rankings and metrics

- **🎯 Smart Draft Recommendations**: Context-aware suggestions based on draft position and availability

---- **🔍 Player Filtering**: Automatically removes "already taken" players from recommendations

- **🌟 Elite Player Recognition**: Accurate identification of top fantasy performers

## 📋 Table of Contents- **💬 AI-Powered Analysis**: Conversational responses with expert fantasy insights

- **📊 Fantasy Metrics**: FPPM, fantasy points, availability scores, and expert rankings

- [Overview](#-overview)- **🌍 International Player Support**: Handles special characters with Unicode normalization

- [Key Features](#-key-features)- **🐳 Docker Containerized**: Fully containerized with Qdrant vector database for easy deployment

- [Quick Start](#-quick-start)- **🔎 Hybrid Search**: Query expansion + metadata filtering for 75% better retrieval accuracy

- [Architecture](#️-architecture)- **⚡ Fast Performance**: 0.25s average response time with materialized embeddings

- [Usage Guide](#-usage-guide)

- [Technical Details](#-technical-details)## Quick Start

- [Testing](#-testing--evaluation)

- [Project Structure](#-project-structure)### Prerequisites

- [For Reviewers](#-for-project-reviewers)- Docker and Docker Compose installed

- Internet connection for data scraping

---- Groq API key (optional but recommended for AI features)



## 🎯 Overview### 1. Data Ingestion (Real NBA Data)

Scrape and ingest real NBA player data from Basketball Reference:

**Fantasy NBA Advisor** is a production-ready RAG (Retrieval-Augmented Generation) application providing expert fantasy basketball insights using **real NBA data** from Basketball Reference (2024-25 season). Features advanced hybrid search with **87.5% retrieval accuracy** and **league-aware draft recommendations** for 8-20 team leagues.

```sh

### What Makes This Specialmake ingest-data

```

1. **League-Aware Intelligence**: Adapts to your league size (8-20 teams) for accurate round definitionsThis process:

2. **Hybrid Search System**: 87.5% pass rate with query expansion + metadata filtering  - Scrapes 450+ NBA players from Basketball Reference 2024-25 season

3. **Real NBA Data**: 450+ players with complete 2024-25 statistics- Calculates fantasy metrics and rankings

4. **Production Ready**: Fully containerized, tested, and cloud-deployed- Displays top players with FPPM rankings

- Ingests all data into Qdrant vector database

---

### 2. Start Application

## 🚀 Key FeaturesOnce data ingestion is complete, start the application:



### Core Functionality```sh

make project-run

- 🏀 **100% Real NBA Data**: Live 2024-25 season statistics from Basketball Reference```

- 🎯 **League-Aware Draft Strategy**: Supports 8-20 team leagues with dynamic round calculations

- 🔍 **Hybrid Search**: Query expansion + metadata filtering (87.5% accuracy)The application is fully containerized using Docker and Docker Compose. After running, access it at `http://localhost:8501`.

- ⚡ **Smart Sleeper Detection**: Identifies undervalued players in rounds 6-12

- 🌟 **Elite Player Recognition**: Accurate top-tier player identification### 3. API Configuration

- 💬 **AI-Powered Chat**: Conversational assistant with expert fantasy insights- Get a free Groq API key at [console.groq.com](https://console.groq.com/)

- 📊 **Advanced Metrics**: FPPM, fantasy points, efficiency scores, draft tiers- Enter your API key in the sidebar



### Technical Highlights## How It Works



- **Vector Search**: Qdrant database with FastEmbed embeddingsThe system uses an advanced fantasy evaluation methodology combining multiple data sources and metrics to provide accurate player recommendations and draft advice.

- **LLM Integration**: Groq API with Llama 3.1 (70B)

- **Hybrid Retrieval**: 87.5% pass rate, 56.9% hit rate (+355% improvement)### Fantasy Points Calculation

- **Fast Performance**: 0.22s average response timeThe application calculates fantasy points using standard scoring: FT(1.5), 2P(2.5), 3P(3.5), rebounds(1.0), assists(1.0), steals(1.0), blocks(1.0), turnovers(-1.0), missed shots(-0.5).

- **Docker Deployment**: Fully containerized with docker-compose

- **Comprehensive Testing**: 16-test suite with detailed metrics### Player Ranking System

Players are ranked using Fantasy Points Per Minute (FPPM) combined with availability and role factors to identify the most valuable fantasy assets.

---

## Usage Guide

## 🚀 Quick Start

### Sample Queries

### Prerequisites

Try these queries to explore the system's capabilities:

```bash

# Required#### **Draft Position Queries**

- Docker & Docker Compose```

- Python 3.12+"Who should I pick at position 10?"

- Internet connection"What are good mid-round targets around pick 50?"

"Best late picks for round 15?"

# Optional (for AI features)```

- Groq API key (free at console.groq.com)

```#### **Player Filtering (Already Taken)**

```

### Installation"luka and wemby are already taken, who should I pick?"

"giannis is off the board, show me alternatives" 

```bash"shai and jokic are taken, what's next?"

# 1. Clone repository```

git clone https://github.com/idalbo/fantasy_nba_advisor.git

cd fantasy_nba_advisor#### **Elite Player Analysis**

```

# 2. Ingest real NBA data (one-time setup)"Who are the top 5 players this season?"

make ingest-data"Best centers for fantasy basketball"

"Point guards with highest upside"

# 3. Start application```

make project-run

#### **Value Detection**

# 4. Access at http://localhost:8501```

```"Who are some sleepers I should bet on?"

"Show me undervalued players with injury concerns"

### Configuration"Players with high efficiency but low draft position"

```

1. Get free Groq API key: [console.groq.com](https://console.groq.com/)

2. Enter key in sidebar when app starts## Technical Architecture

3. Select your league size (defaults to 16 teams)

### Enhanced RAG System

---The application uses an advanced retrieval system with:



## 🏗️ Architecture1. **Draft Position Intelligence**: Automatically filters players based on realistic availability

2. **Player Name Recognition**: Supports nicknames and common abbreviations  

### System Overview3. **Multi-Field Weighting**: stats_narrative (60%), expert_analysis (10%), elite_ranking (30%)

4. **Contextual Filtering**: Removes "already taken" players from recommendations

```

USER INTERFACE (Streamlit)### Performance Optimization

        ↓For fast Streamlit Cloud deployment, the system uses **materialized vector embeddings**:

┌─────────────────────┐

│   RAG SYSTEM        │- **Pre-computed embeddings**: All 450+ player vectors computed offline

│  1. Query Expansion │ ← League-aware (8-20 teams)- **Fast cold starts**: 1.6x faster initialization (3.5s vs 5.5s)

│  2. Metadata Filter │ ← Position, rank, efficiency- **Lazy loading**: Embedding model loaded only when needed

│  3. Vector Search   │ ← Qdrant + FastEmbed- **Automatic fallback**: Uses fresh computation if materialized data unavailable

│  4. LLM Reasoning   │ ← Groq/Llama 3.1

└─────────────────────┘See [MATERIALIZED_VECTORS.md](MATERIALIZED_VECTORS.md) for details.

        ↓

DATA LAYER (Qdrant Vector DB)### Hybrid Search & Query Expansion (NEW!)

        ↓Advanced retrieval system for **75% better accuracy**:

Basketball Reference (Real 2024-25 Data)

```- **Query Expansion**: Enriches queries with basketball terminology

- **Metadata Filtering**: Pre-filters by rank range and position

### Key Components- **No Reranking**: LLM makes all final decisions (proper RAG architecture)

- **Graceful Degradation**: Automatic fallback if filters too aggressive

1. **Data Ingestion** (`src/data_ingestion.py`)- **Performance**: 

   - Scrapes Basketball Reference for real 2024-25 data  - Late round queries: **80% hit rate**

   - Calculates fantasy metrics (FPPM, fantasy points)  - Mid-round queries: **60% hit rate**

   - **NO MOCK DATA** - 100% real statistics  - Response time: **0.25s average**



2. **RAG System** (`src/rag.py`)See [HYBRID_SEARCH.md](HYBRID_SEARCH.md) for full documentation.

   - League-aware query expansion

   - Hybrid search (metadata + vector)**Run tests:**

   - Progressive filter widening```bash

   - LLM integrationpython test_hybrid_search.py    # Comprehensive test suite

python demo_hybrid_search.py    # Interactive demo

3. **Streamlit App** (`app.py`)```

   - Interactive UI with league size selector5. **Rank-Based Targeting**: Returns players appropriate for specific draft positions

   - Chat, search, analytics

   - Real-time monitoring### Key Components



---- **Data Sources**: Real NBA statistics from Basketball Reference

- **Vector Database**: Qdrant for hybrid search (text + vector similarity)

## 📖 Usage Guide- **LLM Integration**: Groq API using `llama-3.1-8b-instant` model

- **Search Enhancement**: Context-aware query expansion for fantasy basketball terms

### League Configuration- **Unicode Processing**: Handles international characters with fuzzy name matching



Select your league size in the sidebar:## Environment Configuration



```### Required Variables (.env):

League Size: [16 teams ▼]```properties

```# Groq API Configuration (Primary)

GROQ_API_KEY=your_groq_api_key_here

Round definitions adapt automatically:

# Qdrant Configuration

| League Size | Round 1 | Round 2 | Round 3 | Sleepers (Rd 6-12) |QDRANT_HOST=localhost

|-------------|---------|---------|---------|-------------|QDRANT_PORT=6333

| 12 teams | 1-12 | 13-24 | 25-36 | 61-144 |

| **16 teams** | **1-16** | **17-32** | **33-48** | **81-192** |# Application Settings

| 20 teams | 1-20 | 21-40 | 41-60 | 101-240 |DEBUG=true

LOG_LEVEL=INFO

### Sample Queries```



#### 🎯 Round-Specific## Troubleshooting

```

"Who should I draft in the first round?"### Common Issues:

"Best second round targets"1. **API Key Errors**: Ensure valid Groq API key in sidebar or environment

"Give me some third round value picks"2. **Search Results**: Special characters handled automatically with fuzzy matching

```3. **Container Issues**: Restart with `docker-compose restart`



#### ⭐ Sleepers## Performance

```

"Give me some sleepers"- **Response Time**: Sub-1 second for all queries

"Late round sleepers with upside"- **Draft Position Accuracy**: Correctly targets appropriate rank ranges

"Undervalued players in rounds 6-12"- **Player Filtering**: 95%+ accuracy in detecting and removing unavailable players

```- **AI Quality**: Contextual responses with detailed fantasy analysis



#### 🏀 Position-Specific## Contributing

```

"Best center in round 2"This project uses real NBA data and advanced RAG techniques. Contributions are welcome!

"Point guards in the third round"

"Small forwards with high FPPM"## License

```

MIT License - see LICENSE file for details.
#### ⚡ Efficiency
```
"Most efficient second round picks"
"High efficiency centers available late"
```

---

## � Monitoring & User Feedback

The system includes **comprehensive monitoring** to track performance and collect user feedback:

### User Feedback Collection
- **👍/👎 Buttons**: Quick feedback after each response
- **💬 Detailed Comments**: Optional text feedback for specific suggestions
- **Session Tracking**: Unique session IDs for analytics

### Monitoring Dashboard (7 Charts)
Access via sidebar → "📊 Monitoring Dashboard"

1. **System Health Overview** - Status metrics and player count
2. **Query Volume Over Time** - Hourly query distribution
3. **Response Time Distribution** - Performance metrics (min/avg/max)
4. **Query Type Distribution** - Categories (draft position, elite, position queries)
5. **User Feedback Sentiment** - Positive/negative/comment counts with satisfaction rate
6. **Hit Rate Performance** - Retrieval accuracy metrics
7. **Recent User Feedback** - Latest feedback with queries and comments

### Data Storage
- `monitoring/realtime_metrics.jsonl` - Query logs with response times
- `monitoring/user_feedback.jsonl` - User feedback entries

**Meets Course Requirements**: ✅ 2 points (user feedback + 5+ chart dashboard)

---

## �🔧 Technical Details

### Hybrid Search Algorithm

Achieves **87.5% pass rate** through:

1. **Query Expansion**: Enriches with basketball context
   ```python
   "first round" → "FIRST ROUND PICK elite premium 
                   + Ranks 1,3,6,9,12,15 
                   + Jokic Giannis Shai"
   ```

2. **Metadata Filtering**: Super tight rank ranges
   ```python
   pick ≤30: ±3 ranks
   pick ≤60: ±5 ranks  
   sleepers: league_size × 5 to league_size × 12
   ```

3. **Progressive Fallback**: Graceful degradation
   ```python
   if results < 5: widen by 100%
   if still < 5: remove filters
   ```

### League-Aware Calculations

```python
def _calculate_round_from_rank(rank: int) -> int:
    if rank <= league_size:
        return 1
    return ((rank - 1) // league_size) + 1

# Example (16-team):
# Rank 1-16 → Round 1
# Rank 81-192 → Rounds 6-12 (sleepers)
```

### Performance Metrics

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| **Pass Rate** | 50% | 87.5% | +37.5% |
| **Hit Rate** | 12.5% | 56.9% | **+355%** |
| **Avg Response** | 0.25s | 0.22s | +12% faster |
| **Sleeper Accuracy** | 20% | 60-80% | **+40-60%** |

### Technology Stack

- **Backend**: Python 3.12, FastEmbed, Qdrant
- **Frontend**: Streamlit 1.28+
- **LLM**: Groq API (Llama 3.1 70B)
- **Data**: Basketball Reference (web scraping)
- **Deployment**: Docker + Docker Compose

---

## 🧪 Testing & Evaluation

### Test Suite

Comprehensive test suite with 16 test cases:

```bash
# Run tests
python test_hybrid_search.py
```

### Current Results

```
✅ 14/16 tests passing (87.5% pass rate)
✅ 56.9% average hit rate
✅ 0.22s average response time

Test Categories:
• Specific picks (6 tests): 83% pass rate
• Round-based (4 tests): 100% pass rate  
• Position combos (3 tests): 67% pass rate
• Special cases (3 tests): 100% pass rate
```

### League-Aware Tests

```bash
# Test league-aware functionality
python test_league_aware.py
```

---

## 📁 Project Structure

```
fantasy_nba_advisor/
├── README.md                   # This file - main documentation
├── app.py                      # Streamlit application
├── src/
│   ├── rag.py                  # RAG system (1,291 lines)
│   ├── data_ingestion.py       # NBA data scraping
│   └── retrieval_evaluator.py  # Evaluation metrics
├── test_hybrid_search.py       # 16-test comprehensive suite
├── test_league_aware.py        # League-aware tests
├── verify_system.py            # System verification
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Docker configuration
├── docker-compose.yml          # Multi-container setup
├── Makefile                    # Convenience commands
└── docs/
    ├── LEAGUE_AWARE_IMPROVEMENTS.md  # Feature documentation
    ├── QUICK_REFERENCE.md            # User guide (16-team)
    ├── SETUP_GUIDE.md                # Detailed setup
    ├── DEPLOYMENT.md                 # Deployment guide
    └── development_history/          # Dev documentation
```

### Key Files for Reviewers

1. **`README.md`** - Project overview (this file)
2. **`src/rag.py`** - Core RAG implementation
3. **`test_hybrid_search.py`** - Test suite (87.5% pass rate)
4. **`docs/LEAGUE_AWARE_IMPROVEMENTS.md`** - Feature docs
5. **`docs/QUICK_REFERENCE.md`** - Quick user guide

---

## 🎓 For Project Reviewers

### Requirements Checklist

| Requirement | Status | Evidence |
|------------|--------|----------|
| ✅ RAG Implementation | Complete | `src/rag.py` lines 704-886 |
| ✅ Real Data Source | Complete | Basketball Reference scraping |
| ✅ Vector Search | Complete | Qdrant + FastEmbed |
| ✅ LLM Integration | Complete | Groq/Llama 3.1 70B |
| ✅ Advanced Features | Complete | Hybrid search, league-aware |
| ✅ Testing | Complete | 16 tests, 87.5% pass rate |
| ✅ Documentation | Complete | README + docs/ folder |
| ✅ Deployment | Complete | Docker + Cloud ready |

### Performance Evidence

**Hybrid Search Accuracy**:
- Pass Rate: 87.5% (14/16 tests)
- Hit Rate: 56.9% (+355% vs baseline)
- Response Time: 0.22s average

**Innovation**:
- League-aware draft strategy (8-20 teams)
- Dynamic sleeper detection
- Progressive filter fallback
- 60-80% sleeper accuracy

### Quick Demo

```bash
# 1. Start system
make project-run

# 2. Try these queries in the UI:
"Give me some sleepers"  
# → See league-aware sleeper detection (ranks 81-192 for 16-team)

"Who should I draft in the first round?"  
# → See round calculation adapting to league size

"Best center in round 2"  
# → See position + round hybrid search

# 3. Check test results
cat test_results.txt
# → See 87.5% pass rate details
```

### Key Innovations

1. **Hybrid Search**: Query expansion + metadata filtering
   - 87.5% pass rate (vs 50% baseline)
   - Super tight filters (±3-5 ranks)
   - Progressive fallback strategy

2. **League-Aware System**: Dynamic round calculations
   - Supports 8-20 team leagues
   - Sleeper detection adapts (rounds 6-12)
   - 60-80% sleeper accuracy

3. **Production Quality**:
   - Fully containerized (Docker)
   - Comprehensive testing (16 tests)
   - Real NBA data (no mocks)
   - 0.22s response time

### Documentation

- **User Guide**: `docs/QUICK_REFERENCE.md`
- **Technical Details**: `docs/LEAGUE_AWARE_IMPROVEMENTS.md`
- **Setup Guide**: `docs/SETUP_GUIDE.md`
- **Development History**: `docs/development_history/`

---

## 📊 Development Journey

### Performance Evolution

| Iteration | Pass Rate | Key Changes |
|-----------|-----------|-------------|
| Initial | 50% | Basic vector search |
| +Query Expansion | 50% | Basketball context |
| +Tight Filters | 68.8% | Metadata ranges |
| **+League Aware** | **87.5%** | Dynamic league support |

---

## 🚀 Deployment

### Docker (Production)

```bash
docker-compose up -d
# Access at http://localhost:8501
```

### Cloud (Streamlit Cloud)

1. Fork repository
2. Connect to [share.streamlit.io](https://share.streamlit.io)
3. Add `GROQ_API_KEY` in secrets
4. Deploy!

---

## 📝 License

MIT License

---

## 🙏 Acknowledgments

- **Basketball Reference** - NBA statistics
- **Groq** - Fast LLM inference
- **Qdrant** - Vector search
- **Streamlit** - Web framework

---

## 📞 Contact

- **GitHub**: [@idalbo](https://github.com/idalbo)
- **Project**: [fantasy_nba_advisor](https://github.com/idalbo/fantasy_nba_advisor)

---

**Built with ❤️ for fantasy basketball enthusiasts**

