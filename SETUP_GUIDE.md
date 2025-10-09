# Fantasy NBA Advisor - Setup Guide

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose installed
- Internet connection for data scraping
- Groq API key (free from [console.groq.com](https://console.groq.com))

### Installation (5 minutes)
```bash
# 1. Clone the repository
git clone https://github.com/idalbo/fantasy_nba_advisor.git
cd fantasy_nba_advisor

# 2. Configure environment variables
cp .env.example .env
# Edit .env file with your Groq API key

# 3. Start the application
make ingest-data    # First time only (ingests NBA data)
make project-run    # Starts the application

# 4. Access the application
open http://localhost:8501
```

## 💻 System Requirements

- **RAM:** 4GB minimum, 8GB recommended
- **Storage:** 2GB free space
- **Docker:** 20.0+ with Docker Compose
- **Web Browser:** Chrome, Firefox, Safari, or Edge

## 🔧 Detailed Setup Instructions

### Step 1: Environment Setup

1. **Clone the Repository**
   ```bash
   git clone https://github.com/idalbo/fantasy_nba_advisor.git
   cd fantasy_nba_advisor
   ```

2. **Create Environment File**
   ```bash
   cp .env.example .env
   ```

3. **Edit Environment Variables**
   Open `.env` in your preferred editor and configure:
   ```properties
   # Required - Get from https://console.groq.com
   GROQ_API_KEY=your_groq_api_key_here
   
   # Optional - Default values work for Docker setup
   QDRANT_HOST=localhost
   QDRANT_PORT=6333
   DEBUG=true
   LOG_LEVEL=INFO
   ```

### Step 2: Data Ingestion

The system requires NBA player data to function. Run this once:

```bash
make ingest-data
```

This command will:
- Start Qdrant vector database
- Scrape NBA statistics from Basketball Reference
- Process and index 450+ NBA players
- Calculate Fantasy Points Per Minute (FPPM) for each player
- Store everything in the vector database

**Expected Output:**
```
✅ Started Qdrant vector database
✅ Scraped 450+ NBA players from Basketball Reference
✅ Calculated FPPM and fantasy rankings
✅ Indexed all data in vector database
✅ Data ingestion completed successfully
```

### Step 3: Start the Application

```bash
make project-run
```

This starts:
- Qdrant vector database (if not already running)
- Streamlit web application on port 8501

### Step 4: Access and Configure

1. **Open your browser** to [http://localhost:8501](http://localhost:8501)

2. **Enter your Groq API key** in the sidebar
   - The application works without an API key for browsing data
   - AI chat features require a valid Groq API key

3. **Start using the application!**

## ⚙️ Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GROQ_API_KEY` | Yes | None | Your Groq API key for LLM features |
| `QDRANT_HOST` | No | localhost | Qdrant vector database host |
| `QDRANT_PORT` | No | 6333 | Qdrant vector database port |
| `DEBUG` | No | true | Enable debug logging |
| `LOG_LEVEL` | No | INFO | Logging level (DEBUG, INFO, WARNING, ERROR) |

### Docker Configuration

The application uses Docker Compose with these services:

```yaml
services:
  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6335:6333"
  
  fantasy-nba:
    build: .
    ports:
      - "8504:8501"
    depends_on:
      - qdrant
```

## 📚 Usage Examples

### Sample Queries

1. **Draft Position Queries**
   ```
   "Who should I pick at position 10?"
   "What are good mid-round targets around pick 50?"
   ```

2. **Player Filtering**
   ```
   "luka and wemby are already taken, who should I pick?"
   "giannis is off the board, show me alternatives"
   ```

3. **Elite Player Analysis**
   ```
   "Who are the top 5 players this season?"
   "Best centers for fantasy basketball"
   ```

4. **Value Detection**
   ```
   "Who are some sleepers I should bet on?"
   "Show me undervalued players with injury concerns"
   ```

## 📁 File Structure

```
fantasy_nba_advisor/
├── src/
│   ├── rag.py                      # Core RAG logic with draft intelligence
│   ├── app.py                      # Streamlit application interface
│   ├── data_ingestion.py           # NBA data scraping and processing
│   └── retrieval_evaluator.py      # In-app evaluation functionality
├── evaluation/
│   └── comprehensive_evaluation.py # Standalone testing script
├── docker-compose.yml              # Container orchestration
├── Dockerfile                      # Application container definition
├── requirements.txt                # Python dependencies
├── .env                            # Environment variables (create from .env.example)
├── README.md                       # User documentation
└── Makefile                        # Build and run commands
```

## 🛠️ Troubleshooting

### Common Issues

#### 1. Application Won't Start
**Problem:** Port conflicts
```bash
# Solution: Check if ports are in use
docker-compose down
make project-run
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