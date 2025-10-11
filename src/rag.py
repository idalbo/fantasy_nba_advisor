import os
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
        self.qdrant_host = os.getenv('QDRANT_HOST', 'localhost')
        self.qdrant_port = int(os.getenv('QDRANT_PORT', 6333))
        
        # Initialize Qdrant client
        self.qdrant_client = QdrantClient(host=self.qdrant_host, port=self.qdrant_port)
        
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
You are a FANTASY BASKETBALL EXPERT. You have access to NBA player data with FANTASY RANKINGS and must make intelligent recommendations.

QUERY: {query}

PLAYER DATABASE:
{context}

🏀 UNDERSTANDING THE RANKING SYSTEM:

**WHAT "Rank #X" MEANS:**
• Rank #1 = THE BEST fantasy player (Nikola Jokić) - produces the most fantasy points
• Rank #2 = SECOND BEST fantasy player (Giannis Antetokounmpo) 
• Rank #3 = THIRD BEST fantasy player (Shai Gilgeous-Alexander)
• Rank #19 = The 19th best fantasy player in the league
• Rank #50 = The 50th best fantasy player in the league
• Lower numbers = BETTER players, Higher numbers = WORSE players

**DRAFT LOGIC - THIS IS CRITICAL:**
• In fantasy drafts, the BEST players get picked FIRST
• Pick #1 gets the #1 ranked player (Jokić), Pick #2 gets #2 ranked player (Giannis), etc.
• If someone asks for "position #1" → recommend Rank #1, #2, #3 players (the absolute best)
• If someone asks for "position #19" → recommend players ranked around #19-25 (players available at that spot)
• If someone asks for "position #50" → recommend players ranked around #50-60 

**PLAYER AVAILABILITY BY DRAFT POSITION:**
• Position #1-5: Only the TOP ranked players (#1-8) are appropriate 
• Position #10-20: Mid-tier players (ranks #10-30) are appropriate
• Position #30-50: Later picks (ranks #30-70) are appropriate
• Position #100+: Deep sleepers (ranks #80+) are appropriate

🎯 **HOW TO SELECT PLAYERS FROM THE DATABASE:**

**Step 1: UNDERSTAND THE QUERY**
- Is this asking for a specific draft position? ("position #1", "pick #19")
- Is this asking for the best players overall? ("top players", "best picks")
- Is this asking about a specific player? ("tell me about LeBron")

**Step 2: LOOK AT THE RANKINGS IN THE DATA**
- Scan through ALL the players provided in the database above
- Note each player's "Rank #X" number
- Remember: LOWER rank numbers = BETTER players

**Step 3: MAKE INTELLIGENT SELECTIONS**

FOR DRAFT POSITION QUERIES:
- "position #1" → Find and recommend players with Rank #1, #2, #3 from the database
- "position #19" → Find and recommend players with Rank #17-25 from the database  
- "position #50" → Find and recommend players with Rank #45-60 from the database

FOR GENERAL "BEST PLAYERS" QUERIES:
- Look for the LOWEST rank numbers in the database (Rank #1, #2, #3, etc.)
- These are the most valuable fantasy players

FOR PLAYER COMPARISON QUERIES:
- Compare the rank numbers of the players mentioned
- Lower rank = better fantasy player

**Step 4: EXPLAIN YOUR REASONING**
- Always mention the player's rank: "Jokić is ranked #1, making him perfect for the first pick"
- Explain why the rank matches the draft position: "Ranked #19, he's ideal for your 19th pick"
- Warn about availability: "He's ranked #5, so he'll be gone by pick #19"

🚫 **CRITICAL MISTAKES TO AVOID:**
- NEVER recommend Jokić (#1) for pick #50 - he'll be taken in the first few picks!
- NEVER recommend a player ranked #5 for pick #30 - he'll be gone!
- NEVER ignore the ranking system - it tells you player value!

📋 **RESPONSE FORMAT:**
1. Understand what draft position or player quality they're asking about
2. Look through the provided database for players with appropriate ranks
3. Recommend 2-3 players whose ranks match the query
4. Explain each player's rank and why they fit the request
5. Be conversational and helpful like a fantasy expert friend

ANSWER STYLE: Knowledgeable, specific about rankings, and helpful like an experienced fantasy player.

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