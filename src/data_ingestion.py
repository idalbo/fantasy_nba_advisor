import os
import requests
import pandas as pd
from bs4 import BeautifulSoup
import time
import json
import re
from typing import List, Dict
from tqdm import tqdm
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
import uuid
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataIngestion:
    def __init__(self):
        self.qdrant_host = os.getenv('QDRANT_HOST', 'localhost')
        self.qdrant_port = int(os.getenv('QDRANT_PORT', 6333))
        self.client = QdrantClient(host=self.qdrant_host, port=self.qdrant_port)
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.collection_name = "nba_players"
        
        # Fantasy scoring system
        self.scoring_system = {
            'FT': 1.5,
            'FTA': -0.5,
            '2P': 2.5,
            '2PA': -0.5,
            '3P': 3.5,
            '3PA': -0.5,
            'ORB': 1.0,
            'DRB': 1.0,
            'AST': 1.0,
            'BLK': 1.0,
            'STL': 1.0,
            'TOV': -1.0
        }

    def setup_collection(self):
        """Create or recreate the Qdrant collection"""
        logger.info("Setting up Qdrant collection...")
        
        # Delete collection if it exists
        try:
            self.client.delete_collection(collection_name=self.collection_name)
            logger.info("Deleted existing collection")
        except:
            pass
        
        # Create new collection
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE),
        )
        logger.info(f"Created collection: {self.collection_name}")

    def scrape_basketball_reference(self):
        """Scrape NBA player statistics from Basketball Reference"""
        logger.info("Scraping Basketball Reference for NBA player statistics...")
        
        url = "https://www.basketball-reference.com/leagues/NBA_2025_per_game.html"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find the stats table
            table = soup.find('table', {'id': 'per_game_stats'})
            if not table:
                # If not found, try to find it by class or other attributes
                table = soup.find('table', class_='sortable')
                if not table:
                    # Try to find any table with stats
                    tables = soup.find_all('table')
                    for t in tables:
                        if 'Player' in str(t) and 'PTS' in str(t):
                            table = t
                            break
            
            if not table:
                logger.error("Could not find statistics table on Basketball Reference")
                raise Exception("Statistics table not found")
            
            try:
                # First, extract team information directly from HTML
                team_data = self._extract_team_data_from_html(table)
                
                # Convert table to DataFrame using pandas read_html
                df_list = pd.read_html(str(table))
                df = df_list[0]
                
                # Debug: Print column names
                logger.info(f"Scraped columns: {list(df.columns)}")
                
                # Clean up the DataFrame
                df = df[df['Player'] != 'Player']  # Remove header rows
                df = df.dropna(subset=['Player'])  # Remove empty rows
                
                # Add extracted team data to DataFrame
                df = self._merge_team_data(df, team_data)
                
                # Debug: Show sample of first few rows
                if not df.empty:
                    logger.info(f"Sample row with team data:")
                    sample_row = df.iloc[0]
                    logger.info(f"   Player: {sample_row.get('Player', 'N/A')}")
                    logger.info(f"   Team: {sample_row.get('Team_Extracted', 'N/A')}")
                    logger.info(f"   Position: {sample_row.get('Pos', 'N/A')}")
                
                # Handle players with multiple teams (keep only TOT - total season stats)
                df = self._deduplicate_players(df)
                
                # Convert numeric columns to proper types
                numeric_columns = ['Age', 'G', 'GS', 'MP', 'FG', 'FGA', 'FG%', '3P', '3PA', '3P%', 
                                 '2P', '2PA', '2P%', 'eFG%', 'FT', 'FTA', 'FT%', 'ORB', 'DRB', 
                                 'TRB', 'AST', 'STL', 'BLK', 'TOV', 'PF', 'PTS']
                
                for col in numeric_columns:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                
                logger.info(f"Successfully scraped and processed {len(df)} unique player records")
                logger.info(f"Sample player: {df.iloc[0]['Player'] if not df.empty else 'None'}")
                return df
                
            except Exception as e:
                logger.error(f"Error parsing table: {e}")
                raise Exception(f"Failed to parse Basketball Reference data: {e}")
                
        except Exception as e:
            logger.error(f"Error scraping Basketball Reference: {e}")
            raise Exception(f"Failed to scrape Basketball Reference: {e}")

    def _deduplicate_players(self, df):
        """Remove duplicate players, keeping TOT (total) stats when available"""
        logger.info("Deduplicating players with multiple team entries...")
        
        # Check which team column exists
        team_col = None
        possible_team_cols = ['Tm', 'Team', 'TM', 'TEAM']
        for col in possible_team_cols:
            if col in df.columns:
                team_col = col
                break
        
        if not team_col:
            logger.warning("No team column found, returning data as-is")
            return df
        
        # Group by player name
        deduplicated_players = []
        
        for player_name in df['Player'].unique():
            player_rows = df[df['Player'] == player_name]
            
            if len(player_rows) == 1:
                # Single team, keep as is
                deduplicated_players.append(player_rows.iloc[0])
            else:
                # Multiple teams, prefer TOT (total) stats
                tot_row = player_rows[player_rows[team_col] == 'TOT']
                if not tot_row.empty:
                    deduplicated_players.append(tot_row.iloc[0])
                else:
                    # If no TOT row, take the first entry
                    deduplicated_players.append(player_rows.iloc[0])
        
        result_df = pd.DataFrame(deduplicated_players)
        logger.info(f"Deduplicated from {len(df)} to {len(result_df)} unique players")
        return result_df

    def _parse_table_manually(self, table):
        """Manually parse the HTML table"""
        try:
            rows = table.find_all('tr')
            headers = []
            data = []
            
            # Get headers
            header_row = rows[0]
            for th in header_row.find_all(['th', 'td']):
                headers.append(th.get_text().strip())
            
            # Get data rows
            for row in rows[1:]:
                row_data = []
                for td in row.find_all(['td', 'th']):
                    row_data.append(td.get_text().strip())
                if row_data and len(row_data) >= len(headers):
                    data.append(row_data[:len(headers)])
            
            if headers and data:
                df = pd.DataFrame(data, columns=headers)
                return df
            
            return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"Manual table parsing failed: {e}")
            return pd.DataFrame()

    def scrape_hoopshype_rankings(self):
        """Scrape player rankings and analysis from HoopsHype"""
        logger.info("Scraping HoopsHype rankings...")
        
        url = "https://eu.hoopshype.com/story/sports/nba/2025/10/03/nba-ranking-the-top-100-players-for-2025-26/86477672007/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebTree/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            rankings_data = {}
            # Find article content or player sections
            article_content = soup.find(['article', 'div'], class_=lambda x: x and 'content' in x.lower())
            
            if article_content:
                # Extract player mentions and surrounding context
                paragraphs = article_content.find_all('p')
                for p in paragraphs:
                    text = p.get_text().strip()
                    if len(text) > 100:  # Substantial content
                        # Try to identify player names in the text
                        # This is a simplified approach - in practice, you'd want more sophisticated NLP
                        words = text.split()
                        for i, word in enumerate(words):
                            if word.istitle() and i < len(words) - 1 and words[i+1].istitle():
                                potential_name = f"{word} {words[i+1]}"
                                if potential_name not in rankings_data:
                                    rankings_data[potential_name] = text
            
            logger.info(f"Successfully scraped {len(rankings_data)} player analyses from HoopsHype")
            return rankings_data
            
        except Exception as e:
            logger.error(f"Error scraping HoopsHype: {e}")
            return {}

    def _normalize_name(self, name):
        """Normalize player name for comparison"""
        if not name:
            return ""
        return re.sub(r'[^\w\s]', '', name.strip().lower())

    def _safe_convert(self, value, conversion_type=float):
        """Safely convert value to specified type"""
        try:
            if value is None or value == '':
                return None
            return conversion_type(value)
        except (ValueError, TypeError):
            return None

    def _extract_team_data_from_html(self, table):
        """Extract team information directly from an HTML table.

        This function is robust to variations in Basketball-Reference table
        markup: it tries 'team_id' first, then 'team_name_abbr'. Returns a
        dict mapping player display name -> team abbreviation.
        """
        logger.info("Extracting team data from HTML...")
        team_data = {}

        try:
            rows = table.find_all('tr')
            for row in rows[1:]:  # Skip header row
                player_cell = row.find('td', {'data-stat': 'player'})
                if not player_cell:
                    continue

                player_name = player_cell.get_text().strip()
                if not player_name or player_name == 'Player':
                    continue

                # Prefer team_id column but fall back to team_name_abbr
                team_cell = row.find('td', {'data-stat': 'team_id'}) or row.find('td', {'data-stat': 'team_name_abbr'})
                if not team_cell:
                    continue

                team_link = team_cell.find('a')
                team = team_link.get_text().strip() if team_link else team_cell.get_text().strip()
                if team and team not in ['Tm', '']:
                    team_data[player_name] = team

            logger.info(f"Extracted team data for {len(team_data)} players")
            if team_data:
                sample_teams = list(team_data.items())[:3]
                for player, team in sample_teams:
                    logger.info(f"   {player}: {team}")

        except Exception as e:
            logger.error(f"Error extracting team data: {e}")

        return team_data
    
    def _merge_team_data(self, df, team_data):
        """Merge extracted team data into the DataFrame.

        Adds `Team_Extracted` (the canonical extracted value) and, for
        compatibility, sets `Team` when it is missing or empty.
        """
        logger.info("Merging team data with DataFrame...")

        df = df.copy()
        df['Team_Extracted'] = df['Player'].map(team_data)

        # If a canonical Team column is missing or empty, populate it from Team_Extracted
        if 'Team' not in df.columns:
            df['Team'] = None

        missing_team_mask = df['Team'].isna() | (df['Team'].astype(str).str.strip() == '')
        df.loc[missing_team_mask, 'Team'] = df.loc[missing_team_mask, 'Team_Extracted']

        successful_matches = df['Team_Extracted'].notna().sum()
        logger.info(f"Successfully matched team data for {successful_matches}/{len(df)} players")

        return df

    def _get_team_name(self, row):
        """Extract team name with fallback handling"""
        # Try different possible team column names
        possible_team_cols = ['Team', 'Tm', 'TM', 'TEAM', 'tm', 'team']
        
        for col in possible_team_cols:
            if col in row.index and pd.notna(row.get(col)) and row.get(col) != '':
                team = str(row[col]).strip()
                if team and team.upper() not in ['NAN', 'UNKNOWN', '']:
                    return team
        
        # If still no team found, log for debugging
        logger.warning(f"No team found for player {row.get('Player', 'Unknown')}. Available columns: {list(row.index)}")
        return 'Unknown'


    def _clean_html(self, text):
        """Clean HTML tags and normalize text"""
        if not text:
            return ""
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', ' ', text)
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        # Fix Unicode escape sequences and special characters
        text = text.encode('utf-8').decode('unicode_escape').encode('latin1').decode('utf-8', errors='ignore')
        # Fix common Unicode characters manually if needed
        text = text.replace('\u2019', "'")  # Right single quotation mark
        text = text.replace('\u2018', "'")  # Left single quotation mark  
        text = text.replace('\u201c', '"')  # Left double quotation mark
        text = text.replace('\u201d', '"')  # Right double quotation mark
        text = text.replace('\u2013', '-')  # En dash
        text = text.replace('\u2014', '—')  # Em dash
        text = text.replace('\u2026', '...')  # Horizontal ellipsis
        return text.strip()

    def _extract_badges(self, badges_data):
        """Extract meaningful badges from badges data"""
        if not badges_data or not isinstance(badges_data, list):
            return []
        
        meaningful_badges = []
        for badge in badges_data:
            if isinstance(badge, dict) and badge.get('title'):
                title = badge['title']
                # Filter for basketball-relevant badges
                if any(keyword in title.lower() for keyword in ['mvp', 'championship', 'all-star', 'rookie', 'dpoy', 'sixth man']):
                    meaningful_badges.append(title)
        
        return meaningful_badges

    def collect_ringer_data(self):
        """Collect The Ringer rankings data"""
        logger.info("Collecting The Ringer rankings data...")
        
        try:
            url = "https://nbarankings.theringer.com/"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            rankings_data = {}
            
            # Extract Next.js data
            next_data_pattern = r'<script id="__NEXT_DATA__" type="application/json">({.*?})</script>'
            match = re.search(next_data_pattern, response.text, re.DOTALL)
            
            if match:
                try:
                    next_data = json.loads(match.group(1))
                    logger.info("Found __NEXT_DATA__ script tag")
                    
                    # Navigate the Next.js data structure
                    props = next_data.get('props', {})
                    page_props = props.get('pageProps', {})
                    
                    # Look for player data in various possible locations
                    players = None
                    possible_keys = ['processedPlayers', 'players', 'rankings', 'data', 'playerList', 'nbaPlayers', 'playerRankings', 'playersData', 'allPlayers', 'roster']
                    
                    for key in possible_keys:
                        if key in page_props:
                            players = page_props[key]
                            logger.info(f"Found player data under key: {key}")
                            break
                    
                    # If not found in pageProps, check other locations
                    if not players:
                        initial_props = next_data.get('props', {}).get('initialProps', {})
                        if initial_props:
                            for key in possible_keys:
                                if key in initial_props:
                                    players = initial_props[key]
                                    logger.info(f"Found player data in initialProps under key: {key}")
                                    break
                    
                    # Check nested pageProps
                    if not players:
                        for main_key in page_props.keys():
                            if isinstance(page_props[main_key], dict):
                                nested_dict = page_props[main_key]
                                for key in possible_keys:
                                    if key in nested_dict:
                                        potential_players = nested_dict[key]
                                        if isinstance(potential_players, list) and len(potential_players) > 0:
                                            players = potential_players
                                            logger.info(f"Found nested player list with {len(players)} items")
                                            break
                                        elif isinstance(potential_players, dict):
                                            for sub_key in possible_keys:
                                                if sub_key in potential_players and isinstance(potential_players[sub_key], list):
                                                    players = potential_players[sub_key]
                                                    logger.info(f"Found nested player list with {len(players)} items")
                                                    break
                                if players:
                                    break
                    
                    if players and isinstance(players, list):
                        logger.info(f"Processing {len(players)} players from Next.js data")
                        
                        # Look for playerData
                        player_data = next_data.get('props', {}).get('pageProps', {}).get('content', {}).get('processedPlayers', {}).get('playerData', {})
                        if player_data:
                            logger.info(f"Found playerData with {len(player_data)} entries")
                            
                            extracted_count = 0
                            for i, player_id in enumerate(players[:100]):
                                if player_id in player_data:
                                    player_obj = player_data[player_id]
                                    
                                    if isinstance(player_obj, dict):
                                        first_name = player_obj.get('first_name', '').strip()
                                        last_name = player_obj.get('last_name', '').strip()
                                        name = f"{first_name} {last_name}".strip() if first_name and last_name else player_obj.get('title', '').strip()
                                        
                                        if name:
                                            description_parts = []
                                            
                                            if player_obj.get('team'):
                                                description_parts.append(f"Plays for {player_obj['team']}")
                                            
                                            if player_obj.get('position'):
                                                description_parts.append(f"Position: {player_obj['position']}")
                                            
                                            description_parts.append(f"Ranked #{i+1} by The Ringer")
                                            
                                            for field in ['analysis', 'description', 'commentary', 'summary']:
                                                if player_obj.get(field):
                                                    description_parts.append(str(player_obj[field]))
                                                    break
                                            
                                            if description_parts:
                                                final_description = ". ".join(description_parts)
                                                rankings_data[name] = final_description
                                                extracted_count += 1
                            
                            logger.info(f"Successfully extracted {extracted_count} player analyses from The Ringer")
                        else:
                            logger.warning("No playerData found in Next.js structure")
                    else:
                        logger.warning("No player array found in Next.js structure")
                        
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse Next.js JSON data: {e}")
                except Exception as e:
                    logger.error(f"Error processing Next.js data: {e}")
            else:
                logger.warning("No __NEXT_DATA__ script tag found")
            
            return rankings_data
            
        except Exception as e:
            logger.error(f"Error collecting Ringer data: {e}")
            return {}

    def scrape_hoopshype_rankings(self):
        """Scrape player rankings and analysis from HoopsHype"""
        logger.info("Scraping HoopsHype rankings...")
        
        url = "https://eu.hoopshype.com/story/sports/nba/2025/10/03/nba-ranking-the-top-100-players-for-2025-26/86477672007/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebTree/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            rankings_data = {}
            # Find article content or player sections
            article_content = soup.find(['article', 'div'], class_=lambda x: x and 'content' in x.lower())
            
            if article_content:
                # Extract player mentions and surrounding context
                paragraphs = article_content.find_all('p')
                for p in paragraphs:
                    text = p.get_text().strip()
                    if len(text) > 100:  # Substantial content
                        # Try to identify player names in the text
                        words = text.split()
                        for i, word in enumerate(words):
                            if word.istitle() and i < len(words) - 1 and words[i+1].istitle():
                                potential_name = f"{word} {words[i+1]}"
                                if potential_name not in rankings_data:
                                    rankings_data[potential_name] = text
            
            logger.info(f"Successfully scraped {len(rankings_data)} player analyses from HoopsHype")
            return rankings_data
            
        except Exception as e:
            logger.error(f"Error scraping HoopsHype: {e}")
            return {}

    def calculate_fantasy_points(self, stats):
        """Calculate fantasy points based on the scoring system"""
        try:
            fantasy_points = 0
            for stat, multiplier in self.scoring_system.items():
                if stat in stats and pd.notna(stats[stat]):
                    fantasy_points += float(stats[stat]) * multiplier
            return round(fantasy_points, 2)
        except:
            return 0.0

    def combine_expert_analysis(self, player_name, ringer_data, hoopshype_data):
        """Combine expert analysis from multiple sources"""
        analysis_parts = []
        
        # Check for exact name match first
        if player_name in ringer_data:
            clean_analysis = self._clean_html(ringer_data[player_name])
            analysis_parts.append(f"The Ringer Analysis: {clean_analysis}")
        
        if player_name in hoopshype_data:
            clean_analysis = self._clean_html(hoopshype_data[player_name])
            analysis_parts.append(f"HoopsHype Analysis: {clean_analysis}")
        
        # If no exact match, try partial matching
        if not analysis_parts:
            first_name, last_name = player_name.split()[:2] if len(player_name.split()) >= 2 else (player_name, "")
            
            for source_name, analysis in ringer_data.items():
                if first_name in source_name and last_name in source_name:
                    clean_analysis = self._clean_html(analysis)
                    analysis_parts.append(f"The Ringer Analysis: {clean_analysis}")
                    break
            
            for source_name, analysis in hoopshype_data.items():
                if first_name in source_name and last_name in source_name:
                    clean_analysis = self._clean_html(analysis)
                    analysis_parts.append(f"HoopsHype Analysis: {clean_analysis}")
                    break
        
        return " | ".join(analysis_parts) if analysis_parts else "No expert analysis available."

    def prepare_documents(self, stats_df, ringer_data, hoopshype_data):
        """Prepare documents for vector database ingestion with improved structure"""
        logger.info("Preparing documents for ingestion with new structure...")
        
        documents = []
        all_elite_values = []
        
        # First pass: Calculate all elite values for ranking
        for _, row in stats_df.iterrows():
            try:
                player_name = row['Player']
                
                # Basic stats extraction
                games_played = row.get('G', 0)
                games_started = row.get('GS', 0)
                minutes_per_game = row.get('MP', 0)
                
                # Calculate fantasy points
                fantasy_points = self.calculate_fantasy_points({
                    'FT': row.get('FT', 0),
                    'FTA': row.get('FTA', 0),
                    '2P': row.get('2P', 0),
                    '2PA': row.get('2PA', 0),
                    '3P': row.get('3P', 0),
                    '3PA': row.get('3PA', 0),
                    'ORB': row.get('ORB', 0),
                    'DRB': row.get('DRB', 0),
                    'AST': row.get('AST', 0),
                    'BLK': row.get('BLK', 0),
                    'STL': row.get('STL', 0),
                    'TOV': row.get('TOV', 0)
                })
                
                # Calculate FPPM
                fppm = fantasy_points / minutes_per_game if minutes_per_game > 0 else 0
                
                # Calculate Elite Fantasy Value
                if games_played > 0 and minutes_per_game > 0:
                    starter_ratio = games_started / games_played if games_started <= games_played else 1.0
                    
                    if minutes_per_game >= 35:
                        minutes_factor = 1.0
                    elif minutes_per_game >= 30:
                        minutes_factor = 0.9 + (minutes_per_game - 30) * 0.02
                    elif minutes_per_game >= 25:
                        minutes_factor = 0.8 + (minutes_per_game - 25) * 0.02
                    elif minutes_per_game >= 20:
                        minutes_factor = 0.7 + (minutes_per_game - 20) * 0.02
                    elif minutes_per_game >= 15:
                        minutes_factor = 0.6 + (minutes_per_game - 15) * 0.02
                    else:
                        minutes_factor = min(minutes_per_game / 15.0 * 0.6, 0.6)
                    
                    availability_score = starter_ratio * 0.4 + minutes_factor * 0.6
                    elite_fantasy_value = fppm * availability_score
                else:
                    elite_fantasy_value = 0
                
                # Only include players with meaningful stats
                if minutes_per_game >= 10 and games_played >= 5:
                    all_elite_values.append((player_name, elite_fantasy_value, row))
                    
            except Exception as e:
                logger.error(f"Error calculating elite value for {row.get('Player', 'Unknown')}: {e}")
                continue
        
        # Sort by elite fantasy value (descending) to create rankings
        all_elite_values.sort(key=lambda x: x[1], reverse=True)
        
        # Second pass: Create documents with rankings
        for rank, (player_name, elite_fantasy_value, row) in enumerate(tqdm(all_elite_values, desc="Creating documents"), 1):
            try:
                # Extract all stats
                team_name = self._get_team_name(row)
                position = row.get('Pos', 'Unknown')
                games_played = row.get('G', 0)
                games_started = row.get('GS', 0)
                minutes_per_game = row.get('MP', 0)
                
                # Calculate all stats
                fantasy_points = self.calculate_fantasy_points({
                    'FT': row.get('FT', 0),
                    'FTA': row.get('FTA', 0),
                    '2P': row.get('2P', 0),
                    '2PA': row.get('2PA', 0),
                    '3P': row.get('3P', 0),
                    '3PA': row.get('3PA', 0),
                    'ORB': row.get('ORB', 0),
                    'DRB': row.get('DRB', 0),
                    'AST': row.get('AST', 0),
                    'BLK': row.get('BLK', 0),
                    'STL': row.get('STL', 0),
                    'TOV': row.get('TOV', 0)
                })
                
                fppm = fantasy_points / minutes_per_game if minutes_per_game > 0 else 0
                
                # Get expert analysis (combined from both sources)
                expert_analysis = self.combine_expert_analysis(player_name, ringer_data, hoopshype_data)
                
                # Create FIELD 1: Statistical Narrative (Main content - higher value for stats)
                stats_text = f"{player_name} is a {position.lower()} who played {games_played} games last season, appearing for {round(minutes_per_game, 1)} minutes per game. He started {games_started} of those games, giving him a starter ratio of {round(games_started / games_played if games_played > 0 else 0, 3)}. On average, he scored {row.get('PTS', 0)} points per game, dished out {row.get('AST', 0)} assists per game, and grabbed {row.get('TRB', 0)} rebounds per game. His shooting efficiency shows {row.get('FG%', 0):.1%} field goal percentage, {row.get('3P%', 0):.1%} from three-point range, and {row.get('FT%', 0):.1%} from the free-throw line. He also contributed {row.get('STL', 0)} steals and {row.get('BLK', 0)} blocks per game while turning the ball over {row.get('TOV', 0)} times per game. His fantasy production averages {round(fantasy_points, 2)} fantasy points per game, giving him an efficiency rating of {round(fppm, 3)} fantasy points per minute played."
                
                # Create FIELD 2: Expert Analysis (Secondary content)
                expert_text = expert_analysis if expert_analysis != "No expert analysis available." else f"Expert analysis for {player_name} is not available from current sources."
                
                # Create FIELD 3: Draft Ranking & Elite Score (Boosted field for draft questions)
                # Determine bucket (1-10, 11-20, 21-30, etc.)
                bucket_start = ((rank - 1) // 10) * 10 + 1
                bucket_end = bucket_start + 9
                total_players = len(all_elite_values)
                
                # Identify key strength
                key_strength = "balanced production"
                if row.get('AST', 0) >= 7:
                    key_strength = "elite playmaking and assists"
                elif row.get('TRB', 0) >= 10:
                    key_strength = "dominant rebounding"
                elif row.get('PTS', 0) >= 25:
                    key_strength = "high-volume scoring"
                elif row.get('STL', 0) + row.get('BLK', 0) >= 2:
                    key_strength = "defensive contributions"
                elif row.get('3P', 0) >= 2.5:
                    key_strength = "three-point shooting"
                
                # Draft recommendation based on ranking
                if rank <= 12:
                    draft_rec = "first round pick"
                elif rank <= 24:
                    draft_rec = "early second round pick"
                elif rank <= 36:
                    draft_rec = "mid second round pick"
                elif rank <= 48:
                    draft_rec = "late second round pick"
                elif rank <= 72:
                    draft_rec = "third to fourth round pick"
                elif rank <= 96:
                    draft_rec = "middle round pick"
                else:
                    draft_rec = "late round or waiver wire pickup"
                
                elite_ranking_text = f"{player_name} has an elite fantasy score of {round(elite_fantasy_value, 2)}, with fantasy points per minute of {round(fppm, 3)}. His key capability is {key_strength}, making him a valuable fantasy asset. He is ranked #{rank} overall and falls in the {bucket_start}-{bucket_end} tier among all qualified NBA players. In a draft of {total_players} players, he should be considered a {draft_rec}. His ranking is based on his combination of efficiency (FPPM), playing time, and role importance on his team."
                
                # Store all stats for payload
                stats_dict = {
                    'age': row.get('Age', 0),
                    'games': games_played,
                    'games_started': games_started,
                    'minutes_per_game': minutes_per_game,
                    'points': row.get('PTS', 0),
                    'assists': row.get('AST', 0),
                    'rebounds': row.get('TRB', 0),
                    'steals': row.get('STL', 0),
                    'blocks': row.get('BLK', 0),
                    'turnovers': row.get('TOV', 0),
                    'field_goal_percentage': row.get('FG%', 0),
                    'three_point_percentage': row.get('3P%', 0),
                    'free_throw_percentage': row.get('FT%', 0)
                }

                document = {
                    'id': str(uuid.uuid4()),
                    'player_name': player_name,
                    'team': team_name,
                    'position': position,
                    'overall_rank': rank,
                    'bucket_range': f"{bucket_start}-{bucket_end}",
                    'stats_narrative': stats_text,  # Field 1: Stats-focused content (primary)
                    'expert_analysis': expert_text,  # Field 2: Expert analysis content (secondary)
                    'elite_ranking': elite_ranking_text,  # Field 3: Ranking/draft content (boosted)
                    'fantasy_points': round(fantasy_points, 2),
                    'fppm': round(fppm, 3),
                    'elite_fantasy_value': round(elite_fantasy_value, 3),
                    'games_played': games_played,
                    'games_started': games_started,
                    'minutes_per_game': round(minutes_per_game, 1),
                    'stats': stats_dict
                }
                
                documents.append(document)
                
            except Exception as e:
                logger.error(f"Error processing player {player_name}: {e}")
                continue
        
        logger.info(f"Prepared {len(documents)} documents with new structure (ranked 1-{len(documents)})")
        return documents

    def ingest_to_qdrant(self, documents):
        """Ingest documents into Qdrant vector database with new structure"""
        logger.info("Ingesting documents into Qdrant with new vectorization approach...")
        
        points = []
        for doc in tqdm(documents, desc="Creating embeddings"):
            try:
                # Create three separate embeddings for the three content fields
                # Field 1: Stats narrative (primary content - stats data)
                stats_embedding = self.model.encode(doc['stats_narrative']).tolist()
                
                # Field 2: Expert analysis (secondary content)
                expert_embedding = self.model.encode(doc['expert_analysis']).tolist()
                
                # Field 3: Elite ranking/draft content (boosted field)
                ranking_embedding = self.model.encode(doc['elite_ranking']).tolist()
                
                # Create combined embedding by weighing the different content types
                # Stats data: 60% (most important for answering questions)
                # Elite ranking: 30% (boosted for draft questions)
                # Expert analysis: 10% (supplementary context)
                combined_embedding = []
                for i in range(len(stats_embedding)):
                    combined_value = (
                        stats_embedding[i] * 0.6 +
                        ranking_embedding[i] * 0.3 +
                        expert_embedding[i] * 0.1
                    )
                    combined_embedding.append(combined_value)
                
                # Create point for Qdrant
                point = PointStruct(
                    id=doc['id'],
                    vector=combined_embedding,
                    payload={
                        'player_name': doc['player_name'],
                        'team': doc['team'],
                        'position': doc['position'],
                        'overall_rank': doc['overall_rank'],
                        'bucket_range': doc['bucket_range'],
                        'stats_narrative': doc['stats_narrative'],
                        'expert_analysis': doc['expert_analysis'],
                        'elite_ranking': doc['elite_ranking'],
                        'fantasy_points': doc['fantasy_points'],
                        'fppm': doc['fppm'],
                        'elite_fantasy_value': doc['elite_fantasy_value'],
                        'games_played': doc['games_played'],
                        'games_started': doc['games_started'],
                        'minutes_per_game': doc['minutes_per_game'],
                        'stats': doc['stats']
                    }
                )
                points.append(point)
                
            except Exception as e:
                logger.error(f"Error creating embedding for {doc['player_name']}: {e}")
                continue
        
        # Upload points in batches
        batch_size = 100
        for i in tqdm(range(0, len(points), batch_size), desc="Uploading to Qdrant"):
            batch = points[i:i+batch_size]
            self.client.upsert(
                collection_name=self.collection_name,
                points=batch
            )
        
        logger.info(f"Successfully ingested {len(points)} documents into Qdrant with new structure")

    def run_ingestion(self):
        """Run the complete data ingestion pipeline"""
        start_time = time.time()
        
        try:
            # Setup Qdrant collection
            self.setup_collection()
            
            # Scrape data from all sources
            logger.info("Scraping REAL NBA data from Basketball Reference...")
            stats_df = self.scrape_basketball_reference()
            
            if stats_df.empty:
                logger.error("CRITICAL: No real NBA data found from Basketball Reference. Cannot proceed.")
                raise Exception("Real NBA data scraping failed")
            
            logger.info(f"Successfully scraped {len(stats_df)} real NBA players")
            
            # Scrape expert analysis
            logger.info("Collecting expert analysis from external sources...")
            ringer_data = self.collect_ringer_data()
            hoopshype_data = self.scrape_hoopshype_rankings()
            
            # Log what we actually got
            logger.info(f"Ringer data: {len(ringer_data)} player analyses collected")
            logger.info(f"HoopsHype data: {len(hoopshype_data)} player analyses collected")
            
            # Prepare documents with real data (even if expert analysis is limited)
            documents = self.prepare_documents(stats_df, ringer_data, hoopshype_data)
            
            if not documents:
                logger.error("No documents prepared from real data. Cannot proceed.")
                raise Exception("Document preparation failed")
            
            # Calculate and display FPPM rankings
            self._display_fppm_rankings(documents)
            
            # Ingest to Qdrant
            self.ingest_to_qdrant(documents)
            
            # Save processing stats
            end_time = time.time()
            stats = {
                'total_players': len(documents),
                'ringer_analyses': len(ringer_data),
                'hoopshype_analyses': len(hoopshype_data),
                'processing_time_seconds': round(end_time - start_time, 2),
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'data_source': 'Real NBA data from Basketball Reference (NO MOCK DATA)'
            }
            
            # Save stats to file
            os.makedirs('data', exist_ok=True)
            with open('data/ingestion_stats.json', 'w') as f:
                json.dump(stats, f, indent=2)
            
            logger.info(f"Real data ingestion completed in {stats['processing_time_seconds']} seconds")
            logger.info(f"Ingestion stats: {stats}")
            
        except Exception as e:
            logger.error(f"Real data ingestion failed: {e}")
            raise

    def _display_fppm_rankings(self, documents):
        """Display FPPM rankings for all players with new structure"""
        logger.info("Displaying Elite Fantasy Value rankings...")
        
        # Documents are already sorted by elite fantasy value from prepare_documents
        print("\n" + "="*120)
        print("🏀 NBA PLAYERS RANKED BY ELITE FANTASY VALUE - TOP 50")
        print("="*120)
        print(f"{'Rank':<4} {'Player Name':<25} {'Elite Score':<12} {'FPPM':<6} {'Fantasy Pts':<12} {'Minutes':<8} {'Games':<6} {'Team':<5} {'Position':<8} {'Bucket':<10}")
        print("-" * 120)
        
        for i, doc in enumerate(documents[:50], 1):
            player = doc['player_name']
            elite_score = doc['elite_fantasy_value']
            fppm = doc['fppm']
            fantasy_points = doc['fantasy_points']
            minutes = doc['minutes_per_game']
            games = doc['games_played']
            team = doc['team']
            position = doc['position']
            bucket = doc['bucket_range']
            
            print(f"{i:<4} {player:<25} {elite_score:<12} {fppm:<6} {fantasy_points:<12} {minutes:<8} {games:<6} {team:<5} {position:<8} {bucket:<10}")
        
        print("-" * 120)
        print(f"Total players ranked: {len(documents)}")
        
        # Display elite players (Elite Score >= 1.0)
        elite_players = [d for d in documents if d['elite_fantasy_value'] >= 1.0]
        print(f"\n🌟 ELITE PLAYERS (Elite Score >= 1.0): {len(elite_players)}")
        for doc in elite_players:
            print(f"   {doc['player_name']}: {doc['elite_fantasy_value']} Elite Score (Rank #{doc['overall_rank']})")
        
        # Display tier breakdown
        print(f"\n📊 TIER BREAKDOWN:")
        tiers = {}
        for doc in documents:
            bucket = doc['bucket_range']
            if bucket not in tiers:
                tiers[bucket] = []
            tiers[bucket].append(doc['player_name'])
        
        for bucket in sorted(tiers.keys(), key=lambda x: int(x.split('-')[0])):
            players_in_tier = len(tiers[bucket])
            sample_players = ', '.join(tiers[bucket][:3])
            print(f"   Tier {bucket}: {players_in_tier} players (e.g., {sample_players})")
        
        print("="*120 + "\n")
        
        logger.info(f"Elite Fantasy Value Rankings complete: {len(documents)} players ranked, {len(elite_players)} elite players")

if __name__ == "__main__":
    ingestion = DataIngestion()
    ingestion.run_ingestion()
