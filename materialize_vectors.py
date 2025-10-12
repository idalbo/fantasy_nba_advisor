#!/usr/bin/env python3
"""
Script to materialize Qdrant vector database for fast loading in Streamlit Cloud.
This pre-computes all embeddings and saves them to disk.
"""

import json
import pickle
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer
from loguru import logger
import sys
import os

# Add src to path
sys.path.append('src')

def load_player_data():
    """Load NBA player data from JSON file"""
    try:
        with open('nba_players_full.json', 'r') as f:
            data = json.load(f)
            logger.info(f"✅ Loaded {len(data)} players from nba_players_full.json")
            return data
    except FileNotFoundError:
        logger.error("❌ nba_players_full.json not found")
        return []
    except Exception as e:
        logger.error(f"❌ Error loading player data: {e}")
        return []

def build_draft_context(rank: int, fppm: float, position: str) -> str:
    """Build rich draft position context for better vector search retrieval"""
    if rank == 999:
        return "Late round sleeper or waiver wire option."
    
    # Elite tier (Ranks 1-10)
    if rank <= 10:
        tier = "ELITE FIRST ROUND PICK"
        desc = f"Top {rank} fantasy player. Should go in picks 1-10 of any draft. Premium first round selection."
        if rank <= 3:
            desc += " Consensus top 3 pick. Absolute elite tier."
        elif rank <= 6:
            desc += " Core first round target."
    
    # First round (Ranks 11-30)
    elif rank <= 30:
        tier = "FIRST ROUND VALUE"
        desc = f"Ranked #{rank}. Excellent first round pick around picks {rank-5} to {rank+5}. Solid fantasy starter."
        if position in ['C', 'PF']:
            desc += f" Strong {position} option for positional scarcity."
    
    # Second/Third round (Ranks 31-50)
    elif rank <= 50:
        tier = "EARLY MID-ROUND"
        desc = f"Ranked #{rank}. Great 2nd/3rd round value around picks {rank-5} to {rank+5}. Quality starter material."
    
    # Mid rounds (Ranks 51-100)
    elif rank <= 100:
        tier = "MID-ROUND PICK"
        desc = f"Ranked #{rank}. Solid middle round option around picks {rank-10} to {rank+10}. Good bench depth or flex starter."
    
    # Late rounds (Ranks 101-200)
    elif rank <= 200:
        tier = "LATE ROUND VALUE"
        desc = f"Ranked #{rank}. Late round pick around {rank-15} to {rank+15}. Deep league option or streaming candidate."
    else:
        tier = "DEEP SLEEPER"
        desc = f"Ranked #{rank}. Very late pick or waiver wire target. Speculative add."
    
    # Add FPPM context
    if fppm >= 1.0:
        efficiency = "Elite efficiency (1+ FPPM)."
    elif fppm >= 0.85:
        efficiency = "Excellent efficiency (0.85+ FPPM)."
    elif fppm >= 0.70:
        efficiency = "Good efficiency (0.70+ FPPM)."
    else:
        efficiency = "Lower efficiency for the rank."
    
    return f"{tier}: {desc} {efficiency}"

def create_materialized_embeddings():
    """Create and save materialized embeddings for fast loading"""
    logger.info("🚀 Starting materialization of Qdrant vector database...")
    
    # Initialize embedding model
    logger.info("📦 Loading sentence transformer model...")
    embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Load player data
    player_data = load_player_data()
    if not player_data:
        logger.error("❌ No player data to process")
        return False
    
    # Create embeddings
    logger.info(f"🧮 Computing embeddings for {len(player_data)} players...")
    embeddings = []
    processed_data = []
    
    for i, player in enumerate(player_data):
        # Create enriched searchable text with draft context
        rank = player.get('fantasy_rank', player.get('overall_rank', 999))
        fppm = player.get('fppm', 0)
        position = player.get('position', '')
        
        # Build draft position context
        draft_context = build_draft_context(rank, fppm, position)
        
        # Create searchable text (same as in RAG class)
        text = f"{player.get('player_name', '')} {position} {player.get('team', '')} "
        text += f"Fantasy Rank #{rank}. {draft_context} "
        text += f"{player.get('expert_analysis', '')} {player.get('stats_narrative', '')}"
        
        # Create embedding
        embedding = embedding_model.encode(text)
        embeddings.append(embedding)
        processed_data.append(player)
        
        if (i + 1) % 50 == 0:
            logger.info(f"📊 Processed {i + 1}/{len(player_data)} players...")
    
    # Convert to numpy array for efficient storage
    embeddings_array = np.array(embeddings)
    
    # Create data directory if it doesn't exist
    data_dir = Path('data')
    data_dir.mkdir(exist_ok=True)
    
    # Save embeddings and metadata
    embeddings_file = data_dir / 'player_embeddings.pkl'
    metadata_file = data_dir / 'player_metadata.json'
    
    logger.info("💾 Saving materialized data...")
    
    # Save embeddings as pickle (efficient for numpy arrays)
    with open(embeddings_file, 'wb') as f:
        pickle.dump({
            'embeddings': embeddings_array,
            'embedding_model': 'all-MiniLM-L6-v2',
            'vector_size': embeddings_array.shape[1],
            'num_players': len(processed_data)
        }, f)
    
    # Save metadata as JSON
    with open(metadata_file, 'w') as f:
        json.dump(processed_data, f, indent=2)
    
    logger.info(f"✅ Materialized vector database saved:")
    logger.info(f"   📁 Embeddings: {embeddings_file} ({embeddings_array.nbytes / 1024 / 1024:.1f} MB)")
    logger.info(f"   📁 Metadata: {metadata_file}")
    logger.info(f"   🔢 Vector size: {embeddings_array.shape[1]}")
    logger.info(f"   👥 Players: {len(processed_data)}")
    
    return True

def test_materialized_data():
    """Test loading the materialized data"""
    logger.info("🧪 Testing materialized data loading...")
    
    data_dir = Path('data')
    embeddings_file = data_dir / 'player_embeddings.pkl'
    metadata_file = data_dir / 'player_metadata.json'
    
    if not embeddings_file.exists() or not metadata_file.exists():
        logger.error("❌ Materialized data files not found")
        return False
    
    try:
        # Load embeddings
        with open(embeddings_file, 'rb') as f:
            embedding_data = pickle.load(f)
        
        # Load metadata
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        logger.info(f"✅ Successfully loaded materialized data:")
        logger.info(f"   🔢 Embeddings shape: {embedding_data['embeddings'].shape}")
        logger.info(f"   👥 Players: {len(metadata)}")
        logger.info(f"   📊 Model: {embedding_data['embedding_model']}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error loading materialized data: {e}")
        return False

if __name__ == "__main__":
    logger.info("🏀 Fantasy NBA Advisor - Vector Database Materialization")
    logger.info("=" * 60)
    
    # Create materialized embeddings
    if create_materialized_embeddings():
        logger.info("✅ Materialization completed successfully!")
        
        # Test loading
        if test_materialized_data():
            logger.info("✅ Materialized data verified!")
            logger.info("🚀 Ready for fast Streamlit Cloud deployment!")
        else:
            logger.error("❌ Materialized data verification failed")
            sys.exit(1)
    else:
        logger.error("❌ Materialization failed")
        sys.exit(1)