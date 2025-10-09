#!/usr/bin/env python3
"""
Fantasy NBA Advisor - Main Entry Point

This script provides a simple interface to run different components of the
Fantasy NBA Advisor application.

Usage:
    python main.py --help
    python main.py ingest    # Run data ingestion
    python main.py app       # Run Streamlit app
    python main.py evaluate  # Run evaluation
    python main.py monitor   # Run monitoring
"""

import argparse
import sys
import os

def run_data_ingestion():
    """Run the data ingestion pipeline"""
    print("🚀 Starting data ingestion...")
    sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
    from src.data_ingestion import DataIngestion
    
    ingestion = DataIngestion()
    ingestion.run_ingestion()
    print("✅ Data ingestion completed!")

def run_streamlit_app():
    """Run the Streamlit application"""
    print("🚀 Starting Streamlit application...")
    import subprocess
    subprocess.run([
        "streamlit", "run", "streamlit_app.py", 
        "--server.address", "0.0.0.0", 
        "--server.port", "8501"
    ])

def run_evaluation():
    """Run the evaluation pipeline"""
    print("🚀 Starting evaluation...")
    sys.path.append(os.path.join(os.path.dirname(__file__), 'evaluation'))
    
    groq_api_key = os.getenv('GROQ_API_KEY')
    if not groq_api_key:
        groq_api_key = input("Enter your Groq API key (or press Enter to skip LLM evaluation): ").strip()
        if not groq_api_key:
            groq_api_key = None
    
    from evaluation.evaluate import FantasyNBAEvaluator
    evaluator = FantasyNBAEvaluator(groq_api_key)
    results = evaluator.run_comprehensive_evaluation()
    
    print(f"✅ Evaluation completed! Overall score: {results.get('overall_score', 'N/A')}")

def run_monitoring():
    """Run the monitoring report"""
    print("🚀 Generating monitoring report...")
    sys.path.append(os.path.join(os.path.dirname(__file__), 'monitoring'))
    from monitor import main as monitor_main
    
    monitor_main()
    print("✅ Monitoring report generated!")

def main():
    parser = argparse.ArgumentParser(
        description="Fantasy NBA Advisor - AI-powered fantasy basketball insights"
    )
    
    parser.add_argument(
        'command',
        choices=['ingest', 'app', 'evaluate', 'monitor'],
        help='Command to run'
    )
    
    args = parser.parse_args()
    
    if args.command == 'ingest':
        run_data_ingestion()
    elif args.command == 'app':
        run_streamlit_app()
    elif args.command == 'evaluate':
        run_evaluation()
    elif args.command == 'monitor':
        run_monitoring()

if __name__ == "__main__":
    main()