#!/usr/bin/env python3
"""
Display comprehensive NBA player rankings with both elite scores and fantasy rankings
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

def comprehensive_rankings():
    """Display comprehensive rankings with both elite scores and fantasy rankings."""
    try:
        with open('nba_players_full.json', 'r') as f:
            players = json.load(f)
        
        # Process players with both rankings
        comprehensive_data = []
        for player in players:
            elite_text = player.get('elite_ranking', '')
            elite_score = extract_elite_score(elite_text)
            fppm = player.get('fppm', 0)
            
            # Use FPPM as fallback if elite score extraction fails
            final_elite_score = elite_score if elite_score > 0 else fppm
            
            comprehensive_data.append({
                'name': player.get('name', 'Unknown'),
                'position': player.get('position', 'N/A'),
                'team': player.get('team', 'N/A'),
                'fantasy_rank': player.get('fantasy_rank', 999),
                'elite_score': final_elite_score,
                'fppm': fppm,
                'fantasy_points': player.get('fantasy_points', 0),
                'minutes_per_game': player.get('minutes_per_game', 0),
                'elite_ranking': elite_text
            })
        
        # Sort by fantasy rank (primary) for consistent ordering
        sorted_by_fantasy = sorted(comprehensive_data, key=lambda x: x['fantasy_rank'])
        
        # Also create elite score ranking
        sorted_by_elite = sorted(comprehensive_data, key=lambda x: x['elite_score'], reverse=True)
        
        print("🏀 COMPREHENSIVE NBA PLAYER RANKINGS")
        print("=" * 100)
        print(f"Total Players: {len(sorted_by_fantasy)}")
        print("Fantasy Rank = Overall fantasy basketball ranking (1-450)")
        print("Elite Score = Fantasy Points Per Minute efficiency rating")
        print("=" * 100)
        
        # Create elite ranking lookup
        elite_rank_lookup = {player['name']: idx + 1 for idx, player in enumerate(sorted_by_elite)}
        
        print(f"{'Rank':<4} {'Name':<25} {'Pos':<3} {'Team':<4} {'Elite Rank':<10} {'Elite Score':<11} {'FPPM':<6} {'FP/G':<6} {'MPG':<5}")
        print("-" * 100)
        
        for player in sorted_by_fantasy:
            name = player['name']
            position = player['position']
            team = player['team']
            fantasy_rank = player['fantasy_rank']
            elite_score = player['elite_score']
            fppm = player['fppm']
            fantasy_points = player['fantasy_points']
            minutes = player['minutes_per_game']
            
            # Get elite ranking position
            elite_rank = elite_rank_lookup.get(name, 'N/A')
            
            print(f"{fantasy_rank:<4} {name:<25} {position:<3} {team:<4} #{elite_rank:<9} {elite_score:<11.3f} {fppm:<6.3f} {fantasy_points:<6.1f} {minutes:<5.1f}")
        
        print("=" * 100)
        
        # Summary statistics
        print("\n📊 RANKING COMPARISON ANALYSIS:")
        print("-" * 50)
        
        # Top performers in both rankings
        top_fantasy = sorted_by_fantasy[:20]
        top_elite = sorted_by_elite[:20]
        
        # Find players in both top 20s
        top_fantasy_names = {p['name'] for p in top_fantasy}
        top_elite_names = {p['name'] for p in top_elite}
        both_top_20 = top_fantasy_names.intersection(top_elite_names)
        
        print(f"Players in BOTH Top 20 Fantasy & Elite Rankings: {len(both_top_20)}")
        for name in sorted(both_top_20):
            player_data = next(p for p in sorted_by_fantasy if p['name'] == name)
            elite_rank = elite_rank_lookup[name]
            print(f"  • {name}: Fantasy #{player_data['fantasy_rank']}, Elite #{elite_rank}")
        
        # Biggest discrepancies
        print(f"\n🔍 BIGGEST RANKING DISCREPANCIES:")
        print("-" * 40)
        discrepancies = []
        for player in sorted_by_fantasy:
            name = player['name']
            fantasy_rank = player['fantasy_rank']
            elite_rank = elite_rank_lookup.get(name, 999)
            if isinstance(elite_rank, int):
                diff = abs(fantasy_rank - elite_rank)
                discrepancies.append((name, fantasy_rank, elite_rank, diff))
        
        # Sort by biggest discrepancy
        discrepancies.sort(key=lambda x: x[3], reverse=True)
        
        print("Top 10 players with biggest ranking differences:")
        for i, (name, f_rank, e_rank, diff) in enumerate(discrepancies[:10], 1):
            direction = "Elite Higher" if e_rank < f_rank else "Fantasy Higher"
            print(f"{i:2d}. {name:<22} Fantasy: #{f_rank:<3} Elite: #{e_rank:<3} Diff: {diff:<3} ({direction})")
        
        # Key players verification
        print(f"\n🎯 KEY PLAYERS VERIFICATION:")
        print("-" * 30)
        key_players = ['Pascal Siakam', 'Nikola Jokić', 'Giannis Antetokounmpo', 'LeBron James', 'Stephen Curry']
        for name in key_players:
            player_data = next((p for p in sorted_by_fantasy if p['name'] == name), None)
            if player_data:
                elite_rank = elite_rank_lookup.get(name, 'N/A')
                print(f"{name}: Fantasy #{player_data['fantasy_rank']}, Elite #{elite_rank}, Elite Score: {player_data['elite_score']:.3f}")
        
    except FileNotFoundError:
        print("Error: nba_players_full.json file not found")
    except json.JSONDecodeError:
        print("Error: Invalid JSON format in nba_players_full.json")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    comprehensive_rankings()