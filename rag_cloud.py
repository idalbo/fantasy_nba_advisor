"""
Cloud-compatible RAG system for Fantasy NBA Advisor
"""
import os
import json
import logging
from typing import List, Dict, Any, Optional
from groq import Groq

logger = logging.getLogger(__name__)

class FantasyNBARag:
    def __init__(self, groq_api_key: str = None, cloud_mode: bool = False):
        self.cloud_mode = cloud_mode
        
        # Initialize Groq client - prioritize passed API key over environment
        self.groq_client = None
        api_key_to_use = None
        
        if groq_api_key:
            # User provided API key takes priority
            api_key_to_use = groq_api_key
        else:
            # Fall back to environment key
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
        
        # Load sample data for cloud mode
        if cloud_mode:
            self.sample_data = self._load_sample_data()
    
    def _load_sample_data(self) -> List[Dict[str, Any]]:
        """Load NBA player data for cloud demo"""
        try:
            # Try to load full dataset first
            if os.path.exists('nba_players_full.json'):
                with open('nba_players_full.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.info(f"Loaded {len(data)} NBA players from full dataset")
                    return data
        except Exception as e:
            logger.warning(f"Could not load full dataset: {e}")
        
        # Fallback to sample data
        logger.info("Using sample data fallback")
        return [
            {
                "player_name": "Nikola Jokić",
                "name": "Nikola Jokić",  # For chart compatibility
                "position": "C",
                "team": "DEN",
                "fppm": 1.286,
                "fantasy_points": 47.2,  # For chart compatibility
                "fantasy_rank": 1,
                "stats_narrative": "Elite center averaging 47.2 fantasy points per game with exceptional efficiency. Triple-double threat every night.",
                "expert_analysis": "The best fantasy pick in basketball. Consistent production across all categories.",
                "elite_ranking": "Rank 1 overall. Must-draft player in any format."
            },
            {
                "player_name": "Giannis Antetokounmpo", 
                "name": "Giannis Antetokounmpo",
                "position": "PF",
                "team": "MIL",
                "fppm": 1.221,
                "fantasy_points": 41.75,
                "fantasy_rank": 2,
                "stats_narrative": "Dominant two-way player with 41.75 fantasy points per game. Elite in rebounds, assists, blocks.",
                "expert_analysis": "Perennial MVP candidate with consistent fantasy production.",
                "elite_ranking": "Rank 2 overall. Safe first round pick."
            },
            {
                "player_name": "Shai Gilgeous-Alexander",
                "position": "PG", 
                "team": "OKC",
                "fppm": 1.129,
                "fantasy_rank": 3,
                "stats_narrative": "Elite guard with 38.6 fantasy points per game. Excellent scorer and playmaker.",
                "expert_analysis": "Young superstar with room to grow. Elite fantasy production.",
                "elite_ranking": "Rank 3 overall. Top guard option."
            },
            {
                "player_name": "Anthony Davis",
                "position": "PF/C",
                "team": "LAL", 
                "fppm": 1.069,
                "fantasy_rank": 5,
                "stats_narrative": "Versatile big man with 35.8 fantasy points per game when healthy. Elite defensive stats.",
                "expert_analysis": "Injury risk but elite upside. Monitor health closely.",
                "elite_ranking": "Rank 5 overall. High ceiling, injury concern."
            },
            {
                "player_name": "Luka Dončić",
                "position": "PG",
                "team": "DAL",
                "fppm": 1.020, 
                "fantasy_rank": 7,
                "stats_narrative": "Triple-double machine with 36.1 fantasy points per game. Elite playmaker and scorer.",
                "expert_analysis": "Consistent fantasy production with high floor and ceiling.",
                "elite_ranking": "Rank 7 overall. Elite point guard option."
            },
            {
                "player_name": "Victor Wembanyama",
                "position": "C",
                "team": "SAS",
                "fppm": 1.068,
                "fantasy_rank": 6,
                "stats_narrative": "Rookie sensation with 35.45 fantasy points per game. Unique combination of size and skill.",
                "expert_analysis": "Generational talent with immediate fantasy impact.",
                "elite_ranking": "Rank 6 overall. Future superstar."
            },
            {
                "player_name": "Jayson Tatum",
                "position": "SF/PF", 
                "team": "BOS",
                "fppm": 0.98,
                "fantasy_rank": 8,
                "stats_narrative": "Versatile scorer with 33.2 fantasy points per game. Consistent production across categories.",
                "expert_analysis": "Reliable fantasy option with championship experience.",
                "elite_ranking": "Rank 8 overall. Solid first round pick."
            },
            {
                "player_name": "LeBron James",
                "position": "SF/PF",
                "team": "LAL",
                "fppm": 0.95,
                "fantasy_rank": 10,
                "stats_narrative": "Veteran superstar still producing 32.8 fantasy points per game at age 39.",
                "expert_analysis": "Age concerns but still elite production. Monitor workload management.",
                "elite_ranking": "Rank 10 overall. High floor despite age."
            }
        ]
    
    def get_response(self, query: str) -> str:
        """Get AI response for fantasy basketball query"""
        if not self.groq_client:
            return "❌ **Groq API key required**: Please enter your API key in the sidebar to enable AI features."
        
        try:
            # Get relevant players for context (more for draft position queries)
            relevant_players = self.search_players(query, 15)
            
            # Create context from actual player data
            player_context = ""
            if relevant_players:
                player_context = "\n\nCurrent NBA Player Data (from our database of 450 players):\n"
                for i, player in enumerate(relevant_players[:12], 1):
                    player_context += f"{i}. {player.get('name', 'Unknown')} ({player.get('position', '?')}, {player.get('team', '?')}) - Rank #{player.get('fantasy_rank', '?')}, FPPM: {player.get('fppm', 0):.3f}, FP/G: {player.get('fantasy_points', 0):.1f}\n"
            
            # Enhanced prompt for fantasy basketball with real data
            system_prompt = f"""You are an expert fantasy basketball advisor with access to current NBA player rankings and statistics from a comprehensive database of 450 NBA players.

CRITICAL INSTRUCTIONS:
- ONLY use the actual player data provided in the context below
- NEVER make up rankings, stats, or player information
- Always reference specific FPPM values and fantasy ranks from the data
- When asked about draft positions (e.g., "pick 78"), recommend players ranked around that position
- Provide multiple options with their exact ranks, FPPM values, and reasoning{player_context}

Key Guidelines:
- Focus on Fantasy Points Per Minute (FPPM) as the primary efficiency metric
- Consider positional scarcity and team context
- Provide specific recommendations with actual data from the context
- Reference exact rankings and stats from the database
- For draft picks, suggest players ranked within 5 spots of the requested position
- Compare multiple players and explain their strengths/weaknesses
- Be accurate with all numerical information"""

            response = self.groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                temperature=0.1,  # Lower temperature for more factual responses
                max_tokens=1000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error getting Groq response: {e}")
            return f"❌ **Error**: Unable to get AI response. {str(e)}"
    
    def search_players(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """Search for players - enhanced for cloud mode with draft position handling"""
        if not self.cloud_mode:
            return []
            
        query_lower = query.lower()
        results = []
        
        # Check if query is asking for a specific draft position/pick number
        import re
        pick_match = re.search(r'(?:pick|number|position)\s*(\d+)', query_lower)
        if pick_match:
            pick_number = int(pick_match.group(1))
            # Find players ranked around that pick (±3 positions)
            target_players = [p for p in self.sample_data 
                            if abs(p.get('fantasy_rank', 999) - pick_number) <= 5]
            if target_players:
                # Sort by how close they are to the target pick
                target_players.sort(key=lambda x: abs(x.get('fantasy_rank', 999) - pick_number))
                return target_players[:num_results]
        
        # Regular search for player names, positions, teams
        for player in self.sample_data:
            score = 0
            player_text = f"{player['player_name']} {player['position']} {player['team']} {player['stats_narrative']}".lower()
            
            # Simple scoring based on keyword matches
            keywords = query_lower.split()
            for keyword in keywords:
                if keyword in player_text:
                    score += 1
            
            if score > 0:
                player_copy = player.copy()
                player_copy['score'] = score
                results.append(player_copy)
        
        # Sort by score and rank
        results.sort(key=lambda x: (-x['score'], x['fantasy_rank']))
        return results[:num_results]
    
    def get_elite_players(self, num_results: int = 5) -> List[Dict[str, Any]]:
        """Get top elite players"""
        if not self.cloud_mode:
            return []
            
        # Return top players by rank
        sorted_players = sorted(self.sample_data, key=lambda x: x['fantasy_rank'])
        return sorted_players[:num_results]
    
    def rag(self, query: str, num_results: int = 5) -> tuple[str, List[Dict[str, Any]]]:
        """
        RAG method to match the interface expected by the main app
        Returns a tuple of (response, search_results)
        """
        if not self.cloud_mode:
            return "Cloud mode not enabled", []
        
        # Get response and search results
        response = self.get_response(query)
        search_results = self.search_players(query, num_results)
        
        return response, search_results