#!/usr/bin/env python3
"""
Extract and display all NBA player names in fantasy ranking order
"""

import json

def extract_player_rankings():
    """Extract player names from the NBA players JSON file in ranking order."""
    try:
        with open('nba_players_full.json', 'r') as f:
            players = json.load(f)
        
        # Sort by fantasy_rank to ensure proper order
        sorted_players = sorted(players, key=lambda x: x.get('fantasy_rank', 999))
        
        print("🏀 NBA PLAYER RANKINGS - COMPLETE LIST")
        print("=" * 60)
        print(f"Total Players: {len(sorted_players)}")
        print("=" * 60)
        
        for i, player in enumerate(sorted_players, 1):
            name = player.get('name', 'Unknown')
            position = player.get('position', 'N/A')
            team = player.get('team', 'N/A')
            fantasy_rank = player.get('fantasy_rank', 'N/A')
            fppm = player.get('fppm', 0)
            
            print(f"{i:3d}. {name:<25} | {position:>2} | {team:>3} | Rank: {fantasy_rank:>3} | FPPM: {fppm:.3f}")
        
        print("=" * 60)
        print(f"Complete ranking of all {len(sorted_players)} NBA players")
        
        # Show some key players for verification
        print("\n🔍 KEY PLAYERS VERIFICATION:")
        key_players = ['Pascal Siakam', 'Nikola Jokić', 'Giannis Antetokounmpo', 'LeBron James', 'Stephen Curry']
        for player in sorted_players:
            if player.get('name') in key_players:
                print(f"  {player.get('name')}: Rank #{player.get('fantasy_rank')}")
        
    except FileNotFoundError:
        print("Error: nba_players_full.json file not found")
    except json.JSONDecodeError:
        print("Error: Invalid JSON format in nba_players_full.json")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    extract_player_rankings()