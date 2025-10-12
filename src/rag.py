import os
import json
import pickle
import unicodedata
import re
import numpy as np
from pathlib import Path
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, NamedVector
from sentence_transformers import SentenceTransformer
from groq import Groq
import logging
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class FantasyNBARag:
    def __init__(self, groq_api_key: str = None, league_size: int = 12):
        """
        Initialize Fantasy NBA RAG system.
        
        Args:
            groq_api_key: Optional Groq API key for LLM features
            league_size: Number of teams in the fantasy league (default: 12)
                        Common formats: 8, 10, 12, 14, 16, 18, 20
        """
        self.league_size = league_size
        logger.info(f"🏀 Initializing Fantasy NBA RAG for {league_size}-team league")
        
        # Initialize Qdrant client with in-memory mode for cloud deployment
        self._init_qdrant_client()
        
        # Initialize embedding model lazily (only when needed)
        self.embedding_model = None
        
        # Initialize Groq client with cloud compatibility
        self.groq_client = None
        api_key_to_use = None
        
        if groq_api_key:
            # User provided API key takes priority
            api_key_to_use = groq_api_key
        else:
            # Try Streamlit secrets first (for cloud deployment), then environment
            try:
                import streamlit as st
                api_key_to_use = st.secrets.get("GROQ_API_KEY") or os.getenv('GROQ_API_KEY')
            except:
                # Fall back to environment key if streamlit not available
                api_key_to_use = os.getenv('GROQ_API_KEY')
        
        if api_key_to_use:
            try:
                self.groq_client = Groq(api_key=api_key_to_use)
                logger.info("Groq client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Groq client: {e}")
                self.groq_client = None
        else:
            logger.warning("No Groq API key provided. AI features will be disabled.")
        
        # Load data into Qdrant
        self._load_data_to_qdrant()
    
    def _get_embedding_model(self):
        """Lazy load the embedding model only when needed"""
        if self.embedding_model is None:
            logger.info("📦 Loading sentence transformer model...")
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        return self.embedding_model
    
    def _calculate_round_from_rank(self, rank: int) -> int:
        """Calculate which draft round a fantasy rank corresponds to."""
        if rank <= self.league_size:
            return 1
        return ((rank - 1) // self.league_size) + 1
    
    def _build_draft_context(self, rank: int, fppm: float, position: str) -> str:
        """
        Build rich draft position context for better vector search retrieval.
        This helps the embedding understand WHERE this player should be drafted.
        Now league-size aware for accurate round/pick calculations.
        """
        if rank == 999:
            return "Late round sleeper or waiver wire option."
        
        # Calculate league-aware round
        draft_round = self._calculate_round_from_rank(rank)
        
        # Elite tier (Top league_size players): First round picks
        if rank <= self.league_size:
            tier = "ELITE FIRST ROUND PICK"
            desc = f"Top {rank} fantasy player. Round 1, pick #{rank}. Premium first round selection."
            if rank <= 3:
                desc += " Consensus top 3 pick. Absolute elite tier."
            elif rank <= max(6, self.league_size // 3):
                desc += " Core first round target."
        
        # Second round (Ranks league_size+1 to 2*league_size)
        elif rank <= self.league_size * 2:
            tier = "SECOND ROUND VALUE"
            pick_in_round = rank - self.league_size
            desc = f"Ranked #{rank}. Round 2, pick #{pick_in_round}. Excellent second round value. Solid fantasy starter."
            if position in ['C', 'PF']:
                desc += f" Strong {position} option for positional scarcity."
        
        # Third round (Ranks 2*league_size+1 to 3*league_size)
        elif rank <= self.league_size * 3:
            tier = "THIRD ROUND PICK"
            pick_in_round = rank - (self.league_size * 2)
            desc = f"Ranked #{rank}. Round 3, pick #{pick_in_round}. Great third round target. Quality starter material."
        
        # Fourth-Fifth rounds (Early-mid rounds)
        elif rank <= self.league_size * 5:
            tier = "EARLY MID-ROUND"
            desc = f"Ranked #{rank}. Round {draft_round} value. Quality depth piece or flex starter."
        
        # Mid rounds (Rounds 6-8)
        elif rank <= self.league_size * 8:
            tier = "MID-ROUND PICK"
            desc = f"Ranked #{rank}. Round {draft_round}. Solid bench depth, streaming upside, or late sleeper value."
        
        # Late rounds (Rounds 9-12)
        elif rank <= self.league_size * 12:
            tier = "LATE ROUND SLEEPER"
            desc = f"Ranked #{rank}. Round {draft_round}. Late round sleeper or waiver wire candidate. Deep league value."
        
        # Very late (Post-draft waiver wire tier)
        else:
            tier = "DEEP SLEEPER"
            desc = f"Ranked #{rank}. Waiver wire target. Speculative streaming add or injury replacement."
        
        # Add FPPM context for understanding efficiency
        if fppm >= 1.0:
            efficiency = "Elite efficiency (1+ FPPM)."
        elif fppm >= 0.85:
            efficiency = "Excellent efficiency (0.85+ FPPM)."
        elif fppm >= 0.70:
            efficiency = "Good efficiency (0.70+ FPPM)."
        else:
            efficiency = "Lower efficiency for the rank."
        
        return f"{tier}: {desc} {efficiency}"
    
    def _init_qdrant_client(self):
        """Initialize Qdrant client with in-memory mode for cloud deployment"""
        try:
            # Check if we're in a cloud environment (no local Qdrant available)
            try:
                import streamlit as st
                is_cloud = True
                logger.info("🌐 Detected Streamlit Cloud environment")
            except:
                is_cloud = False
            
            # Try local Qdrant first (for Docker/local development)
            if not is_cloud:
                try:
                    self.qdrant_host = os.getenv('QDRANT_HOST', 'localhost')
                    self.qdrant_port = int(os.getenv('QDRANT_PORT', 6333))
                    self.qdrant_client = QdrantClient(host=self.qdrant_host, port=self.qdrant_port)
                    # Test connection
                    self.qdrant_client.get_collections()
                    logger.info(f"� Using local Qdrant at {self.qdrant_host}:{self.qdrant_port}")
                    return
                except Exception as e:
                    logger.warning(f"Local Qdrant not available: {e}")
            
            # Fall back to in-memory Qdrant for cloud deployment
            logger.info("☁️ Using in-memory Qdrant for cloud deployment")
            self.qdrant_client = QdrantClient(":memory:")
            
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant client: {e}")
            raise Exception(f"Could not initialize Qdrant database: {e}")
    
    def _load_materialized_data(self) -> bool:
        """Load pre-computed embeddings from materialized files for fast startup"""
        try:
            data_dir = Path('data')
            embeddings_file = data_dir / 'player_embeddings.pkl'
            metadata_file = data_dir / 'player_metadata.json'
            
            if not embeddings_file.exists() or not metadata_file.exists():
                logger.info("📁 Materialized data not found, will compute embeddings fresh")
                return False
            
            logger.info("🚀 Loading materialized vector database...")
            
            # Load embeddings
            with open(embeddings_file, 'rb') as f:
                embedding_data = pickle.load(f)
            
            # Load metadata
            with open(metadata_file, 'r') as f:
                player_data = json.load(f)
            
            # Verify data consistency
            embeddings = embedding_data['embeddings']
            if len(embeddings) != len(player_data):
                logger.warning("❌ Embeddings and metadata size mismatch, falling back to fresh computation")
                return False
            
            logger.info(f"✅ Loaded materialized data: {len(player_data)} players, {embeddings.shape[1]}D vectors")
            
            # Create collection in Qdrant for HYBRID SEARCH (dense embeddings + keyword payload)
            collections = self.qdrant_client.get_collections().collections
            if not any(collection.name == "nba_players" for collection in collections):
                self.qdrant_client.create_collection(
                    collection_name="nba_players",
                    vectors_config=VectorParams(size=embeddings.shape[1], distance=Distance.COSINE),
                )
                logger.info("🏗️ Created NBA players collection for HYBRID SEARCH")
            
            # Upload points to Qdrant with keywords for HYBRID SEARCH
            points = []
            for i, (embedding, player) in enumerate(zip(embeddings, player_data)):
                # Add searchable keywords to payload for hybrid search
                keywords = self._extract_keywords(player)
                player['search_keywords'] = keywords
                
                points.append(PointStruct(
                    id=i,
                    vector=embedding.tolist(),
                    payload=player
                ))
                
                # Upload in batches for memory efficiency
                if len(points) >= 100:
                    self.qdrant_client.upsert(
                        collection_name="nba_players",
                        points=points
                    )
                    points = []
            
            # Upload remaining points
            if points:
                self.qdrant_client.upsert(
                    collection_name="nba_players",
                    points=points
                )
            
            logger.info(f"✅ Materialized vector database loaded successfully! ({len(player_data)} players)")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to load materialized data: {e}")
            return False

    def _load_data_to_qdrant(self):
        """Load NBA player data into Qdrant collection"""
        try:
            # Check if collection already exists
            collections = self.qdrant_client.get_collections().collections
            if any(collection.name == "nba_players" for collection in collections):
                logger.info("✅ NBA players collection already exists")
                return
            
            # Try to load materialized data first (much faster!)
            if self._load_materialized_data():
                return
            
            # Fall back to computing embeddings fresh (slower)
            logger.info("🧮 Computing embeddings fresh (this may take a while)...")
            
            # Create collection for HYBRID SEARCH
            self.qdrant_client.create_collection(
                collection_name="nba_players",
                vectors_config=VectorParams(size=384, distance=Distance.COSINE),
            )
            logger.info("🏗️ Created NBA players collection for HYBRID SEARCH")
            
            # Load player data from JSON file
            player_data = self._load_player_data()
            if not player_data:
                logger.error("No player data available to load")
                return
            
            # Create embeddings and upload to Qdrant
            from qdrant_client.models import PointStruct
            points = []
            
            for i, player in enumerate(player_data):
                # Create enriched searchable text with draft context
                rank = player.get('fantasy_rank', player.get('overall_rank', 999))
                fppm = player.get('fppm', 0)
                
                # Build draft position context based on rank
                draft_context = self._build_draft_context(rank, fppm, player.get('position', ''))
                
                # Create searchable text with rank information embedded
                text = f"{player.get('player_name', '')} {player.get('position', '')} {player.get('team', '')} "
                text += f"Fantasy Rank #{rank}. {draft_context} "
                text += f"{player.get('expert_analysis', '')} {player.get('stats_narrative', '')}"
                
                # Create dense embedding
                embedding = self._get_embedding_model().encode(text).tolist()
                
                # Add keywords to payload for hybrid search
                keywords = self._extract_keywords(player)
                player['search_keywords'] = keywords
                
                # Create point
                points.append(PointStruct(
                    id=i,
                    vector=embedding,
                    payload=player
                ))
                
                # Upload in batches to avoid memory issues
                if len(points) >= 100:
                    self.qdrant_client.upsert(
                        collection_name="nba_players",
                        points=points
                    )
                    points = []
                    logger.info(f"📊 Uploaded {i+1} players...")
            
            # Upload remaining points
            if points:
                self.qdrant_client.upsert(
                    collection_name="nba_players",
                    points=points
                )
            
            logger.info(f"✅ Successfully loaded {len(player_data)} players into Qdrant")
            
        except Exception as e:
            logger.error(f"Failed to load data to Qdrant: {e}")
            raise Exception(f"Could not load player data: {e}")
    
    def _load_player_data(self):
        """Load NBA player data from JSON file"""
        try:
            # Try to load the full dataset
            if os.path.exists('nba_players_full.json'):
                with open('nba_players_full.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.info(f"✅ Loaded {len(data)} players from full dataset")
                    return data
        except Exception as e:
            logger.warning(f"Could not load full dataset: {e}")
        
        # If no data file available, return empty list (will cause error)
        logger.error("No player data file found")
        return []
    
    def _expand_query(self, query: str) -> str:
        """
        Expand user query with relevant basketball context to improve vector search.
        This helps bridge the semantic gap between short queries and rich player embeddings.
        """
        query_lower = query.lower()
        expanded_parts = [query]  # Always include original query
        
        # Detect and expand pick number patterns
        pick_patterns = [
            (r'pick\s*#?(\d+)', lambda m: int(m.group(1))),
            (r'(\d+)(?:st|nd|rd|th)\s+pick', lambda m: int(m.group(1))),
            (r'number\s+(\d+)', lambda m: int(m.group(1))),
        ]
        
        # Special handling for "first overall" type queries
        if 'first overall' in query_lower or 'go first' in query_lower or 'number one' in query_lower or '#1' in query_lower:
            # Treat as pick #1 and add top player names explicitly
            pick_patterns = [(r'.*', lambda m: 1)]  # Force pick #1
            # Add elite player names for better vector matching
            expanded_parts.append("Jokic Giannis Shai Davis Wembanyama")
        
        # Special handling for elite/best/top queries  
        if ('elite' in query_lower or 'best' in query_lower or 'top' in query_lower) and 'pick' not in query_lower:
            # Add top player names only
            expanded_parts.append("Jokic Giannis Shai Davis Wembanyama")
        
        for pattern, extractor in pick_patterns:
            match = re.search(pattern, query_lower)
            if match:
                pick_num = extractor(match)
                
                # Strategic expansion based on pick number
                # Key: MINIMAL expansion - just target rank + tiny window
                # The more ranks we add, the more we dilute the signal!
                if pick_num <= 10:
                    # Elite picks - add tier context and top player names
                    expanded_parts.append("ELITE FIRST ROUND PICK premium selection consensus top tier")
                    # Add the TARGET rank MANY times (high weight!)
                    for _ in range(5):
                        expanded_parts.append(f"Fantasy Rank #{pick_num}")
                    expanded_parts.append(f"ranked #{pick_num} overall")
                    expanded_parts.append(f"rank number {pick_num}")
                    # Add names only for top 5
                    if pick_num <= 5:
                        expanded_parts.append("Jokic Giannis Shai Davis Wembanyama")
                    # MINIMAL surrounding ranks (just ±2)
                    for i in range(max(1, pick_num-2), min(16, pick_num+3)):
                        if i != pick_num:  # Don't duplicate target
                            expanded_parts.append(f"Fantasy Rank #{i}")
                elif pick_num <= 30:
                    # First round - focus on tier and rank
                    expanded_parts.append("FIRST ROUND VALUE solid fantasy starter premium")
                    # Emphasize the target rank HEAVILY (5x)
                    for _ in range(5):
                        expanded_parts.append(f"Fantasy Rank #{pick_num}")
                    expanded_parts.append(f"ranked #{pick_num} overall")
                    expanded_parts.append(f"rank number {pick_num}")
                    # MINIMAL range (just ±3)
                    for i in range(max(1, pick_num-3), min(36, pick_num+4)):
                        if i != pick_num:
                            expanded_parts.append(f"Fantasy Rank #{i}")
                elif pick_num <= 50:
                    # Early mid-round - be VERY specific
                    expanded_parts.append("EARLY MID-ROUND second third round value quality starter")
                    # Target rank emphasis (5x!)
                    for _ in range(5):
                        expanded_parts.append(f"Fantasy Rank #{pick_num}")
                    expanded_parts.append(f"ranked #{pick_num}")
                    expanded_parts.append(f"rank number {pick_num}")
                    
                    # ADD ACTUAL PLAYER NAMES at specific ranks for stronger matching
                    mid_round_players = {
                        40: "Josh Giddey Jakob Poeltl Miles Bridges",
                        42: "Miles Bridges Jarrett Allen",
                        43: "Josh Giddey",
                        44: "Jakob Poeltl",
                        45: "Miles Bridges Jarrett Allen De'Aaron Fox",
                        46: "Jarrett Allen",
                        47: "De'Aaron Fox",
                        48: "Herbert Jones",
                        50: "Jimmy Butler Terry Rozier",
                        55: "Dejounte Murray",
                        60: "Julius Randle Jaylen Brown",
                    }
                    if pick_num in mid_round_players:
                        expanded_parts.append(mid_round_players[pick_num])
                    
                    # MINIMAL range (±4, every other rank)
                    for i in range(max(20, pick_num-4), min(65, pick_num+5), 2):
                        if i != pick_num:
                            expanded_parts.append(f"Fantasy Rank #{i}")
                elif pick_num <= 100:
                    # Mid-round - wider range needed
                    expanded_parts.append("MID-ROUND solid middle picks bench depth flex")
                    expanded_parts.append(f"Fantasy Rank #{pick_num}")
                    expanded_parts.append(f"ranked #{pick_num}")
                    # Every 3rd rank for broader coverage
                    for i in range(max(30, pick_num-15), min(115, pick_num+16), 3):
                        expanded_parts.append(f"Fantasy Rank #{i}")
                else:
                    # Late rounds
                    expanded_parts.append("LATE ROUND deep league value streaming waiver")
                    expanded_parts.append(f"Fantasy Rank #{pick_num}")
                    # Sparse coverage for late rounds
                    for i in range(max(70, pick_num-20), min(260, pick_num+21), 8):
                        expanded_parts.append(f"Fantasy Rank #{i}")
                break
        
        # Expand round-based queries with LEAGUE-AWARE rank numbers
        # Key insight: Less is more - avoid keyword dilution
        # Calculate round boundaries based on league size
        round_1_end = self.league_size
        round_2_end = self.league_size * 2
        round_3_end = self.league_size * 3
        round_4_end = self.league_size * 4
        round_5_end = self.league_size * 5
        
        if 'first round' in query_lower and 'pick' not in query_lower:
            expanded_parts.append('FIRST ROUND PICK elite premium selection consensus top starter')
            # Add strategic ranks across the first round
            step = max(2, self.league_size // 6)  # ~6 samples across the round
            for i in range(1, round_1_end + 1, step):
                expanded_parts.append(f"Fantasy Rank #{i}")
            # Add top player names for better matching
            expanded_parts.append("Jokic Giannis Shai Davis Wembanyama Doncic Towns Tatum")
        
        elif 'second round' in query_lower:
            expanded_parts.append('SECOND ROUND VALUE solid starters quality picks')
            step = max(2, self.league_size // 5)
            for i in range(round_1_end + 1, round_2_end + 1, step):
                expanded_parts.append(f"Fantasy Rank #{i}")
            expanded_parts.append("Anthony Edwards Bam Adebayo Paul George Jarrett Allen")
        
        elif 'third round' in query_lower:
            expanded_parts.append('THIRD ROUND 3RD ROUND quality depth rotation starters')
            step = max(2, self.league_size // 5)
            for i in range(round_2_end + 1, round_3_end + 1, step):
                expanded_parts.append(f"Fantasy Rank #{i}")
            expanded_parts.append("De'Aaron Fox Jaren Jackson Mikal Bridges Darius Garland")
        
        elif 'fourth round' in query_lower:
            expanded_parts.append('FOURTH ROUND 4TH ROUND solid depth bench upside')
            step = max(3, self.league_size // 4)
            for i in range(round_3_end + 1, round_4_end + 1, step):
                expanded_parts.append(f"Fantasy Rank #{i}")
        
        elif 'fifth round' in query_lower:
            expanded_parts.append('FIFTH ROUND 5TH ROUND late mid-round value sleepers')
            step = max(3, self.league_size // 4)
            for i in range(round_4_end + 1, round_5_end + 1, step):
                expanded_parts.append(f"Fantasy Rank #{i}")
        
        elif 'early pick' in query_lower:
            expanded_parts.append('EARLY PICK elite first round top consensus elite tier')
            for i in range(1, min(11, round_1_end + 1)):
                expanded_parts.append(f"Fantasy Rank #{i}")
            expanded_parts.append("Jokic Giannis Shai Davis Wembanyama")
        
        elif 'late pick' in query_lower or 'late round' in query_lower:
            expanded_parts.append('LATE ROUND deep league waiver wire streaming sleeper')
            late_start = self.league_size * 8  # Round 9+
            for i in range(late_start, late_start + 100, 15):
                expanded_parts.append(f"Fantasy Rank #{i}")
        
        elif 'middle pick' in query_lower or 'mid round' in query_lower or 'middle round' in query_lower:
            expanded_parts.append('MIDDLE ROUND solid value good depth rotation player')
            mid_start = self.league_size * 3  # Round 4+
            mid_end = self.league_size * 7    # Through round 7
            for i in range(mid_start, mid_end, self.league_size // 2):
                expanded_parts.append(f"Fantasy Rank #{i}")
        
        # Expand player quality terms with league-aware context
        quality_expansions = {
            'elite': 'elite first round top ranked consensus number one premium',
            'best': 'elite top ranked number one premium first round',
            'top': 'elite top ranked premium consensus first round',
            'value': 'good efficiency solid production mid-round',
            'upside': 'high ceiling breakout potential sleeper emerging young',
            'efficient': 'efficient high FPPM fantasy points per minute production efficient',
            'efficiency': 'efficient high FPPM fantasy points per minute production efficient',
        }
        
        # Special handling for SLEEPERS - most important for your use case!
        # Sleepers = undervalued players with upside, typically late rounds
        if 'sleeper' in query_lower or 'sleepers' in query_lower:
            # Define sleeper territory: Rounds 6-12 (post-core starters, pre-waiver)
            sleeper_start = self.league_size * 5   # After round 5
            sleeper_end = self.league_size * 12    # Through round 12
            
            expanded_parts.append('SLEEPER late round deep league value upside breakout emerging')
            expanded_parts.append('undervalued underrated breakout candidate upside potential')
            expanded_parts.append('waiver wire streaming deep league late round target')
            
            # Add strategic rank samples in sleeper territory
            step = max(5, self.league_size // 3)
            for i in range(sleeper_start, min(sleeper_end, 200), step):
                expanded_parts.append(f"Fantasy Rank #{i}")
            
            # Add example sleeper-type players (typically ranks 60-150)
            expanded_parts.append("Amen Thompson Tari Eason Jaime Jaquez Santi Aldama")
            expanded_parts.append("Derrick White Jordan Clarkson Cason Wallace Isaiah Hartenstein")
        else:
            # Apply other quality term expansions
            for quality_term, expansion in quality_expansions.items():
                if quality_term in query_lower:
                    expanded_parts.append(expansion)
                    break
        
        # Expand position-specific queries with better context
        position_expansions = {
            'point guard': 'PG point guard playmaker assists ball handler',
            'pg': 'PG point guard playmaker assists',
            'shooting guard': 'SG shooting guard scorer wing perimeter',
            'sg': 'SG shooting guard scorer',
            'small forward': 'SF small forward wing versatile scorer',
            'sf': 'SF small forward wing',
            'power forward': 'PF power forward big man frontcourt',
            'pf': 'PF power forward frontcourt',
            'center': 'C center big man paint rim protector rebounder',
        }
        
        for pos_term, expansion in position_expansions.items():
            if pos_term in query_lower:
                expanded_parts.append(expansion)
                # If combined with round/pick terms, add relevant player examples
                if 'first round' in query_lower or 'elite' in query_lower or 'best' in query_lower:
                    if pos_term in ['center', 'c']:
                        expanded_parts.append("Jokic Davis Wembanyama Towns Sabonis Embiid")
                    elif pos_term in ['point guard', 'pg']:
                        expanded_parts.append("Shai Doncic Cunningham Harden")
                break
        
        # Join all parts with spaces
        expanded_query = ' '.join(expanded_parts)
        
        if expanded_query != query:
            logger.info(f"🔎 Expanded query: '{query}' → '{expanded_query[:100]}...'")
        
        return expanded_query
    
    def _extract_metadata_filters(self, query: str) -> Dict[str, Any]:
        """
        Extract metadata filters from query for hybrid search.
        Returns filter conditions based on query intent.
        """
        query_lower = query.lower()
        filters = {}
        
        # Special handling for "first overall" type queries
        if 'first overall' in query_lower or 'go first' in query_lower or 'number one' in query_lower:
            filters['rank_range'] = (1, 15)
            logger.info(f"🎯 First overall filter: ranks 1-15")
            return filters  # Return early with this filter
        
        # Check for "#1" pattern specifically
        if '#1' in query_lower or 'pick 1' in query_lower or '1st pick' in query_lower:
            filters['rank_range'] = (1, 15)
            logger.info(f"🎯 Pick #1 filter: ranks 1-15")
            return filters
        
        # Extract pick/rank number for filtering
        pick_patterns = [
            (r'pick\s*#?(\d+)', lambda m: int(m.group(1))),
            (r'(\d+)(?:st|nd|rd|th)\s+pick', lambda m: int(m.group(1))),
            (r'number\s+(\d+)', lambda m: int(m.group(1))),
        ]
        
        for pattern, extractor in pick_patterns:
            match = re.search(pattern, query_lower)
            if match:
                pick_num = extractor(match)
                # SUPER TIGHT filters for specific picks!
                # The metadata filter is our primary tool - vector search is noisy
                if pick_num <= 10:
                    # Top 10 picks: TINY ±3 window
                    filters['rank_range'] = (max(1, pick_num - 3), min(15, pick_num + 3))
                elif pick_num <= 30:
                    # First round: ±3 range (very tight!)
                    filters['rank_range'] = (max(1, pick_num - 3), min(40, pick_num + 3))
                elif pick_num <= 60:
                    # Early-mid rounds: ±5 range
                    filters['rank_range'] = (max(1, pick_num - 5), min(80, pick_num + 5))
                elif pick_num <= 100:
                    # Mid rounds: ±8 range
                    filters['rank_range'] = (max(1, pick_num - 8), min(120, pick_num + 8))
                else:
                    # Late rounds: ±15 range
                    filters['rank_range'] = (max(1, pick_num - 15), min(250, pick_num + 15))
                logger.info(f"🎯 Rank filter for pick #{pick_num}: {filters['rank_range'][0]}-{filters['rank_range'][1]}")
                break
        
        # Extract round-based filters (LEAGUE-AWARE!)
        if 'first round' in query_lower:
            # First round = picks 1 to league_size (e.g., 1-16 in 16-team)
            filters['rank_range'] = (1, self.league_size + 8)  # Small overlap
            logger.info(f"🎯 First round filter: 1-{self.league_size + 8}")
        elif 'second round' in query_lower:
            # Second round = picks league_size+1 to 2*league_size
            filters['rank_range'] = (max(1, self.league_size - 3), self.league_size * 2 + 8)
            logger.info(f"🎯 Second round filter: {filters['rank_range'][0]}-{filters['rank_range'][1]}")
        elif 'third round' in query_lower:
            # Third round = picks 2*league_size+1 to 3*league_size
            filters['rank_range'] = (max(1, self.league_size * 2 - 3), self.league_size * 3 + 8)
            logger.info(f"🎯 Third round filter: {filters['rank_range'][0]}-{filters['rank_range'][1]}")
        elif 'fourth round' in query_lower:
            filters['rank_range'] = (max(1, self.league_size * 3 - 3), self.league_size * 4 + 8)
            logger.info(f"🎯 Fourth round filter: {filters['rank_range'][0]}-{filters['rank_range'][1]}")
        elif 'fifth round' in query_lower:
            filters['rank_range'] = (max(1, self.league_size * 4 - 3), self.league_size * 5 + 8)
            logger.info(f"🎯 Fifth round filter: {filters['rank_range'][0]}-{filters['rank_range'][1]}")
        elif 'mid round' in query_lower or 'middle round' in query_lower:
            # Mid rounds = rounds 4-7
            filters['rank_range'] = (self.league_size * 3, self.league_size * 8)
            logger.info(f"🎯 Mid round filter: {filters['rank_range'][0]}-{filters['rank_range'][1]}")
        elif 'late round' in query_lower or 'late pick' in query_lower:
            # Late rounds = rounds 9+
            filters['rank_range'] = (self.league_size * 8, min(350, self.league_size * 15))
            logger.info(f"🎯 Late round filter: {filters['rank_range'][0]}-{filters['rank_range'][1]}")
        elif 'sleeper' in query_lower or 'sleepers' in query_lower:
            # Sleepers = rounds 6-12 (undervalued late picks with upside)
            filters['rank_range'] = (self.league_size * 5, self.league_size * 12)
            logger.info(f"🎯 Sleeper filter: {filters['rank_range'][0]}-{filters['rank_range'][1]}")
        elif 'elite' in query_lower or 'best' in query_lower or 'top' in query_lower:
            # Elite = first round players
            filters['rank_range'] = (1, self.league_size + 5)
            logger.info(f"🎯 Elite filter: 1-{self.league_size + 5}")
        
        # Extract position filters
        position_map = {
            'point guard': 'PG', 'pg': 'PG',
            'shooting guard': 'SG', 'sg': 'SG',
            'small forward': 'SF', 'sf': 'SF',
            'power forward': 'PF', 'pf': 'PF',
            'center': 'C',
        }
        
        for pos_term, pos_abbr in position_map.items():
            if pos_term in query_lower:
                filters['position'] = pos_abbr
                logger.info(f"📍 Position filter: {pos_abbr}")
                # If we have both position AND rank filters, widen the rank range
                # to ensure we get enough results
                if 'rank_range' in filters:
                    min_rank, max_rank = filters['rank_range']
                    # Expand by 50% when combining constraints
                    expansion = int((max_rank - min_rank) * 0.5)
                    filters['rank_range'] = (max(1, min_rank - expansion), max_rank + expansion)
                    logger.info(f"🎯 Widened rank filter for position combo: {filters['rank_range'][0]}-{filters['rank_range'][1]}")
                break
        
        # Extract efficiency filters (use lower threshold to get more results)
        if 'efficient' in query_lower or 'efficiency' in query_lower:
            filters['min_fppm'] = 0.70  # Lowered from 0.75 to be less restrictive
            logger.info(f"⚡ Efficiency filter: FPPM >= 0.70")
        
        return filters
    
    def _extract_keywords(self, player: Dict[str, Any]) -> str:
        """Extract searchable keywords from player data for hybrid search"""
        keywords = []
        keywords.append(player.get('player_name', '').lower())
        keywords.append(player.get('position', '').lower())
        keywords.append(player.get('team', '').lower())
        
        # Add name variations for better keyword matching
        name = player.get('player_name', '')
        if name:
            # First name, last name
            parts = name.split()
            keywords.extend([p.lower() for p in parts])
        
        # Add stats keywords
        stats_text = player.get('stats_narrative', '').lower()
        keywords.append(stats_text)
        
        return ' '.join(keywords)
    
    def _keyword_score(self, player_keywords: str, query_terms: List[str]) -> float:
        """Calculate keyword matching score (simple BM25-like scoring)"""
        if not player_keywords or not query_terms:
            return 0.0
        
        score = 0.0
        keywords_lower = player_keywords.lower()
        
        for term in query_terms:
            term_lower = term.lower()
            if term_lower in keywords_lower:
                # Exact match gets higher score
                score += 1.0
                # Boost for term frequency (simple TF)
                count = keywords_lower.count(term_lower)
                score += min(count - 1, 2) * 0.5  # Cap bonus at 2 extra occurrences
        
        return score
    
    def search(self, query: str, num_results: int = 5, league_size: int = None) -> List[Dict[str, Any]]:
        """
        HYBRID SEARCH combining dense vector search + keyword matching.
        Implements text+vector search as per DataTalksClub LLM Zoomcamp requirements.
        
        Args:
            query: User's search query
            num_results: Number of results to return (default: 5)
            league_size: Optional override for league size (uses instance default if not provided)
        """
        # Allow per-query league size override
        original_league_size = self.league_size
        if league_size is not None:
            self.league_size = league_size
            logger.info(f"🏀 Using league size override: {league_size} teams")
        
        try:
            logger.info(f"🔍 HYBRID SEARCH (Dense Vector + Keyword Matching): '{query}' (League: {self.league_size} teams)")
            
            # STEP 1: Query Expansion - enrich query with basketball context
            expanded_query = self._expand_query(query)
            
            # STEP 2: Extract Metadata Filters - identify constraints from query
            filters = self._extract_metadata_filters(query)
            
            # STEP 3: Encode query for dense vector search
            query_vector = self._get_embedding_model().encode(expanded_query).tolist()
            
            # STEP 4: Extract query terms for keyword matching
            query_terms = [term.strip().lower() for term in query.split() if len(term.strip()) > 2]
            
            # STEP 5: HYBRID SEARCH - Dense vector search
            vector_results = self.qdrant_client.search(
                collection_name="nba_players",
                query_vector=query_vector,
                limit=200,  # Get many candidates
                with_payload=True
            )
            
            # STEP 6: Re-rank with keyword matching (hybrid approach)
            hybrid_results = []
            for result in vector_results:
                payload = result.payload
                
                # Get vector similarity score
                vector_score = result.score
                
                # Calculate keyword matching score
                keywords = payload.get('search_keywords', '')
                keyword_score = self._keyword_score(keywords, query_terms)
                
                # HYBRID SCORE: Combine vector (70%) + keyword (30%)
                hybrid_score = (0.7 * vector_score) + (0.3 * keyword_score)
                
                hybrid_results.append({
                    'payload': payload,
                    'score': hybrid_score,
                    'vector_score': vector_score,
                    'keyword_score': keyword_score
                })
            
            # Sort by hybrid score
            hybrid_results.sort(key=lambda x: x['score'], reverse=True)
            
            logger.info(f"🎯 Hybrid scoring: Combined {len(hybrid_results)} results (vector + keyword)")
            
            # STEP 7: Apply metadata filters and convert to final format
            results = []
            for result in hybrid_results:
                payload = result['payload']
                overall_rank = (payload.get('fantasy_rank') or 
                              payload.get('overall_rank') or 
                              payload.get('rank') or 999)
                
                # Apply rank range filter if present
                if 'rank_range' in filters:
                    min_rank, max_rank = filters['rank_range']
                    if not (min_rank <= overall_rank <= max_rank):
                        continue
                
                # Apply position filter if present
                if 'position' in filters:
                    player_position = payload.get('position', '')
                    if filters['position'] not in player_position:
                        continue
                
                # Apply efficiency filter if present
                if 'min_fppm' in filters:
                    player_fppm = payload.get('fppm', 0)
                    if player_fppm < filters['min_fppm']:
                        continue
                
                results.append({
                    'score': result['score'],
                    'name': payload.get('player_name', '') or payload.get('name', ''),
                    'team': payload.get('team', ''),
                    'position': payload.get('position', ''),
                    'overall_rank': overall_rank,
                    'bucket_range': payload.get('bucket_range', ''),
                    'stats': payload.get('stats', {}),
                    'fantasy_points': payload.get('fantasy_points', 0),
                    'fppm': payload.get('fppm', 0),
                    'games': payload.get('games_played', 0),
                    'minutes': payload.get('minutes_per_game', 0),
                    'expert_analysis': payload.get('expert_analysis', ''),
                    'elite_ranking': payload.get('elite_ranking', ''),
                    'injury_status': payload.get('injury_status', 'Unknown'),
                    'text': payload.get('stats_narrative', '')
                })
                
                # Stop once we have enough results
                if len(results) >= 100:
                    break
            
            logger.info(f"📊 Hybrid search: {len(hybrid_results)} candidates → {len(results)} after filtering")
            
            # Progressive fallback strategy:
            # 1. If < 5 results and rank filter exists: Try widening rank filter by 100%
            # 2. If still < 5: Fall back to unfiltered
            if len(results) < 5 and filters and 'rank_range' in filters:
                original_filter = filters['rank_range']
                min_rank, max_rank = original_filter
                expansion = max(5, int((max_rank - min_rank)))  # At least ±5 expansion
                filters['rank_range'] = (max(1, min_rank - expansion), min(250, max_rank + expansion))
                
                logger.warning(f"⚠️ Too few results ({len(results)}), widening rank filter from {original_filter} to {filters['rank_range']}")
                
                # Retry with wider filter
                results = []
                for result in hybrid_results[:200]:  # Get more candidates
                    payload = result['payload']
                    overall_rank = (payload.get('fantasy_rank') or 
                                  payload.get('overall_rank') or 
                                  payload.get('rank') or 999)
                    
                    # Apply widened rank range filter
                    if 'rank_range' in filters:
                        min_rank, max_rank = filters['rank_range']
                        if not (min_rank <= overall_rank <= max_rank):
                            continue
                    
                    # Still apply other filters (position, efficiency)
                    if 'position' in filters:
                        player_position = payload.get('position', '')
                        if filters['position'] not in player_position:
                            continue
                    
                    if 'min_fppm' in filters:
                        player_fppm = payload.get('fppm', 0)
                        if player_fppm < filters['min_fppm']:
                            continue
                    
                    results.append({
                        'score': result['score'],
                        'name': payload.get('player_name', '') or payload.get('name', ''),
                        'team': payload.get('team', ''),
                        'position': payload.get('position', ''),
                        'overall_rank': overall_rank,
                        'bucket_range': payload.get('bucket_range', ''),
                        'stats': payload.get('stats', {}),
                        'fantasy_points': payload.get('fantasy_points', 0),
                        'fppm': payload.get('fppm', 0),
                        'games': payload.get('games_played', 0),
                        'minutes': payload.get('minutes_per_game', 0),
                        'expert_analysis': payload.get('expert_analysis', ''),
                        'elite_ranking': payload.get('elite_ranking', ''),
                        'injury_status': payload.get('injury_status', 'Unknown'),
                        'text': payload.get('stats_narrative', '')
                    })
                    
                    if len(results) >= 100:
                        break
                
                logger.info(f"📊 After widening: {len(results)} results")
            
            # If STILL < 5 results, fall back to completely unfiltered
            if len(results) < 5 and filters:
                logger.warning(f"⚠️ Still too few results ({len(results)}), falling back to unfiltered search")
                # Retry with just vector search (no filters)
                results = []
                for result in hybrid_results[:100]:
                    payload = result['payload']
                    overall_rank = (payload.get('fantasy_rank') or 
                                  payload.get('overall_rank') or 
                                  payload.get('rank') or 999)
                    
                    results.append({
                        'score': result['score'],
                        'name': payload.get('player_name', '') or payload.get('name', ''),
                        'team': payload.get('team', ''),
                        'position': payload.get('position', ''),
                        'overall_rank': overall_rank,
                        'bucket_range': payload.get('bucket_range', ''),
                        'stats': payload.get('stats', {}),
                        'fantasy_points': payload.get('fantasy_points', 0),
                        'fppm': payload.get('fppm', 0),
                        'games': payload.get('games_played', 0),
                        'minutes': payload.get('minutes_per_game', 0),
                        'expert_analysis': payload.get('expert_analysis', ''),
                        'elite_ranking': payload.get('elite_ranking', ''),
                        'injury_status': payload.get('injury_status', 'Unknown'),
                        'text': payload.get('stats_narrative', '')
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            return []
        finally:
            # Restore original league size if it was overridden
            if league_size is not None:
                self.league_size = original_league_size

    def _normalize_name(self, name: str) -> str:
        """
        Normalize player names to handle special characters
        """
        # Remove accents and diacritics
        normalized = unicodedata.normalize('NFD', name)
        ascii_name = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')
        return ascii_name.lower().strip()

    def _fuzzy_name_search(self, query_name: str) -> List[Dict[str, Any]]:
        """
        Perform fuzzy search for player names to handle variations
        """
        try:
            # First try exact search
            results = self.search(f'name:{query_name}', num_results=10)
            
            # If no exact results, try normalized search
            if not results:
                normalized_query = self._normalize_name(query_name)
                # Search using vector similarity on the query
                results = self.search(query_name, num_results=10)
                
                # Filter results by name similarity
                filtered_results = []
                for result in results:
                    player_name = result.get('name', '')
                    normalized_player = self._normalize_name(player_name)
                    
                    # Check if names are similar (contains or partial match)
                    if (normalized_query in normalized_player or 
                        normalized_player in normalized_query or
                        any(word in normalized_player for word in normalized_query.split())):
                        filtered_results.append(result)
                
                return filtered_results[:5]
            
            return results
            
        except Exception as e:
            logger.error(f"Fuzzy name search failed: {e}")
            return []

    def build_prompt(self, query: str, search_results: List[Dict[str, Any]]) -> str:
        """
        Build a comprehensive prompt for the LLM with basketball knowledge
        """
        # Build context from search results - show MORE players for better LLM reasoning
        context = ""
        for i, result in enumerate(search_results[:30], 1):  # Show top 30 for diverse rank coverage
            # Extract data from either metadata structure or direct fields
            metadata = result.get('metadata', result)
            
            # Extract key metrics with proper defaults  
            overall_rank = (metadata.get('fantasy_rank') or 
                          metadata.get('rank') or 
                          metadata.get('Rank') or 
                          metadata.get('overall_rank') or 999)
            fppm = metadata.get('fppm', 0)
            fantasy_points = metadata.get('fp', metadata.get('fantasy_points', 0))
            minutes_per_game = metadata.get('minutes', metadata.get('min', 30.0))
            games_played = metadata.get('games', 0)
            injury_status = metadata.get('injury_status', 'Unknown')
            
            # Extract player info
            name = metadata.get('name', metadata.get('Name', 'Unknown'))
            position = metadata.get('position', metadata.get('Position', 'Unknown'))
            team = metadata.get('team', metadata.get('Team', 'Unknown'))
            
            # Calculate FPPG for display
            fppg = fantasy_points if fantasy_points > 0 else fppm * minutes_per_game
            
            context += f"""
Player {i}: {name} ({position}, {team}) - Rank #{overall_rank}
• Fantasy Production: {fppg:.1f} FPPG, {fppm:.3f} FPPM
• Availability: {games_played} games, {minutes_per_game:.1f} min/game
• Injury Status: {injury_status}
• Expert Analysis: {metadata.get('expert_analysis', '')[:200]}{'...' if len(metadata.get('expert_analysis', '')) > 200 else ''}

"""

        # Natural, conversational prompt for fantasy basketball advice
        prompt_template = """
You're a fantasy basketball expert helping someone with their draft. Be conversational and helpful!

User asked: {query}

Here are the {num_players} most relevant players for this question:

{context}

Important context about fantasy rankings:
- Rank #1 is the BEST player (lower rank = better)
- For draft advice: recommend players whose rank matches the pick (±5)
  Example: Pick #1 → suggest players ranked #1-6
  Example: Pick #25 → suggest players ranked #20-30

Your response should:
1. Answer naturally and directly
2. Use ranks to explain value ("Jokić is ranked #1, making him perfect for the top pick")
3. Include key stats (FPPG, FPPM) when relevant
4. Focus on the players shown above

Keep it conversational - imagine you're texting advice to a friend who's drafting right now!

Your advice:
        """.strip()

        num_players = len(search_results[:30])
        return prompt_template.format(query=query, context=context, num_players=num_players)

    def llm(self, prompt: str) -> str:
        """
        Generate response using Groq LLM
        """
        if not self.groq_client:
            return """
### 🤖 AI Analysis Not Available

**To unlock AI-powered fantasy basketball advice:**

#### 🔑 Get Your Free Groq API Key:
1. Visit **[console.groq.com](https://console.groq.com/)**
2. Create a free account
3. Generate an API key
4. Enter it in the sidebar ➡️

#### 📊 Available Now (No API Key Required):
- ✅ **Player Statistics** - Browse comprehensive NBA stats
- ✅ **Smart Search** - Find players by position, team, or performance
- ✅ **Fantasy Rankings** - View top performers by position
- ✅ **Visual Charts** - Compare players with interactive graphs
- ✅ **Expert Analysis** - Read professional scouting reports

#### 🚀 With API Key:
- 🧠 **Personalized Advice** - Custom draft strategies
- 📈 **Trade Analysis** - AI-powered trade recommendations  
- 🎯 **Matchup Insights** - Weekly lineup optimization
- 💡 **Sleeper Picks** - Hidden gem recommendations

**The player data below shows relevant matches for your search!** 👇
            """.strip()
        
        try:
            response = self.groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1024,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return f"Error generating response: {str(e)}"

    def rag(self, query: str, num_results: int = 5) -> tuple[str, List[Dict[str, Any]]]:
        """
        Complete RAG pipeline: search + generate
        """
        try:
            # Adjust num_results based on query type
            query_lower = query.lower()
            if any(term in query_lower for term in ['draft', 'pick', '14th', '15th', 'sleeper', 'value']):
                # For draft questions, return more players to analyze
                num_results = max(num_results, 15)
            
            # Search for relevant documents
            search_results = self.search(query, num_results)
            
            if not search_results:
                return "No relevant player data found for your query. Please try a different search.", []
            
            # Build prompt and generate response
            prompt = self.build_prompt(query, search_results)
            answer = self.llm(prompt)
            
            return answer, search_results
            
        except Exception as e:
            logger.error(f"RAG pipeline failed: {e}")
            return f"Error processing your query: {str(e)}", []

    def get_player_by_name(self, player_name: str) -> Dict[str, Any]:
        """
        Get specific player information by name with fuzzy matching
        """
        try:
            # Use fuzzy search to handle special characters and variations
            search_results = self._fuzzy_name_search(player_name)
            
            if search_results:
                # Return the best match
                result = search_results[0]
                return {
                    'name': result.get('name', ''),
                    'team': result.get('team', ''),
                    'position': result.get('position', ''),
                    'stats': result.get('stats', {}),
                    'fantasy_points': result.get('fantasy_points', 0),
                    'expert_analysis': result.get('expert_analysis', ''),
                    'fantasy_value': self._calculate_fantasy_value(result.get('stats', {}), result.get('fantasy_points', 0))
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"Failed to get player {player_name}: {e}")
            return {}

    def _calculate_fantasy_value(self, stats: Dict[str, Any], fantasy_points: float) -> Dict[str, float]:
        """
        Calculate comprehensive fantasy value based on FPPM and availability
        """
        try:
            games_played = stats.get('games', 0)  # Fixed: use 'games' not 'games_played'
            games_started = stats.get('games_started', 0)
            minutes_per_game = stats.get('minutes_per_game', 0)
            
            # Calculate Fantasy Points Per Minute (FPPM)
            fppm = fantasy_points / minutes_per_game if minutes_per_game > 0 else 0
            
            # Availability score (0-1): considers games played and minutes
            # Heavily weight players who start games and play significant minutes
            availability_score = 0
            if games_played > 0:
                # Base availability from games played (max 82 games)
                games_factor = min(games_played / 70, 1.0)  # 70+ games = full score
                
                # Starting factor (games started / games played)
                starting_factor = games_started / games_played if games_played > 0 else 0
                
                # Minutes factor (20+ minutes = good, 30+ = excellent)
                minutes_factor = min(minutes_per_game / 30, 1.0) if minutes_per_game >= 20 else minutes_per_game / 20 * 0.7
                
                # Combine factors with weights
                availability_score = (games_factor * 0.4 + starting_factor * 0.3 + minutes_factor * 0.3)
            
            # Elite Fantasy Value = FPPM × Availability Score (updated formula)
            elite_fantasy_value = fppm * availability_score
            
            return {
                'fppm': round(fppm, 3),
                'availability_score': round(availability_score, 3),
                'elite_fantasy_value': round(elite_fantasy_value, 3),
                'games_factor': round(min(games_played / 70, 1.0), 3),
                'starting_factor': round(games_started / games_played if games_played > 0 else 0, 3),
                'minutes_factor': round(min(minutes_per_game / 30, 1.0) if minutes_per_game >= 20 else minutes_per_game / 20 * 0.7, 3)
            }
            
        except Exception as e:
            logger.error(f"Fantasy value calculation failed: {e}")
            return {
                'fppm': 0,
                'availability_score': 0,
                'elite_fantasy_value': 0,
                'games_factor': 0,
                'starting_factor': 0,
                'minutes_factor': 0
            }
    
    # Adapter methods for app.py compatibility
    def search_players(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """
        Adapter method to maintain compatibility with app.py
        Maps to the vector search method
        """
        return self.search(query, num_results)
    
    def get_response(self, query: str) -> str:
        """
        Adapter method to maintain compatibility with app.py
        Maps to the RAG method and returns just the response text
        """
        try:
            response, _ = self.rag(query)
            return response
        except Exception as e:
            logger.error(f"Error getting response: {e}")
            return f"Sorry, I encountered an error processing your request: {e}"
    
    @property 
    def sample_data(self) -> List[Dict[str, Any]]:
        """
        Adapter property for compatibility with analytics
        Retrieves sample data from vector database for analytics display
        """
        try:
            # Get all points from the collection to provide data for analytics
            collection_info = self.qdrant_client.get_collection("nba_players")
            if collection_info.points_count > 0:
                # Retrieve a sample of players for analytics (limit to avoid performance issues)
                search_result = self.qdrant_client.scroll(
                    collection_name="nba_players",
                    limit=100,  # Get top 100 players for analytics
                    with_payload=True,
                    with_vectors=False
                )
                
                # Extract player data from Qdrant format
                players = []
                for point in search_result[0]:  # search_result is (points, next_page_offset)
                    if point.payload:
                        # Add necessary fields for analytics compatibility
                        player_data = point.payload.copy()
                        
                        # Ensure required fields exist for analytics
                        if 'name' not in player_data and 'player_name' in player_data:
                            player_data['name'] = player_data['player_name']
                        
                        # Map vector DB fields to expected analytics fields
                        if 'fantasy_points_per_game' in player_data:
                            player_data['fantasy_points'] = player_data['fantasy_points_per_game']
                        
                        players.append(player_data)
                
                logger.info(f"Retrieved {len(players)} players from vector database for analytics")
                return players
            else:
                logger.warning("No players found in vector database")
                return []
                
        except Exception as e:
            logger.error(f"Error retrieving sample data from vector database: {e}")
            # No fallbacks - return empty list if vector DB is unavailable
            return []