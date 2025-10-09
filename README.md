# Fantasy NBA Advisor

**Fantasy NBA Advisor** is an advanced RAG (Retrieval-Augmented Generation) application that provides expert insights and advice for fantasy NBA players using **100% real NBA data** from Basketball Reference (2024-25 season).

## Key Features

- **🏀 Real NBA Data**: 450 NBA players with complete fantasy rankings and metrics
- **🎯 Smart Draft Recommendations**: Context-aware suggestions based on draft position and availability
- **🔍 Player Filtering**: Automatically removes "already taken" players from recommendations
- **🌟 Elite Player Recognition**: Accurate identification of top fantasy performers
- **💬 AI-Powered Analysis**: Conversational responses with expert fantasy insights
- **📊 Fantasy Metrics**: FPPM, fantasy points, availability scores, and expert rankings
- **🌍 International Player Support**: Handles special characters with Unicode normalization
- **🐳 Docker Containerized**: Fully containerized with Qdrant vector database for easy deployment

## Quick Start

### Prerequisites
- Docker and Docker Compose installed
- Internet connection for data scraping
- Groq API key (optional but recommended for AI features)

### 1. Data Ingestion (Real NBA Data)
Scrape and ingest real NBA player data from Basketball Reference:

```sh
make ingest-data
```
This process:
- Scrapes 450+ NBA players from Basketball Reference 2024-25 season
- Calculates fantasy metrics and rankings
- Displays top players with FPPM rankings
- Ingests all data into Qdrant vector database

### 2. Start Application
Once data ingestion is complete, start the application:

```sh
make project-run
```

The application is fully containerized using Docker and Docker Compose. After running, access it at `http://localhost:8501`.

### 3. API Configuration
- Get a free Groq API key at [console.groq.com](https://console.groq.com/)
- Enter your API key in the sidebar

## How It Works

The system uses an advanced fantasy evaluation methodology combining multiple data sources and metrics to provide accurate player recommendations and draft advice.

### Fantasy Points Calculation
The application calculates fantasy points using standard scoring: FT(1.5), 2P(2.5), 3P(3.5), rebounds(1.0), assists(1.0), steals(1.0), blocks(1.0), turnovers(-1.0), missed shots(-0.5).

### Player Ranking System
Players are ranked using Fantasy Points Per Minute (FPPM) combined with availability and role factors to identify the most valuable fantasy assets.

## Usage Guide

### Sample Queries

Try these queries to explore the system's capabilities:

#### **Draft Position Queries**
```
"Who should I pick at position 10?"
"What are good mid-round targets around pick 50?"
"Best late picks for round 15?"
```

#### **Player Filtering (Already Taken)**
```
"luka and wemby are already taken, who should I pick?"
"giannis is off the board, show me alternatives" 
"shai and jokic are taken, what's next?"
```

#### **Elite Player Analysis**
```
"Who are the top 5 players this season?"
"Best centers for fantasy basketball"
"Point guards with highest upside"
```

#### **Value Detection**
```
"Who are some sleepers I should bet on?"
"Show me undervalued players with injury concerns"
"Players with high efficiency but low draft position"
```

## Technical Architecture

### Enhanced RAG System
The application uses an advanced retrieval system with:

1. **Draft Position Intelligence**: Automatically filters players based on realistic availability
2. **Player Name Recognition**: Supports nicknames and common abbreviations  
3. **Multi-Field Weighting**: stats_narrative (60%), expert_analysis (10%), elite_ranking (30%)
4. **Contextual Filtering**: Removes "already taken" players from recommendations
5. **Rank-Based Targeting**: Returns players appropriate for specific draft positions

### Key Components

- **Data Sources**: Real NBA statistics from Basketball Reference
- **Vector Database**: Qdrant for hybrid search (text + vector similarity)
- **LLM Integration**: Groq API using `llama-3.1-8b-instant` model
- **Search Enhancement**: Context-aware query expansion for fantasy basketball terms
- **Unicode Processing**: Handles international characters with fuzzy name matching

## Environment Configuration

### Required Variables (.env):
```properties
# Groq API Configuration (Primary)
GROQ_API_KEY=your_groq_api_key_here

# Qdrant Configuration
QDRANT_HOST=localhost
QDRANT_PORT=6333

# Application Settings
DEBUG=true
LOG_LEVEL=INFO
```

## Troubleshooting

### Common Issues:
1. **API Key Errors**: Ensure valid Groq API key in sidebar or environment
2. **Search Results**: Special characters handled automatically with fuzzy matching
3. **Container Issues**: Restart with `docker-compose restart`

## Performance

- **Response Time**: Sub-1 second for all queries
- **Draft Position Accuracy**: Correctly targets appropriate rank ranges
- **Player Filtering**: 95%+ accuracy in detecting and removing unavailable players
- **AI Quality**: Contextual responses with detailed fantasy analysis

## Contributing

This project uses real NBA data and advanced RAG techniques. Contributions are welcome!

## License

MIT License - see LICENSE file for details.