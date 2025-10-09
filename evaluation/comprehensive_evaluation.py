"""
Comprehensive Evaluation Script - Standalone Testing and Analysis

This script provides comprehensive evaluation capabilities for development and testing.
Can be run independently to analyze retrieval quality, LLM responses, and embedding performance.

Purpose: Standalone evaluation script for comprehensive testing and benchmarking
Usage: Run directly as `python evaluation/comprehensive_evaluation.py`
Class: FantasyNBAEvaluator
"""

import json
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import logging
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
from rag import FantasyNBARag
import time

logger = logging.getLogger(__name__)

class FantasyNBAEvaluator:
    def __init__(self, groq_api_key: str = None):
        self.rag = FantasyNBARag(groq_api_key)
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Test queries and expected results for retrieval evaluation
        self.test_queries = [
            {
                "query": "Best point guards for fantasy basketball",
                "expected_positions": ["PG"],
                "expected_keywords": ["assists", "points", "fantasy"]
            },
            {
                "query": "Top scoring players in the NBA",
                "expected_keywords": ["points", "scoring", "offense"]
            },
            {
                "query": "Players with high fantasy points",
                "expected_keywords": ["fantasy", "points", "value"]
            },
            {
                "query": "Best centers for rebounds and blocks",
                "expected_positions": ["C"],
                "expected_keywords": ["rebounds", "blocks", "defense"]
            },
            {
                "query": "Efficient shooters with good three point percentage",
                "expected_keywords": ["shooting", "three", "efficiency", "percentage"]
            },
            {
                "query": "Players prone to turnovers",
                "expected_keywords": ["turnovers", "ball handling", "mistakes"]
            },
            {
                "query": "Most valuable fantasy basketball players",
                "expected_keywords": ["fantasy", "valuable", "points", "performance"]
            },
            {
                "query": "Rookies with high potential",
                "expected_keywords": ["rookie", "young", "potential", "development"]
            },
            {
                "query": "Players with injury concerns",
                "expected_keywords": ["injury", "health", "availability", "games"]
            },
            {
                "query": "Undervalued fantasy players",
                "expected_keywords": ["undervalued", "sleeper", "value", "draft"]
            }
        ]
        
        # Test queries for LLM evaluation
        self.llm_test_queries = [
            {
                "query": "Who should I draft first overall in fantasy basketball?",
                "expected_themes": ["top tier players", "consistent performance", "fantasy value"]
            },
            {
                "query": "Compare LeBron James and Stephen Curry for fantasy",
                "expected_themes": ["comparison", "strengths", "weaknesses", "fantasy impact"]
            },
            {
                "query": "What stats are most important for fantasy basketball?",
                "expected_themes": ["statistics", "fantasy scoring", "categories", "strategy"]
            },
            {
                "query": "Should I trade a point guard for a center?",
                "expected_themes": ["trade evaluation", "position needs", "value assessment"]
            },
            {
                "query": "Best waiver wire pickups this week",
                "expected_themes": ["available players", "opportunity", "short-term value"]
            }
        ]

    def evaluate_retrieval(self, num_results: int = 5) -> Dict[str, Any]:
        """
        Evaluate retrieval quality using test queries
        """
        logger.info("Starting retrieval evaluation...")
        
        results = {
            'total_queries': len(self.test_queries),
            'avg_relevance_score': 0,
            'position_accuracy': 0,
            'keyword_coverage': 0,
            'response_times': [],
            'detailed_results': []
        }
        
        total_relevance = 0
        position_matches = 0
        keyword_coverage_total = 0
        
        for i, test_case in enumerate(self.test_queries):
            start_time = time.time()
            
            # Perform search
            search_results = self.rag.search(test_case['query'], num_results)
            
            response_time = time.time() - start_time
            results['response_times'].append(response_time)
            
            # Evaluate relevance (using search scores)
            if search_results:
                avg_relevance = sum(r['score'] for r in search_results) / len(search_results)
                total_relevance += avg_relevance
                
                # Evaluate position accuracy
                if 'expected_positions' in test_case:
                    position_found = any(
                        any(pos in result['position'] for pos in test_case['expected_positions'])
                        for result in search_results
                    )
                    if position_found:
                        position_matches += 1
                
                # Evaluate keyword coverage
                if 'expected_keywords' in test_case:
                    found_keywords = 0
                    for keyword in test_case['expected_keywords']:
                        keyword_found = any(
                            keyword.lower() in result['text'].lower() or
                            keyword.lower() in result['expert_analysis'].lower()
                            for result in search_results
                        )
                        if keyword_found:
                            found_keywords += 1
                    
                    keyword_coverage = found_keywords / len(test_case['expected_keywords'])
                    keyword_coverage_total += keyword_coverage
                else:
                    keyword_coverage = 1.0  # If no expected keywords, assume full coverage
                    keyword_coverage_total += keyword_coverage
            else:
                avg_relevance = 0
                keyword_coverage = 0
            
            # Store detailed results
            results['detailed_results'].append({
                'query': test_case['query'],
                'num_results': len(search_results),
                'avg_relevance': avg_relevance,
                'keyword_coverage': keyword_coverage,
                'response_time': response_time,
                'top_players': [r['name'] for r in search_results[:3]] if search_results else []
            })
        
        # Calculate averages
        results['avg_relevance_score'] = total_relevance / len(self.test_queries)
        results['position_accuracy'] = position_matches / len([q for q in self.test_queries if 'expected_positions' in q])
        results['keyword_coverage'] = keyword_coverage_total / len(self.test_queries)
        results['avg_response_time'] = sum(results['response_times']) / len(results['response_times'])
        
        logger.info(f"Retrieval evaluation completed. Avg relevance: {results['avg_relevance_score']:.3f}")
        return results

    def evaluate_llm_responses(self) -> Dict[str, Any]:
        """
        Evaluate LLM response quality
        """
        logger.info("Starting LLM evaluation...")
        
        if not self.rag.groq_client:
            return {"error": "Groq API key not available for LLM evaluation"}
        
        results = {
            'total_queries': len(self.llm_test_queries),
            'avg_response_length': 0,
            'theme_coverage': 0,
            'response_times': [],
            'detailed_results': []
        }
        
        total_length = 0
        theme_coverage_total = 0
        
        for test_case in self.llm_test_queries:
            start_time = time.time()
            
            # Get RAG response
            response, search_results = self.rag.rag(test_case['query'])
            
            response_time = time.time() - start_time
            results['response_times'].append(response_time)
            
            # Evaluate response length
            response_length = len(response.split())
            total_length += response_length
            
            # Evaluate theme coverage
            themes_found = 0
            for theme in test_case['expected_themes']:
                if any(word in response.lower() for word in theme.split()):
                    themes_found += 1
            
            theme_coverage = themes_found / len(test_case['expected_themes'])
            theme_coverage_total += theme_coverage
            
            # Store detailed results
            results['detailed_results'].append({
                'query': test_case['query'],
                'response_length': response_length,
                'theme_coverage': theme_coverage,
                'response_time': response_time,
                'num_search_results': len(search_results),
                'response_preview': response[:200] + "..." if len(response) > 200 else response
            })
        
        # Calculate averages
        results['avg_response_length'] = total_length / len(self.llm_test_queries)
        results['theme_coverage'] = theme_coverage_total / len(self.llm_test_queries)
        results['avg_response_time'] = sum(results['response_times']) / len(results['response_times'])
        
        logger.info(f"LLM evaluation completed. Avg theme coverage: {results['theme_coverage']:.3f}")
        return results

    def evaluate_embedding_quality(self, sample_size: int = 50) -> Dict[str, Any]:
        """
        Evaluate the quality of embeddings and vector search
        """
        logger.info("Starting embedding evaluation...")
        
        # Get sample of players for embedding evaluation
        try:
            # Search for a broad query to get diverse players
            search_results = self.rag.search("NBA players statistics fantasy", num_results=sample_size)
            
            if len(search_results) < 2:
                return {"error": "Insufficient data for embedding evaluation"}
            
            # Create embeddings for player texts
            player_texts = [result['text'] for result in search_results]
            player_names = [result['name'] for result in search_results]
            
            embeddings = self.model.encode(player_texts)
            
            # Calculate similarity matrix
            similarity_matrix = cosine_similarity(embeddings)
            
            # Evaluate embedding quality metrics
            results = {
                'sample_size': len(search_results),
                'avg_similarity': 0,
                'similarity_variance': 0,
                'position_clustering': {},
                'similarity_distribution': []
            }
            
            # Calculate average similarity (excluding diagonal)
            upper_triangle = np.triu(similarity_matrix, k=1)
            non_zero_similarities = upper_triangle[upper_triangle > 0]
            
            results['avg_similarity'] = float(np.mean(non_zero_similarities))
            results['similarity_variance'] = float(np.var(non_zero_similarities))
            results['similarity_distribution'] = non_zero_similarities.tolist()
            
            # Evaluate position-based clustering
            position_groups = {}
            for i, result in enumerate(search_results):
                pos = result['position']
                if pos not in position_groups:
                    position_groups[pos] = []
                position_groups[pos].append(i)
            
            # Calculate intra-position similarity
            for pos, indices in position_groups.items():
                if len(indices) > 1:
                    intra_similarities = []
                    for i in range(len(indices)):
                        for j in range(i+1, len(indices)):
                            similarity = similarity_matrix[indices[i]][indices[j]]
                            intra_similarities.append(similarity)
                    
                    if intra_similarities:
                        results['position_clustering'][pos] = {
                            'avg_similarity': float(np.mean(intra_similarities)),
                            'count': len(indices)
                        }
            
            logger.info(f"Embedding evaluation completed. Avg similarity: {results['avg_similarity']:.3f}")
            return results
            
        except Exception as e:
            logger.error(f"Embedding evaluation failed: {e}")
            return {"error": str(e)}

    def run_comprehensive_evaluation(self) -> Dict[str, Any]:
        """
        Run all evaluation metrics and compile comprehensive report
        """
        logger.info("Starting comprehensive evaluation...")
        
        evaluation_results = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'retrieval_evaluation': {},
            'llm_evaluation': {},
            'embedding_evaluation': {},
            'overall_score': 0
        }
        
        try:
            # Run retrieval evaluation
            evaluation_results['retrieval_evaluation'] = self.evaluate_retrieval()
            
            # Run LLM evaluation (if API key available)
            evaluation_results['llm_evaluation'] = self.evaluate_llm_responses()
            
            # Run embedding evaluation
            evaluation_results['embedding_evaluation'] = self.evaluate_embedding_quality()
            
            # Calculate overall score (simple average of available metrics)
            scores = []
            
            # Retrieval score (average of relevance, keyword coverage, position accuracy)
            if 'avg_relevance_score' in evaluation_results['retrieval_evaluation']:
                retrieval_score = (
                    evaluation_results['retrieval_evaluation']['avg_relevance_score'] +
                    evaluation_results['retrieval_evaluation']['keyword_coverage'] +
                    evaluation_results['retrieval_evaluation']['position_accuracy']
                ) / 3
                scores.append(retrieval_score)
            
            # LLM score (theme coverage)
            if 'theme_coverage' in evaluation_results['llm_evaluation']:
                scores.append(evaluation_results['llm_evaluation']['theme_coverage'])
            
            # Embedding score (based on similarity metrics)
            if 'avg_similarity' in evaluation_results['embedding_evaluation']:
                # Normalize similarity score (0.7-0.9 similarity is good range)
                sim_score = max(0, min(1, (evaluation_results['embedding_evaluation']['avg_similarity'] - 0.5) * 2))
                scores.append(sim_score)
            
            if scores:
                evaluation_results['overall_score'] = sum(scores) / len(scores)
            
            # Save evaluation results
            import os
            os.makedirs('evaluation', exist_ok=True)
            
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            filename = f'evaluation/evaluation_results_{timestamp}.json'
            
            with open(filename, 'w') as f:
                json.dump(evaluation_results, f, indent=2)
            
            logger.info(f"Comprehensive evaluation completed. Overall score: {evaluation_results['overall_score']:.3f}")
            logger.info(f"Results saved to: {filename}")
            
            return evaluation_results
            
        except Exception as e:
            logger.error(f"Comprehensive evaluation failed: {e}")
            evaluation_results['error'] = str(e)
            return evaluation_results

if __name__ == "__main__":
    import os
    
    # Get API key from environment or prompt
    groq_api_key = os.getenv('GROQ_API_KEY')
    if not groq_api_key:
        groq_api_key = input("Enter your Groq API key (or press Enter to skip LLM evaluation): ").strip()
        if not groq_api_key:
            groq_api_key = None
    
    evaluator = FantasyNBAEvaluator(groq_api_key)
    results = evaluator.run_comprehensive_evaluation()
    
    print("\n" + "="*50)
    print("EVALUATION RESULTS SUMMARY")
    print("="*50)
    
    if 'error' not in results:
        print(f"Overall Score: {results['overall_score']:.3f}")
        
        if 'retrieval_evaluation' in results:
            ret_eval = results['retrieval_evaluation']
            print(f"\nRetrieval Metrics:")
            print(f"  - Average Relevance: {ret_eval.get('avg_relevance_score', 0):.3f}")
            print(f"  - Keyword Coverage: {ret_eval.get('keyword_coverage', 0):.3f}")
            print(f"  - Position Accuracy: {ret_eval.get('position_accuracy', 0):.3f}")
            print(f"  - Avg Response Time: {ret_eval.get('avg_response_time', 0):.3f}s")
        
        if 'llm_evaluation' in results and 'error' not in results['llm_evaluation']:
            llm_eval = results['llm_evaluation']
            print(f"\nLLM Metrics:")
            print(f"  - Theme Coverage: {llm_eval.get('theme_coverage', 0):.3f}")
            print(f"  - Avg Response Length: {llm_eval.get('avg_response_length', 0):.0f} words")
            print(f"  - Avg Response Time: {llm_eval.get('avg_response_time', 0):.3f}s")
        
        if 'embedding_evaluation' in results and 'error' not in results['embedding_evaluation']:
            emb_eval = results['embedding_evaluation']
            print(f"\nEmbedding Metrics:")
            print(f"  - Average Similarity: {emb_eval.get('avg_similarity', 0):.3f}")
            print(f"  - Similarity Variance: {emb_eval.get('similarity_variance', 0):.3f}")
            print(f"  - Sample Size: {emb_eval.get('sample_size', 0)}")
    else:
        print(f"Evaluation failed: {results['error']}")
    
    print("\n" + "="*50)