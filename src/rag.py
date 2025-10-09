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
        
        # Initialize Groq client - prioritize passed API key over environment
        self.groq_client = None
        api_key_to_use = None
        
        if groq_api_key:
            # User provided API key takes priority
            api_key_to_use = groq_api_key
        else:
            # Fall back to environment key only if no user key provided
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

    def search_by_draft_position(self, draft_position: int, num_results: int = 4) -> List[Dict[str, Any]]:
        """
        Search for players appropriate for a specific draft position based on overall rank buckets
        """
        try:
            # Special handling for top picks queries
            if draft_position == 1 and num_results > 4:
                # This is likely a "top 5" or "top 10" query
                target_rank_start = 1
                target_rank_end = num_results + 2  # Get a few extra for safety
            else:
                # Regular draft position query - look for players around the draft position
                # For pick 10, look for players ranked around 8-20 (with some flexibility)
                target_rank_start = max(1, draft_position - 2)  # Start a bit before the pick
                target_rank_end = draft_position + 15  # Allow for value picks and depth
            
            # Get all players and filter by rank
            all_results = self.qdrant_client.scroll(
                collection_name="nba_players",
                limit=450,
                with_payload=True
            )[0]
            
            # Filter players in the target rank range
            target_players = []
            for result in all_results:
                payload = result.payload
                overall_rank = payload.get('overall_rank', 999)
                
                if isinstance(overall_rank, (int, float)) and target_rank_start <= overall_rank <= target_rank_end:
                    target_players.append({
                        'score': 1.0,  # All equally relevant for draft position
                        'name': payload.get('player_name', ''),
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
                        'text': payload.get('stats_narrative', '')
                    })
            
            # Calculate elite fantasy value for each player (same logic as in search method)
            for result in target_players:
                # Get data from result
                minutes_per_game = result.get('minutes', 0)
                fantasy_points = result.get('fantasy_points', 0)
                games_played = result.get('games', 0)
                
                # Also get from stats if available (backup)
                stats = result.get('stats', {})
                if minutes_per_game == 0:
                    minutes_per_game = stats.get('minutes_per_game', 0)
                if games_played == 0:
                    games_played = stats.get('games_played', 0)
                    
                games_started = stats.get('games_started', 0)
                
                # Calculate FPPM (Fantasy Points Per Minute)
                fppm = fantasy_points / minutes_per_game if minutes_per_game > 0 else 0
                result['fppm'] = fppm
                
                # Calculate elite fantasy value = FPPM × Availability Score
                availability_score = 0
                if games_played > 0:
                    games_factor = min(games_played / 65, 1.0)  # Adjust for realistic games
                    starting_factor = games_started / games_played if games_played > 0 else 0
                    minutes_factor = min(minutes_per_game / 32, 1.0) if minutes_per_game >= 15 else minutes_per_game / 15 * 0.6
                    availability_score = (games_factor * 0.5 + starting_factor * 0.25 + minutes_factor * 0.25)
                
                result['elite_fantasy_value'] = fppm * availability_score
            
            # Sort by overall rank and return top matches
            target_players.sort(key=lambda x: x['overall_rank'])
            return target_players[:num_results]
            
        except Exception as e:
            logger.error(f"Draft position search failed: {e}")
            return []

    def search(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """
        Perform hybrid search using both vector similarity and keyword matching
        """
        try:
            # Extract players mentioned as unavailable/already taken
            unavailable_players = self._extract_unavailable_players(query)
            
            # Check for draft position queries first
            query_lower = query.lower()
            draft_position = self._extract_draft_position(query_lower)
            if draft_position:
                # Validate draft position range
                if draft_position > 250:
                    # Return helpful message for unrealistic draft positions
                    return [{
                        'name': f'Invalid Draft Position (Pick {draft_position})',
                        'team': 'N/A',
                        'position': 'N/A',
                        'overall_rank': 'N/A',
                        'bucket_range': 'N/A',
                        'stats': {},
                        'fantasy_points': 0,
                        'fppm': 0,
                        'games': 0,
                        'minutes': 0,
                        'expert_analysis': f'Pick {draft_position} is beyond the typical fantasy draft range. Most fantasy leagues have 10-14 teams with 15-16 roster spots each, ending around pick 140-224. Consider asking about picks in the 1-200 range instead.',
                        'elite_ranking': '',
                        'text': f'Draft position {draft_position} is not realistic for fantasy basketball.',
                        'elite_ranking_score': 0,
                        'elite_fantasy_value': 0,
                        'score': 1.0
                    }]
                elif draft_position < 1:
                    # Handle negative or zero positions
                    return [{
                        'name': f'Invalid Draft Position (Pick {draft_position})',
                        'team': 'N/A',
                        'position': 'N/A',
                        'overall_rank': 'N/A',
                        'bucket_range': 'N/A',
                        'stats': {},
                        'fantasy_points': 0,
                        'fppm': 0,
                        'games': 0,
                        'minutes': 0,
                        'expert_analysis': f'Pick {draft_position} is not a valid draft position. Draft picks start at position 1. Please ask about a pick between 1-200.',
                        'elite_ranking': '',
                        'text': f'Draft position {draft_position} is not valid.',
                        'elite_ranking_score': 0,
                        'elite_fantasy_value': 0,
                        'score': 1.0
                    }]
                
                logger.info(f"Detected draft position query: {draft_position}")
                
                # For draft position queries, assume all players ranked higher than the pick are taken
                if draft_position > 1:
                    # Get players ranked 1 to (draft_position - 1) and add them to unavailable list
                    earlier_picks = self._get_players_by_rank_range(1, draft_position - 1)
                    unavailable_players.extend(earlier_picks)
                
                # Handle "top 5" type queries differently
                if any(phrase in query_lower for phrase in ['top 5', 'top five', 'top 10', 'top ten']):
                    target_num = 5 if any(phrase in query_lower for phrase in ['top 5', 'top five']) else 10
                    results = self.search_by_draft_position(draft_position, target_num)
                else:
                    results = self.search_by_draft_position(draft_position, 4)  # Return 4 players for specific position queries
                
                # Filter out unavailable players
                if unavailable_players:
                    results = self._filter_unavailable_players(results, unavailable_players)
                return results
            
            # Enhance query for fantasy basketball context
            enhanced_query = self._enhance_fantasy_query(query)
            
            # Create query embedding
            query_vector = self.embedding_model.encode(enhanced_query).tolist()
            
            # Perform vector search
            search_results = self.qdrant_client.search(
                collection_name="nba_players",
                query_vector=query_vector,
                limit=num_results,
                with_payload=True,
                with_vectors=False
            )
            
            # Extract and format results
            results = []
            for result in search_results:
                results.append({
                    'score': result.score,
                    'name': result.payload.get('player_name', ''),  # Fixed: use 'player_name' instead of 'name'
                    'team': result.payload.get('team', ''),
                    'position': result.payload.get('position', ''),
                    'overall_rank': result.payload.get('overall_rank', None),  # ADD: include overall rank
                    'bucket_range': result.payload.get('bucket_range', ''),    # ADD: include bucket range
                    'stats': result.payload.get('stats', {}),
                    'fantasy_points': result.payload.get('fantasy_points', 0),
                    'fppm': result.payload.get('fppm', 0),
                    'games': result.payload.get('games_played', 0),  # Fixed: use 'games_played' instead of 'games'
                    'minutes': result.payload.get('minutes_per_game', 0),  # Fixed: use 'minutes_per_game' instead of 'minutes'
                    'expert_analysis': result.payload.get('expert_analysis', ''),
                    'text': result.payload.get('stats_narrative', '')  # Fixed: use 'stats_narrative' for main text content
                })
            
            # Boost results based on query keywords
            boosted_results = self._apply_boosting(query, results)
            
            return boosted_results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    def _extract_draft_position(self, query_lower: str) -> int:
        """
        Extract draft position from query text
        """
        import re
        
        # Handle general top picks queries first
        if any(phrase in query_lower for phrase in ['top 5', 'top five', 'first 5', 'first five']):
            return 1  # Return position 1 to get top players
        if any(phrase in query_lower for phrase in ['top 10', 'top ten', 'first 10', 'first ten']):
            return 1  # Return position 1 to get top players
        
        # Look for patterns like "position 80", "pick 80", "80th pick", "around number 120", etc.
        patterns = [
            r'position\s+(\d+)',
            r'pick\s+(\d+)', 
            r'(\d+)(?:st|nd|rd|th)\s+pick',
            r'(\d+)(?:st|nd|rd|th)\s+position',
            r'(\d+)\s+in\s+the\s+draft',
            r'at\s+(\d+)',
            r'(\d+)\s+overall',
            r'around\s+(?:number\s+)?(\d+)',  # handle "around number 120" or "around 120"
            r'near\s+(?:pick\s+)?(\d+)',      # handle "near pick 120" or "near 120"
            r'about\s+(?:pick\s+)?(\d+)',     # handle "about pick 120" or "about 120"
            r'number\s+(\d+)\s+pick',         # NEW: handle "number 3 pick"
            r'my\s+number\s+(\d+)\s+pick',    # NEW: handle "my number 3 pick"
            r'(?:the\s+)?(\d+)\s+pick',       # NEW: handle "the 3 pick" or "3 pick"
            r'pick\s+number\s+(\d+)',         # NEW: handle "pick number 3"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query_lower)
            if match:
                position = int(match.group(1))
                # Return the position even if it's out of reasonable range
                # We'll handle validation in the calling method
                return position
        
        return None

    def _apply_boosting(self, query: str, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Apply boosting prioritizing FPPM as BY FAR THE MOST IMPORTANT METRIC (80%), then games played (15%), then minutes (5%)
        """
        query_lower = query.lower()
        
        # Calculate comprehensive ranking score for each result
        for result in results:
            # Get data from result (which now has the corrected field mappings)
            minutes_per_game = result.get('minutes', 0)  # Already mapped from 'minutes_per_game'
            fantasy_points = result.get('fantasy_points', 0)
            games_played = result.get('games', 0)  # Already mapped from 'games_played'
            
            # Also get from stats if available (backup)
            stats = result.get('stats', {})
            if minutes_per_game == 0:
                minutes_per_game = stats.get('minutes_per_game', 0)
            if games_played == 0:
                games_played = stats.get('games_played', 0)
                
            games_started = stats.get('games_started', 0)
            
            # Calculate FPPM (Fantasy Points Per Minute) - THE PRIMARY METRIC BY FAR
            fppm = fantasy_points / minutes_per_game if minutes_per_game > 0 else 0
            result['fppm'] = fppm
            
            # Minimum thresholds for meaningful analysis
            min_minutes_threshold = 12  # Lower threshold to include more elite players
            min_games_threshold = 15    # Lower threshold to include more elite players
            
            # Only consider players who meet minimum playing time requirements
            if minutes_per_game < min_minutes_threshold or games_played < min_games_threshold:
                result['elite_ranking_score'] = 0
                result['elite_fantasy_value'] = 0
                continue
            
            # 1. FPPM Score (80% weight) - BY FAR the most important metric
            # Scale FPPM heavily to dominate rankings - elite players like Jokic (1.286), Giannis should be top
            fppm_score = fppm * 1000  # Much higher multiplier for FPPM dominance
            
            # 2. Games Played Score (15% weight) - Volume and availability
            # Scale games played (50+ games is excellent, 30+ is good)
            games_score = min(games_played / 50, 1.3) * 100  # Allow boost for 65+ games
            
            # 3. Minutes Per Game Score (5% weight) - Playing time consistency (minimal impact)
            # Scale minutes (30+ minutes is excellent, 20+ is good)
            minutes_score = min(minutes_per_game / 30, 1.2) * 100  # Allow boost for 35+ minutes
            
            # Combine scores with FPPM heavily weighted
            elite_ranking_score = (
                fppm_score * 0.80 +      # FPPM BY FAR most important (80%)
                games_score * 0.15 +     # Games played for consistency (15%)
                minutes_score * 0.05     # Minutes per game minimal impact (5%)
            )
            
            result['elite_ranking_score'] = elite_ranking_score
            
            # Elite Fantasy Value = FPPM × Availability Score (as specified)
            availability_score = 0
            if games_played > 0:
                games_factor = min(games_played / 65, 1.0)  # Adjust for realistic games
                starting_factor = games_started / games_played if games_played > 0 else 0
                minutes_factor = min(minutes_per_game / 32, 1.0) if minutes_per_game >= 15 else minutes_per_game / 15 * 0.6
                availability_score = (games_factor * 0.5 + starting_factor * 0.25 + minutes_factor * 0.25)
            
            result['elite_fantasy_value'] = fppm * availability_score
        
        # Apply keyword boosts for search relevance (minimal impact on FPPM dominance)
        boost_factors = {
            'draft': 1.05,    # Smaller boosts to let FPPM dominate
            'picks': 1.05,
            'best': 1.03,
            'top': 1.03,
            'first': 1.05,
            'fantasy': 1.02,
            'points': 1.02
        }
        
        for result in results:
            boost = 1.0
            
            # Apply minimal keyword boosts - FPPM should still dominate
            for keyword, factor in boost_factors.items():
                if keyword in query_lower:
                    boost *= factor
            
            result['elite_ranking_score'] = result.get('elite_ranking_score', 0) * boost
        
        # For draft/best player queries - ALWAYS sort by elite ranking score (FPPM priority)
        if any(term in query_lower for term in ['draft', 'picks', 'best', 'top', 'first']):
            # Sort purely by elite ranking score - FPPM dominance ensures Jokic, Giannis, Luka, Shai, Doncic at top
            results.sort(key=lambda x: x.get('elite_ranking_score', 0), reverse=True)
        else:
            # For other queries, still heavily prioritize elite ranking over similarity
            results.sort(key=lambda x: (x.get('elite_ranking_score', 0) * 0.9 + x.get('score', 0) * 0.1), reverse=True)
        
        # Filter out unavailable players if any were mentioned
        unavailable_players = self._extract_unavailable_players(query)
        if unavailable_players:
            results = self._filter_unavailable_players(results, unavailable_players)
            
        return results

    def _extract_unavailable_players(self, query: str) -> List[str]:
        """
        Extract player names that are mentioned as already taken, picked, or unavailable
        """
        unavailable_players = []
        query_lower = query.lower()
        
        import re
        
        # First, handle common patterns like "luka and wemby are already taken"
        # Look for lists of names followed by "are/were taken/picked"
        list_patterns = [
            r'([a-z\s,]+?)\s+(?:are|were|have been)\s+(?:already\s+)?(?:taken|picked|drafted|selected)',
            r'([a-z\s,]+?)\s+(?:already|been)\s+(?:taken|picked|drafted|selected)',
        ]
        
        for pattern in list_patterns:
            matches = re.findall(pattern, query_lower)
            for match in matches:
                # Split by 'and' or ',' to get individual names
                names_text = match.strip()
                # Replace 'and' with ',' for consistent splitting
                names_text = names_text.replace(' and ', ', ')
                # Split by comma
                individual_names = [name.strip() for name in names_text.split(',')]
                
                for name in individual_names:
                    if name:
                        # Clean up the name
                        cleaned_name = name.strip()
                        # Remove common words and phrases that might get captured
                        words_to_remove = ['the', 'is', 'was', 'has', 'been', 'already', 'taken', 'picked', 'drafted', 'selected', 'are', 'were', 'my', 'th', 'pick', 'should', 'be']
                        name_words = [word for word in cleaned_name.split() if word not in words_to_remove and len(word) > 1]
                        
                        if name_words:
                            # Handle common nickname cases
                            final_name = ' '.join(name_words).title()
                            
                            # Map common nicknames to full names
                            nickname_mapping = {
                                'Luka': 'Luka Dončić',
                                'Wemby': 'Victor Wembanyama', 
                                'Giannis': 'Giannis Antetokounmpo',
                                'Jokic': 'Nikola Jokić',
                                'Ad': 'Anthony Davis',
                                'Kat': 'Karl-Anthony Towns',
                                'Shai': 'Shai Gilgeous-Alexander'
                            }
                            
                            # Check if it's a known nickname
                            if final_name in nickname_mapping:
                                unavailable_players.append(nickname_mapping[final_name])
                            elif len(final_name) > 2:  # Must be reasonable length
                                unavailable_players.append(final_name)
        
        # Also check for individual mentions like "Anthony Davis is already taken"
        individual_patterns = [
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:is|was|has been)\s+(?:already\s+)?(?:taken|picked|drafted|selected)',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:already|been)\s+(?:taken|picked|drafted|selected)',
        ]
        
        for pattern in individual_patterns:
            matches = re.findall(pattern, query)  # Use original case for proper names
            for match in matches:
                if match.strip() and len(match.strip()) > 2:
                    unavailable_players.append(match.strip())
        
        # Remove duplicates while preserving order
        seen = set()
        unique_unavailable = []
        for player in unavailable_players:
            if player not in seen:
                seen.add(player)
                unique_unavailable.append(player)
        
        if unique_unavailable:
            logger.info(f"Detected unavailable players: {unique_unavailable}")
        
        return unique_unavailable

    def _get_players_by_rank_range(self, start_rank: int, end_rank: int) -> List[str]:
        """
        Get player names for players ranked between start_rank and end_rank (inclusive)
        """
        try:
            # Get all players and filter by rank
            all_results = self.qdrant_client.scroll(
                collection_name="nba_players",
                limit=450,
                with_payload=True
            )[0]
            
            player_names = []
            for result in all_results:
                payload = result.payload
                overall_rank = payload.get('overall_rank', 999)
                
                if isinstance(overall_rank, (int, float)) and start_rank <= overall_rank <= end_rank:
                    player_name = payload.get('player_name', '')
                    if player_name:
                        player_names.append(player_name)
            
            return player_names
            
        except Exception as e:
            logger.error(f"Failed to get players by rank range: {e}")
            return []

    def _filter_unavailable_players(self, results: List[Dict[str, Any]], unavailable_players: List[str]) -> List[Dict[str, Any]]:
        """
        Filter out players that are mentioned as unavailable
        """
        if not unavailable_players:
            return results
        
        filtered_results = []
        unavailable_lower = [name.lower() for name in unavailable_players]
        
        for result in results:
            player_name = result.get('name', '').lower()
            # Check if this player is in the unavailable list
            is_unavailable = False
            for unavailable_name in unavailable_lower:
                # Check for exact match or if the unavailable name is contained in the player name
                if unavailable_name in player_name or player_name in unavailable_name:
                    # Additional check: make sure it's a meaningful match (not just partial word match)
                    unavailable_words = set(unavailable_name.split())
                    player_words = set(player_name.split())
                    # If at least 2 words match or there's a substantial overlap, consider it unavailable
                    if len(unavailable_words.intersection(player_words)) >= 2 or \
                       (len(unavailable_words) == 1 and unavailable_words.issubset(player_words)):
                        is_unavailable = True
                        logger.info(f"Filtering out unavailable player: {result.get('name')}")
                        break
            
            if not is_unavailable:
                filtered_results.append(result)
        
        return filtered_results

    def _enhance_fantasy_query(self, query: str) -> str:
        """
        Enhance queries with fantasy basketball context - prioritize elite FPPM players
        """
        query_lower = query.lower()
        
        # Handle specific draft position queries (e.g., "14th pick")
        if any(term in query_lower for term in ['14th', '15th', '16th', '17th', '18th', '19th', '20th']) or 'pick' in query_lower:
            # For mid-round picks, search for a broader range including sleepers
            enhanced = f"{query} draft sleeper value picks breakout potential expert analysis mid-round fantasy basketball players FPPM efficiency"
            return enhanced
        
        # Handle draft pick queries - should return elite FPPM players: Jokic, Giannis, Luka, Shai
        if any(term in query_lower for term in ['draft', 'picks', 'first', 'top', 'best']):
            # Add the specific elite players that should dominate rankings
            enhanced = f"{query} Jokic Giannis Antetokounmpo Luka Doncic Shai Gilgeous-Alexander elite NBA superstars high FPPM fantasy points"
            return enhanced
            
        # Handle best player queries - should return absolute elite players
        if any(term in query_lower for term in ['recommend', 'elite', 'star']):
            # Add context for elite NBA superstars with highest FPPM
            enhanced = f"{query} Jokic Giannis Antetokounmpo Luka Doncic Shai Gilgeous-Alexander elite NBA superstars highest FPPM"
            return enhanced
            
        return query

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
        Build a comprehensive prompt for the LLM using search results
        """
        # Check for invalid position cases first
        if search_results and len(search_results) == 1 and 'Invalid Draft Position' in search_results[0].get('name', ''):
            invalid_result = search_results[0]
            return f"""
QUERY: {query}

RESPONSE: {invalid_result.get('expert_analysis', '')}

Please provide a helpful, friendly response explaining why this draft position is not realistic and suggest asking about positions in the normal fantasy draft range (picks 1-200).
            """.strip()
        
        # Check if this is a draft position query
        is_draft_query = any(word in query.lower() for word in ['position', 'pick', 'draft'])
        is_top_picks_query = any(phrase in query.lower() for phrase in ['top 5', 'top five', 'top 10', 'top ten'])
        
        if is_draft_query or is_top_picks_query:
            if is_top_picks_query:
                prompt_template = """
You are a friendly, knowledgeable Fantasy NBA expert helping someone with their draft strategy. Be conversational and helpful.

QUERY: {query}

TOP FANTASY PLAYERS (by overall rank):
{context}

INSTRUCTIONS:
1. **Be conversational and friendly** - like chatting with a fantasy buddy
2. **These are the actual top-ranked players** - explain why they're elite
3. **Focus on the best 3-5 players** for a top picks question
4. **Explain what makes each player special** using their stats and analysis
5. **Use casual language** like "Here are the must-have players..." or "You can't go wrong with..."
6. **Mention FPPM and overall impact** - these are elite fantasy producers
7. **Keep it concise** - 2-3 sentences per top player

ANSWER STYLE: Enthusiastic and knowledgeable, focusing on why these are the cream of the crop.
        """.strip()
            else:
                prompt_template = """
You are a friendly, knowledgeable Fantasy NBA expert helping someone with their draft strategy. Be conversational and helpful, like you're chatting with a friend who needs fantasy advice.

QUERY: {query}

AVAILABLE PLAYERS FOR THIS DRAFT POSITION:
{context}

INSTRUCTIONS:
1. **Be conversational and friendly** - don't be formal or robotic
2. **Focus on 2-3 top recommendations** from the provided players
3. **These players are already filtered by draft position** - they're all realistic options
4. **Explain why each player is a good pick** using their stats and expert analysis
5. **Use casual language** like "Here's who I'd target..." or "You should definitely consider..."
6. **Mention FPPM but explain it simply** - "points per minute" not technical jargon
7. **Include team context and role** from the expert analysis
8. **Keep it concise** - 3-4 sentences per player recommendation max

ANSWER STYLE: Casual, helpful, and focused on actionable advice for this specific draft position.
        """.strip()
        else:
            prompt_template = """
You are a friendly Fantasy NBA expert with deep knowledge of player stats and strategy. Answer in a conversational, helpful tone.

QUERY: {query}

RELEVANT PLAYER DATA:
{context}

INSTRUCTIONS:
1. **Be conversational** - like talking to a friend who needs fantasy help
2. **Focus on the most relevant players** for the question asked
3. **Explain your reasoning** using the stats and expert analysis provided
4. **Use FPPM (fantasy points per minute)** as the key efficiency metric
5. **Include context** from expert analysis when available
6. **Keep it practical** - give actionable advice they can use

ANSWER:
        """.strip()

        # Build context from search results
        context = ""
        for i, result in enumerate(search_results, 1):
            # Use the already-mapped values from the search results
            fppg = result['fantasy_points']  # Fantasy Points Per GAME
            fppm = result.get('fppm', 0)  # Use stored FPPM (already correctly calculated)
            minutes_per_game = result.get('minutes', 0)  # Already mapped from minutes_per_game
            games_played = result.get('games', 0)  # Already mapped from games_played
            overall_rank = result.get('overall_rank', 'N/A')
            bucket_range = result.get('bucket_range', 'N/A')
            
            # Get additional stats from the stats object
            stats = result.get('stats', {})
            
            if is_top_picks_query:
                # Special format for top picks queries - emphasize elite status
                context += f"""
{result['name']} ({result['position']}, {result['team']}) - Overall Rank #{overall_rank} (Elite Tier)
• FPPM: {fppm:.3f} (fantasy points per minute) - Elite efficiency
• Games: {games_played}, Minutes: {minutes_per_game:.1f} per game
• Expert Analysis: {result.get('expert_analysis', '')[:350]}{'...' if len(result.get('expert_analysis', '')) > 350 else ''}
• Elite Ranking: {result.get('elite_ranking', '')[:250]}{'...' if len(result.get('elite_ranking', '')) > 250 else ''}

"""
            elif is_draft_query:
                # Simplified format for specific draft position queries
                context += f"""
{result['name']} ({result['position']}, {result['team']}) - Overall Rank #{overall_rank} ({bucket_range} bucket)
• FPPM: {fppm:.3f} (fantasy points per minute)
• Games: {games_played}, Minutes: {minutes_per_game:.1f} per game
• Expert Analysis: {result.get('expert_analysis', '')[:300]}{'...' if len(result.get('expert_analysis', '')) > 300 else ''}
• Elite Ranking: {result.get('elite_ranking', '')[:200]}{'...' if len(result.get('elite_ranking', '')) > 200 else ''}

"""
            else:
                # Detailed format for other queries
                context += f"""
Player {i}: {result['name']} ({result['position']}, {result['team']})
- FPPG (Fantasy Points Per GAME): {fppg:.1f} ← Total points per game
- FPPM (Fantasy Points Per MINUTE): {fppm:.3f} ← Efficiency (stored value)
- Minutes Per Game: {minutes_per_game:.1f}
- Games Played: {games_played}
- Key Stats: {stats.get('points', 0)} PTS, {stats.get('assists', 0)} AST, {stats.get('total_rebounds', 0)} REB
- Expert Analysis: {result['expert_analysis'][:500]}{'...' if len(result['expert_analysis']) > 500 else ''}

"""

        prompt = prompt_template.format(query=query, context=context.strip())
        return prompt

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