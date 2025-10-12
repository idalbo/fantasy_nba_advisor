#!/usr/bin/env python3
"""
Real-time monitoring module for Fantasy NBA Advisor
Tracks hit rates, response times, and query patterns
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from collections import defaultdict

class RealtimeMonitor:
    """Monitor system performance in real-time"""
    
    def __init__(self, log_file: str = "monitoring/realtime_metrics.jsonl"):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(exist_ok=True)
        
        # In-memory metrics for current session
        self.session_metrics = {
            'queries': 0,
            'total_response_time': 0,
            'hit_rates': [],
            'query_types': defaultdict(int),
            'errors': 0
        }
        
    def log_query(self, query: str, results: List[Dict], 
                  response_time: float, llm_response: Optional[str] = None,
                  expected_rank_range: Optional[tuple] = None):
        """
        Log a query with its results and calculate hit rate if expected range provided
        """
        # Extract ranks from results
        ranks_found = []
        for result in results[:10]:
            metadata = result.get('metadata', result)
            rank = (metadata.get('fantasy_rank') or 
                   metadata.get('overall_rank') or 
                   metadata.get('rank') or 999)
            ranks_found.append(rank)
        
        # Calculate hit rate if we have expected range
        hit_rate = None
        if expected_rank_range:
            min_rank, max_rank = expected_rank_range
            hits = sum(1 for r in ranks_found if min_rank <= r <= max_rank)
            hit_rate = (hits / len(ranks_found)) * 100 if ranks_found else 0
            self.session_metrics['hit_rates'].append(hit_rate)
        
        # Detect query type
        query_type = self._detect_query_type(query)
        self.session_metrics['query_types'][query_type] += 1
        
        # Update session metrics
        self.session_metrics['queries'] += 1
        self.session_metrics['total_response_time'] += response_time
        
        # Create log entry
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'query': query,
            'query_type': query_type,
            'ranks_found': ranks_found[:5],
            'best_rank': min(ranks_found) if ranks_found else 999,
            'hit_rate': hit_rate,
            'response_time': response_time,
            'num_results': len(results),
            'llm_response_length': len(llm_response) if llm_response else 0,
            'expected_range': expected_rank_range
        }
        
        # Append to log file
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
        
        return log_entry
    
    def log_error(self, query: str, error: str):
        """Log an error"""
        self.session_metrics['errors'] += 1
        
        error_entry = {
            'timestamp': datetime.now().isoformat(),
            'query': query,
            'error': str(error),
            'type': 'error'
        }
        
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(error_entry) + '\n')
    
    def _detect_query_type(self, query: str) -> str:
        """Detect the type of query"""
        query_lower = query.lower()
        
        if 'pick #' in query_lower or 'position' in query_lower:
            return 'draft_position'
        elif 'first round' in query_lower or 'second round' in query_lower:
            return 'round_query'
        elif 'elite' in query_lower or 'top' in query_lower or 'best' in query_lower:
            return 'elite_query'
        elif 'center' in query_lower or 'point guard' in query_lower or 'forward' in query_lower:
            return 'position_query'
        else:
            return 'general_query'
    
    def get_session_summary(self) -> Dict:
        """Get summary of current session metrics"""
        avg_response_time = (self.session_metrics['total_response_time'] / 
                           self.session_metrics['queries'] 
                           if self.session_metrics['queries'] > 0 else 0)
        
        avg_hit_rate = (sum(self.session_metrics['hit_rates']) / 
                       len(self.session_metrics['hit_rates'])
                       if self.session_metrics['hit_rates'] else None)
        
        return {
            'total_queries': self.session_metrics['queries'],
            'avg_response_time': round(avg_response_time, 2),
            'avg_hit_rate': round(avg_hit_rate, 1) if avg_hit_rate else None,
            'query_types': dict(self.session_metrics['query_types']),
            'errors': self.session_metrics['errors'],
            'timestamp': datetime.now().isoformat()
        }
    
    def print_session_summary(self):
        """Print a formatted session summary"""
        summary = self.get_session_summary()
        
        print("\n" + "=" * 70)
        print("📊 REAL-TIME MONITORING - SESSION SUMMARY")
        print("=" * 70)
        print(f"\n📈 Performance Metrics:")
        print(f"  Total Queries: {summary['total_queries']}")
        print(f"  Average Response Time: {summary['avg_response_time']}s")
        if summary['avg_hit_rate']:
            print(f"  Average Hit Rate: {summary['avg_hit_rate']}%")
        print(f"  Errors: {summary['errors']}")
        
        print(f"\n📋 Query Type Distribution:")
        for qtype, count in sorted(summary['query_types'].items(), 
                                   key=lambda x: x[1], reverse=True):
            pct = (count / summary['total_queries'] * 100) if summary['total_queries'] > 0 else 0
            print(f"  {qtype:20s}: {count:3d} ({pct:5.1f}%)")
        
        print(f"\n⏰ Session Time: {summary['timestamp']}")
        print("=" * 70)
    
    @staticmethod
    def analyze_logs(log_file: str = "monitoring/realtime_metrics.jsonl") -> Dict:
        """Analyze historical logs"""
        log_path = Path(log_file)
        if not log_path.exists():
            return {'error': 'No log file found'}
        
        metrics = {
            'total_queries': 0,
            'response_times': [],
            'hit_rates': [],
            'query_types': defaultdict(int),
            'errors': 0,
            'hourly_distribution': defaultdict(int)
        }
        
        with open(log_path, 'r') as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    
                    if entry.get('type') == 'error':
                        metrics['errors'] += 1
                        continue
                    
                    metrics['total_queries'] += 1
                    metrics['response_times'].append(entry.get('response_time', 0))
                    
                    if entry.get('hit_rate') is not None:
                        metrics['hit_rates'].append(entry['hit_rate'])
                    
                    qtype = entry.get('query_type', 'unknown')
                    metrics['query_types'][qtype] += 1
                    
                    # Extract hour from timestamp
                    timestamp = datetime.fromisoformat(entry['timestamp'])
                    hour = timestamp.hour
                    metrics['hourly_distribution'][hour] += 1
                    
                except json.JSONDecodeError:
                    continue
        
        # Calculate averages
        avg_response_time = (sum(metrics['response_times']) / len(metrics['response_times'])
                           if metrics['response_times'] else 0)
        avg_hit_rate = (sum(metrics['hit_rates']) / len(metrics['hit_rates'])
                       if metrics['hit_rates'] else None)
        
        return {
            'total_queries': metrics['total_queries'],
            'avg_response_time': round(avg_response_time, 2),
            'avg_hit_rate': round(avg_hit_rate, 1) if avg_hit_rate else None,
            'query_types': dict(metrics['query_types']),
            'errors': metrics['errors'],
            'hourly_distribution': dict(sorted(metrics['hourly_distribution'].items()))
        }
    
    @staticmethod
    def print_historical_analysis(log_file: str = "monitoring/realtime_metrics.jsonl"):
        """Print historical analysis"""
        analysis = RealtimeMonitor.analyze_logs(log_file)
        
        if 'error' in analysis:
            print(f"❌ {analysis['error']}")
            return
        
        print("\n" + "=" * 70)
        print("📚 HISTORICAL ANALYSIS")
        print("=" * 70)
        print(f"\n📊 All-Time Metrics:")
        print(f"  Total Queries: {analysis['total_queries']}")
        print(f"  Average Response Time: {analysis['avg_response_time']}s")
        if analysis['avg_hit_rate']:
            print(f"  Average Hit Rate: {analysis['avg_hit_rate']}%")
        print(f"  Total Errors: {analysis['errors']}")
        
        print(f"\n📋 Query Type Distribution:")
        for qtype, count in sorted(analysis['query_types'].items(),
                                   key=lambda x: x[1], reverse=True):
            pct = (count / analysis['total_queries'] * 100) if analysis['total_queries'] > 0 else 0
            print(f"  {qtype:20s}: {count:3d} ({pct:5.1f}%)")
        
        print(f"\n⏰ Hourly Query Distribution:")
        for hour, count in analysis['hourly_distribution'].items():
            bar = '█' * (count // 5 if count > 0 else 0)
            print(f"  {hour:02d}:00 | {bar} {count}")
        
        print("=" * 70)


# Example usage and testing
if __name__ == "__main__":
    print("🏀 Real-Time Monitoring System - Demo")
    print("=" * 70)
    
    # Create monitor
    monitor = RealtimeMonitor()
    
    # Simulate some queries
    print("\n📝 Simulating queries...")
    
    # Example 1: Draft position query
    mock_results = [
        {'metadata': {'name': 'Giannis', 'fantasy_rank': 2}},
        {'metadata': {'name': 'Jokić', 'fantasy_rank': 1}},
        {'metadata': {'name': 'Shai', 'fantasy_rank': 3}},
    ]
    monitor.log_query(
        query="who for pick #1?",
        results=mock_results,
        response_time=2.5,
        expected_rank_range=(1, 6)
    )
    
    # Example 2: General query
    mock_results2 = [
        {'metadata': {'name': 'LeBron', 'fantasy_rank': 10}},
        {'metadata': {'name': 'Curry', 'fantasy_rank': 21}},
    ]
    monitor.log_query(
        query="best point guards",
        results=mock_results2,
        response_time=1.8,
        expected_rank_range=(1, 50)
    )
    
    # Show session summary
    monitor.print_session_summary()
    
    # Show how to analyze historical data
    print("\n💡 To analyze historical logs, run:")
    print("    RealtimeMonitor.print_historical_analysis()")
