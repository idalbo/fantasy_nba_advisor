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
fantasy_nba_advisor/
├── app.py                      # Main Streamlit application
├── src/
│   ├── rag.py                  # RAG system with hybrid search
│   ├── data_ingestion.py       # NBA data scraper
│   └── realtime_monitoring.py  # Usage analytics
├── data/
│   ├── player_embeddings.pkl   # Pre-computed vectors
│   └── player_metadata.json    # Player data cache
├── monitoring/                 # Interaction logs
├── evaluation/                 # Performance tests
├── docker-compose.yml          # Docker setup
└── requirements.txt            # Python dependencies
```

## How It Works

### 1. Data Collection
Scrapes Basketball Reference for current season stats, fantasy rankings, and expert analysis.

### 2. Hybrid Search
Combines two search methods:
- **Vector Search**: Semantic understanding using sentence embeddings (all-MiniLM-L6-v2)
- **Keyword Matching**: Exact matches for names, positions, teams

```python
hybrid_score = (0.7 * vector_similarity) + (0.3 * keyword_score)
```

### 3. RAG Pipeline
1. Query expansion with basketball context
2. Hybrid search retrieval
3. Rank-based filtering (±5 range)
4. LLM response generation (Groq/Llama 3.1)

## Technical Details

**LLM**: Groq API with Llama 3.1-8b-instant  
**Vector DB**: Qdrant (in-memory for cloud, local Docker for development)  
**Embeddings**: all-MiniLM-L6-v2 (384 dimensions)  
**Framework**: Streamlit for UI, Docker for deployment  

## Configuration

Create a `.env` file:

```bash
GROQ_API_KEY=your_groq_api_key
QDRANT_HOST=localhost
QDRANT_PORT=6333
```

Get a free Groq API key at [console.groq.com](https://console.groq.com/)

## Usage Examples

**Draft advice:**
- "Who should I pick at #16?"
- "Best centers for first round?"

**Player comparisons:**
- "Compare Jokic vs Embiid"
- "Who's better for my team?"

**Position analysis:**
- "Top point guards available"
- "Sleeper picks for late rounds"

## Monitoring

View analytics in the app sidebar:
- Query volume over time
- Response times
- Popular queries
- User feedback

Logs stored in `monitoring/interactions_*.jsonl`

## Testing

The project includes evaluation tests for retrieval accuracy:

```bash
python evaluation/comprehensive_evaluation.py
```

Current metrics:
- **Pass Rate**: 87.5%
- **Hit Rate**: 71.2%
- **Avg Response Time**: 0.21s

## Development

### Add New Data Sources

Edit `src/data_ingestion.py` to add scrapers for additional stats sites.

### Modify Search Logic

Update `src/rag.py`:
- `_expand_query()` - Query enhancement
- `_extract_metadata_filters()` - Filtering logic
- `search()` - Hybrid search algorithm

### Adjust League Settings

Change default league size in `app.py` sidebar or pass to RAG:

```python
rag = FantasyNBARag(groq_api_key=api_key, league_size=16)
```

## Docker Deployment

The app includes a complete Docker setup:

```yaml
services:
  qdrant:      # Vector database
  fantasy-nba: # Streamlit app
```

Qdrant runs on port 6335, app on port 8504.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Acknowledgments

- NBA data from Basketball Reference
- Built for DataTalksClub LLM Zoomcamp
- Uses Groq API for fast LLM inference

## Contact

**GitHub**: [@idalbo](https://github.com/idalbo)  
**Live Demo**: [fantasy-nba-advisor.streamlit.app](https://fantasy-nba-advisor.streamlit.app/)

---

Built with ❤️ for fantasy basketball enthusiasts
