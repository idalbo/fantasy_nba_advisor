#!/usr/bin/env python3
"""
Export NBA player data from Qdrant to JSON for Streamlit Cloud deployment
"""
import json
import os
import sys
from qdrant_client import QdrantClient
from typing import List, Dict, Any

def export_qdrant_data():
    """Export all NBA player data from Qdrant to JSON file"""
    
    # Connect to Qdrant
    qdrant_host = os.getenv('QDRANT_HOST', 'localhost')
    qdrant_port = int(os.getenv('QDRANT_PORT', 6333))
    
    try:
        client = QdrantClient(host=qdrant_host, port=qdrant_port)
        print(f"Connected to Qdrant at {qdrant_host}:{qdrant_port}")
        
        # Get all points from the collection
        collection_name = 'nba_players'
        
        # Scroll through all points
        points = []
        offset = None
        limit = 100
        
        while True:
            result = client.scroll(
                collection_name=collection_name,
                limit=limit,
                offset=offset,
                with_payload=True,
                with_vectors=False  # We don't need vectors for cloud deployment
            )
            
            if not result[0]:  # No more points
                break
                
            points.extend(result[0])
            offset = result[1]  # Next offset
            
            print(f"Exported {len(points)} players so far...")
            
            if offset is None:  # No more data
                break
        
        # Convert to JSON-serializable format
        export_data = []
        for point in points:
            payload = point.payload
            
            # Ensure all required fields for cloud compatibility
            player_data = {
                "id": str(point.id),
                "player_name": payload.get("name", "Unknown"),
                "name": payload.get("name", "Unknown"),  # For chart compatibility
                "position": payload.get("position", "N/A"),
                "team": payload.get("team", "N/A"),
                "fppm": float(payload.get("fppm", 0)),
                "fantasy_points": float(payload.get("fantasy_points", payload.get("fppm", 0) * 35)),  # Estimate FP from FPPM
                "fantasy_rank": int(payload.get("fantasy_rank", 999)),
                "stats_narrative": payload.get("stats_narrative", "NBA player statistics"),
                "expert_analysis": payload.get("expert_analysis", "Professional basketball player"),
                "elite_ranking": payload.get("elite_ranking", f"Rank {payload.get('fantasy_rank', 'Unknown')}"),
                "injury_status": payload.get("injury_status", "Healthy"),
                "recent_performance": payload.get("recent_performance", "Consistent performance"),
                "matchup_analysis": payload.get("matchup_analysis", "Standard matchup expectations"),
                # Additional fields that might be useful
                "overall_rank": payload.get("overall_rank"),
                "ringer_rank": payload.get("ringer_rank"),
                "hoopshype_rank": payload.get("hoopshype_rank"),
                "salary": payload.get("salary"),
                "minutes_per_game": payload.get("minutes_per_game"),
                "usage_rate": payload.get("usage_rate"),
            }
            
            export_data.append(player_data)
        
        # Sort by fantasy rank
        export_data.sort(key=lambda x: x['fantasy_rank'])
        
        # Save to JSON file
        output_file = 'nba_players_full.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Successfully exported {len(export_data)} NBA players to {output_file}")
        print(f"📊 Data includes: player info, stats, rankings, analysis, and more")
        print(f"🚀 Ready for Streamlit Cloud deployment!")
        
        return export_data
        
    except Exception as e:
        print(f"❌ Error exporting data: {e}")
        return None

if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    export_qdrant_data()