import os
import json
import unicodedata
import re
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from groq import Groq
import logging
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class FantasyNBARag:
    def __init__(self, groq_api_key: str = None):
        # Initialize Qdrant client with in-memory mode for cloud deployment
        self._init_qdrant_client()
        
        # Initialize embedding model
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
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
    
    def _load_data_to_qdrant(self):
        """Load NBA player data into Qdrant collection"""
        try:
            # Check if collection already exists
            collections = self.qdrant_client.get_collections().collections
            if any(collection.name == "nba_players" for collection in collections):
                logger.info("✅ NBA players collection already exists")
                return
            
            # Create collection
            from qdrant_client.models import Distance, VectorParams
            self.qdrant_client.create_collection(
                collection_name="nba_players",
                vectors_config=VectorParams(size=384, distance=Distance.COSINE),
            )
            logger.info("🏗️ Created NBA players collection")
            
            # Load player data from JSON file
            player_data = self._load_player_data()
            if not player_data:
                logger.error("No player data available to load")
                return
            
            # Create embeddings and upload to Qdrant
            from qdrant_client.models import PointStruct
            points = []
            
            for i, player in enumerate(player_data):
                # Create searchable text
                text = f"{player.get('player_name', '')} {player.get('position', '')} {player.get('team', '')} "
                text += f"{player.get('expert_analysis', '')} {player.get('stats_narrative', '')}"
                
                # Create embedding
                embedding = self.embedding_model.encode(text).tolist()
                
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
    def search(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """
        Pure vector search - no filtering, let LLM handle all logic
        """
        try:
            logger.info(f"🔍 Vector search query: '{query}'")
            
            # Simple vector search without any filtering
            query_vector = self.embedding_model.encode(query).tolist()
            
            # Perform vector search - get more results to give LLM broader context
            search_results = self.qdrant_client.search(
                collection_name="nba_players",
                query_vector=query_vector,
                limit=max(num_results * 3, 30),  # Get 3x more results for LLM context
                with_payload=True
            )
            
            # Convert to standard format
            results = []
            for result in search_results:
                payload = result.payload
                overall_rank = (payload.get('overall_rank') or 
                              payload.get('fantasy_rank') or 
                              payload.get('rank') or 999)
                
                results.append({
                    'score': result.score,
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
            
            logger.info(f"📊 Found {len(results)} players via vector search")
            return results
            
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []

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
        # Build context from search results
        context = ""
        for i, result in enumerate(search_results[:15], 1):  # Limit to top 15 for context
            overall_rank = result.get('overall_rank', 999)
            fppm = result.get('fppm', 0)
            fantasy_points = result.get('fantasy_points', 0)
            minutes_per_game = result.get('minutes', 0)
            games_played = result.get('games', 0)
            injury_status = result.get('injury_status', 'Unknown')
            
            # Calculate FPPG for display
            fppg = fantasy_points if fantasy_points > 0 else fppm * minutes_per_game
            
            context += f"""
Player {i}: {result['name']} ({result['position']}, {result['team']}) - Rank #{overall_rank}
• Fantasy Production: {fppg:.1f} FPPG, {fppm:.3f} FPPM
• Availability: {games_played} games, {minutes_per_game:.1f} min/game
• Injury Status: {injury_status}
• Expert Analysis: {result.get('expert_analysis', '')[:200]}{'...' if len(result.get('expert_analysis', '')) > 200 else ''}

"""

        # Enhanced prompt with comprehensive basketball knowledge
        prompt_template = """
You are a FANTASY BASKETBALL EXPERT. You must follow the ranking system EXACTLY.

QUERY: {query}

PLAYER DATABASE:
{context}

🚨 CRITICAL RANKING RULES - FOLLOW EXACTLY:

WHAT RANKINGS MEAN:
• Rank #1 = BEST fantasy player (Nikola Jokić) 
• Rank #2 = SECOND BEST fantasy player (Giannis)
• Rank #3 = THIRD BEST fantasy player (Shai)
• Rank #78 = 78th best fantasy player
• LOWER number = BETTER player (Rank #1 > Rank #78)

DRAFT POSITION LOGIC - NEVER VIOLATE THIS:
• Pick #1 → ONLY recommend players ranked #1, #2, or #3
• Pick #78 → ONLY recommend players ranked #75-85 (around rank #78)
• Pick #150 → ONLY recommend players ranked #145-155 (around rank #150)

🚫 FORBIDDEN MISTAKES:
• NEVER recommend Anthony Davis (Rank #4) for pick #1 - Jokić (Rank #1) is better!
• NEVER recommend Rank #25 players for pick #78 - they'll be taken by pick #25!
• NEVER recommend players with LOWER rank numbers for HIGHER draft positions!

📋 EXACT INSTRUCTIONS:

1. READ THE QUERY: What draft position are they asking about?

2. SCAN THE DATABASE: Look through ALL players provided above and note their "Rank #X"

3. MATHEMATICAL RULE: 
   - For pick #N, recommend players ranked #(N-5) to #(N+10)
   - Pick #1 → ranks #1-8
   - Pick #78 → ranks #73-88
   - Pick #150 → ranks #145-160

4. SELECT CORRECTLY:
   - Find players in the database whose rank numbers match the draft position
   - If asking for pick #78, ONLY mention players ranked around #78
   - If asking for pick #1, ONLY mention players ranked #1, #2, #3
   - If the right players aren't in the database, say "I need to see players ranked #X-Y for this pick"

5. DOUBLE-CHECK: Before recommending, verify the player's rank matches the pick number

EXAMPLES TO FOLLOW:
• Query: "number 1 pick" → Answer: "Jokić (Rank #1) is your pick - he's the #1 ranked player"
• Query: "pick #78" → Answer: "Look for players ranked around #78-85 in the database"
• Query: "pick #150" → Answer: "Look for players ranked around #150 in the database"

RESPONSE FORMAT:
1. State the draft position requested
2. State what rank range you're looking for (pick #N needs ranks #N-5 to #N+10)
3. Scan the provided database for players in that rank range
4. If correct players found: Recommend ONLY players whose ranks match
5. If correct players NOT found: Say "I need players ranked #X-Y for pick #Z, but the search results show different players"
6. Explain: "Player X is ranked #Y, perfect for pick #Z"
7. MATH CHECK: Verify rank number ≈ pick number before recommending

NEVER recommend players ranked significantly higher or lower than the draft position!

ANSWER:
        """.strip()

        return prompt_template.format(query=query, context=context)

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