#!/usr/bin/env python3
"""
Extract and display NBA players ranked by elite fantasy scores
"""

import json
import re

def extract_elite_score(elite_ranking_text):
    """Extract the elite fantasy score from the elite_ranking text."""
    if not elite_ranking_text:
        return 0.0
    
    # Look for patterns like "elite fantasy score of 1.29" or "elite fantasy score of 1.21"
    match = re.search(r'elite fantasy score of (\d+\.?\d*)', elite_ranking_text)
    if match:
        return float(match.group(1))
    
    # Fallback: look for FPPM value in the text
    match = re.search(r'fantasy points per minute of (\d+\.?\d*)', elite_ranking_text)
    if match:
        return float(match.group(1))
    
    return 0.0

def extract_elite_rankings():
    """Extract player names from the NBA players JSON file ranked by elite scores."""
    try:
        with open('nba_players_full.json', 'r') as f:
            players = json.load(f)
        
        # Extract elite scores and sort
        players_with_elite_scores = []
        for player in players:
            elite_text = player.get('elite_ranking', '')
            elite_score = extract_elite_score(elite_text)
            fppm = player.get('fppm', 0)
            
            # Use FPPM as fallback if elite score extraction fails
            final_score = elite_score if elite_score > 0 else fppm
            
            players_with_elite_scores.append({
                'name': player.get('name', 'Unknown'),
                'position': player.get('position', 'N/A'),
                'team': player.get('team', 'N/A'),
                'elite_score': final_score,
                'fppm': fppm,
                'fantasy_rank': player.get('fantasy_rank', 999),
                'elite_ranking': elite_text
            })
        
        # Sort by elite score (descending)
        sorted_players = sorted(players_with_elite_scores, key=lambda x: x['elite_score'], reverse=True)
        
        print("🌟 NBA ELITE FANTASY SCORE RANKINGS")
        print("=" * 70)
        print(f"Total Players: {len(sorted_players)}")
        print("Elite Score = Fantasy Points Per Minute (FPPM) efficiency rating")
        print("=" * 70)
        
        for i, player in enumerate(sorted_players, 1):
            name = player['name']
            position = player['position']
            team = player['team']
            elite_score = player['elite_score']
            fppm = player['fppm']
            fantasy_rank = player['fantasy_rank']
            
            print(f"{i:3d}. {name:<25} | {position:>2} | {team:>3} | Elite: {elite_score:.3f} | FPPM: {fppm:.3f} | Rank: #{fantasy_rank}")
        
        print("=" * 70)
        print(f"Complete elite score ranking of all {len(sorted_players)} NBA players")
        
        # Show top 20 for detailed view
        print("\n🏆 TOP 20 ELITE PERFORMERS:")
        print("-" * 50)
        for i, player in enumerate(sorted_players[:20], 1):
            print(f"{i:2d}. {player['name']:<20} | Elite: {player['elite_score']:.3f}")
        
        # Show some key players for verification
        print("\n🔍 KEY PLAYERS ELITE SCORES:")
        key_players = ['Pascal Siakam', 'Nikola Jokić', 'Giannis Antetokounmpo', 'LeBron James', 'Stephen Curry']
        for player in sorted_players:
            if player['name'] in key_players:
                print(f"  {player['name']}: Elite Score {player['elite_score']:.3f} (Fantasy Rank #{player['fantasy_rank']})")
        
    except FileNotFoundError:
        print("Error: nba_players_full.json file not found")
    except json.JSONDecodeError:
        print("Error: Invalid JSON format in nba_players_full.json")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    extract_elite_rankings()