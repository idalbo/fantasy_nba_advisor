import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import logging
from typing import Dict, List, Any
import time

logger = logging.getLogger(__name__)

class FantasyNBAMonitor:
    def __init__(self):
        self.monitoring_dir = 'monitoring'
        os.makedirs(self.monitoring_dir, exist_ok=True)
    
    def load_interactions(self, days_back: int = 7) -> List[Dict[str, Any]]:
        """Load interaction logs from the past N days"""
        interactions = []
        
        for i in range(days_back):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            filename = os.path.join(self.monitoring_dir, f'interactions_{date}.jsonl')
            
            if os.path.exists(filename):
                try:
                    with open(filename, 'r') as f:
                        for line in f:
                            interaction = json.loads(line.strip())
                            interaction['date'] = date
                            interactions.append(interaction)
                except Exception as e:
                    logger.error(f"Error loading {filename}: {e}")
        
        return interactions
    
    def generate_monitoring_report(self, days_back: int = 7) -> Dict[str, Any]:
        """Generate comprehensive monitoring report"""
        interactions = self.load_interactions(days_back)
        
        if not interactions:
            return {'error': 'No interaction data found'}
        
        # Basic statistics
        total_queries = len(interactions)
        unique_users = len(set(i.get('user_id', 'anonymous') for i in interactions))
        
        # Query analysis
        query_lengths = [len(i['query'].split()) for i in interactions]
        avg_query_length = np.mean(query_lengths) if query_lengths else 0
        
        # Response analysis
        response_times = [i.get('response_time', 0) for i in interactions if 'response_time' in i]
        avg_response_time = np.mean(response_times) if response_times else 0
        
        # Feedback analysis
        feedback_data = [i for i in interactions if i.get('feedback')]
        positive_feedback = len([i for i in feedback_data if '👍' in i.get('feedback', '')])
        negative_feedback = len([i for i in feedback_data if '👎' in i.get('feedback', '')])
        
        # Most popular queries
        query_words = []
        for interaction in interactions:
            query_words.extend(interaction['query'].lower().split())
        
        word_counts = pd.Series(query_words).value_counts().head(10)
        
        # Daily usage patterns
        daily_counts = {}
        for interaction in interactions:
            date = interaction.get('date', 'unknown')
            daily_counts[date] = daily_counts.get(date, 0) + 1
        
        # Hour-based usage patterns
        hourly_counts = {}
        for interaction in interactions:
            try:
                hour = datetime.fromisoformat(interaction['timestamp']).hour
                hourly_counts[hour] = hourly_counts.get(hour, 0) + 1
            except:
                continue
        
        # Most searched players
        all_players = []
        for interaction in interactions:
            all_players.extend(interaction.get('top_players', []))
        
        player_counts = pd.Series(all_players).value_counts().head(10) if all_players else pd.Series()
        
        report = {
            'report_timestamp': datetime.now().isoformat(),
            'period_days': days_back,
            'basic_metrics': {
                'total_queries': total_queries,
                'unique_users': unique_users,
                'avg_query_length_words': round(avg_query_length, 2),
                'avg_response_time_seconds': round(avg_response_time, 3)
            },
            'feedback_metrics': {
                'total_feedback': len(feedback_data),
                'positive_feedback': positive_feedback,
                'negative_feedback': negative_feedback,
                'feedback_rate': round(len(feedback_data) / total_queries * 100, 2) if total_queries > 0 else 0,
                'satisfaction_rate': round(positive_feedback / len(feedback_data) * 100, 2) if feedback_data else 0
            },
            'usage_patterns': {
                'daily_counts': daily_counts,
                'hourly_counts': hourly_counts,
                'peak_hour': max(hourly_counts.keys(), key=lambda k: hourly_counts[k]) if hourly_counts else None
            },
            'content_insights': {
                'top_query_words': word_counts.to_dict() if not word_counts.empty else {},
                'most_searched_players': player_counts.to_dict() if not player_counts.empty else {}
            },
            'performance_metrics': {
                'response_time_distribution': {
                    'p50': np.percentile(response_times, 50) if response_times else 0,
                    'p90': np.percentile(response_times, 90) if response_times else 0,
                    'p95': np.percentile(response_times, 95) if response_times else 0
                }
            }
        }
        
        return report
    
    def save_monitoring_report(self, report: Dict[str, Any]) -> str:
        """Save monitoring report to file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = os.path.join(self.monitoring_dir, f'monitoring_report_{timestamp}.json')
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        return filename
    
    def check_system_health(self) -> Dict[str, Any]:
        """Check system health metrics"""
        health_status = {
            'timestamp': datetime.now().isoformat(),
            'database_connection': False,
            'recent_activity': False,
            'error_rate': 0,
            'avg_response_time': 0,
            'recommendations': []
        }
        
        # Check for recent interactions (last 24 hours)
        recent_interactions = self.load_interactions(days_back=1)
        
        if recent_interactions:
            health_status['recent_activity'] = True
            
            # Calculate error rate - look for actual error patterns, not just word "error"
            errors = []
            for i in recent_interactions:
                response = i.get('response', '')
                # Check for actual error patterns
                if (response.startswith('❌ Error:') or 
                    response.startswith('Error generating response:') or
                    'Error code:' in response or
                    'Exception' in response):
                    errors.append(i)
            
            health_status['error_rate'] = len(errors) / len(recent_interactions) * 100
            
            # Calculate average response time
            response_times = [i.get('response_time', 0) for i in recent_interactions if 'response_time' in i]
            health_status['avg_response_time'] = np.mean(response_times) if response_times else 0
        
        # Generate recommendations
        if health_status['error_rate'] > 10:
            health_status['recommendations'].append("High error rate detected. Check system logs.")
        
        if health_status['avg_response_time'] > 5:
            health_status['recommendations'].append("Slow response times. Consider optimizing queries.")
        
        if not health_status['recent_activity']:
            health_status['recommendations'].append("No recent activity. Check if application is accessible.")
        
        return health_status
    
    def export_metrics_for_phoenix(self) -> Dict[str, Any]:
        """Export metrics in format suitable for Phoenix monitoring"""
        interactions = self.load_interactions(days_back=30)
        
        if not interactions:
            return {'error': 'No data available'}
        
        # Convert to format suitable for Phoenix
        phoenix_data = {
            'traces': [],
            'evaluations': [],
            'metadata': {
                'application': 'fantasy-nba-advisor',
                'version': '1.0.0',
                'export_timestamp': datetime.now().isoformat()
            }
        }
        
        for interaction in interactions:
            trace = {
                'trace_id': interaction.get('trace_id', f"trace_{hash(interaction['timestamp'])}"),
                'span_id': f"span_{hash(interaction['query'])}",
                'timestamp': interaction['timestamp'],
                'input': interaction['query'],
                'output': interaction.get('response', ''),
                'metadata': {
                    'num_results': interaction.get('num_results', 0),
                    'top_players': interaction.get('top_players', []),
                    'feedback': interaction.get('feedback')
                },
                'latency_ms': interaction.get('response_time', 0) * 1000
            }
            phoenix_data['traces'].append(trace)
            
            # Add evaluation if feedback is available
            if interaction.get('feedback'):
                evaluation = {
                    'trace_id': trace['trace_id'],
                    'name': 'user_feedback',
                    'label': 'positive' if '👍' in interaction['feedback'] else 'negative',
                    'score': 1.0 if '👍' in interaction['feedback'] else 0.0
                }
                phoenix_data['evaluations'].append(evaluation)
        
        return phoenix_data

def main():
    """Main monitoring function"""
    monitor = FantasyNBAMonitor()
    
    # Generate and save monitoring report
    report = monitor.generate_monitoring_report(days_back=7)
    
    if 'error' not in report:
        filename = monitor.save_monitoring_report(report)
        print(f"Monitoring report saved to: {filename}")
        
        # Print summary
        print("\n" + "="*50)
        print("MONITORING REPORT SUMMARY")
        print("="*50)
        print(f"Total Queries: {report['basic_metrics']['total_queries']}")
        print(f"Feedback Rate: {report['feedback_metrics']['feedback_rate']:.1f}%")
        print(f"Satisfaction Rate: {report['feedback_metrics']['satisfaction_rate']:.1f}%")
        print(f"Avg Response Time: {report['basic_metrics']['avg_response_time_seconds']:.3f}s")
        
        if report['content_insights']['most_searched_players']:
            print(f"\nTop Players:")
            for player, count in list(report['content_insights']['most_searched_players'].items())[:5]:
                print(f"  - {player}: {count} searches")
    else:
        print(f"Error generating report: {report['error']}")
    
    # Check system health
    health = monitor.check_system_health()
    print(f"\nSystem Health: {'✅ Good' if not health['recommendations'] else '⚠️ Issues Detected'}")
    
    if health['recommendations']:
        print("Recommendations:")
        for rec in health['recommendations']:
            print(f"  - {rec}")

if __name__ == "__main__":
    main()