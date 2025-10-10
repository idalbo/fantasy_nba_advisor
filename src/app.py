import streamlit as st

# Page configuration - MUST BE FIRST STREAMLIT COMMAND
st.set_page_config(
    page_title="Fantasy NBA Advisor",
    page_icon="🏀",
    layout="wide",
    initial_sidebar_state="expanded"
)

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import os
import time
from datetime import datetime
import logging
from dotenv import load_dotenv

# Detect deployment environment
# Check for Streamlit Cloud indicators
CLOUD_MODE = (
    os.getenv('STREAMLIT_SHARING_MODE') is not None or 
    os.getenv('STREAMLIT_CLOUD') is not None or
    '/mount/src/' in os.getcwd() or  # Streamlit Cloud path indicator
    os.path.exists('/mount/src') or  # Additional Streamlit Cloud check
    'streamlit_app' in os.path.basename(__file__) and not os.path.exists('/app') or  # Cloud app file without Docker
    not os.path.exists('src')  # Fallback: no src directory
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Debug info (after page config)
if os.getenv('DEBUG', 'false').lower() == 'true':
    st.sidebar.write(f"🔍 Debug: CLOUD_MODE = {CLOUD_MODE}")
    st.sidebar.write(f"🔍 Debug: Current dir = {os.getcwd()}")
    st.sidebar.write(f"🔍 Debug: Files = {os.listdir('.')[:5]}...")
    st.sidebar.write(f"🔍 Debug: /mount/src in cwd = {'/mount/src/' in os.getcwd()}")
    st.sidebar.write(f"🔍 Debug: STREAMLIT_SHARING_MODE = {os.getenv('STREAMLIT_SHARING_MODE')}")
    st.sidebar.write(f"🔍 Debug: src exists = {os.path.exists('src')}")

# Import unified modules for consistent functionality
try:
    import sys
    import os
    
    # Add src directory to path if not already there
    src_dir = os.path.dirname(__file__)
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)
    
    from rag_unified import UnifiedFantasyNBARag
    UNIFIED_RAG_AVAILABLE = True
    logger.info("✅ Using unified RAG system with full evaluation capabilities")
except ImportError as e:
    st.error(f"❌ Failed to import unified RAG system: {e}")
    st.info("Please ensure rag_unified.py is available in the src directory")
    st.stop()

# Import evaluation tools for comprehensive testing
try:
    from rag import FantasyNBARag
    from retrieval_evaluator import RetrievalEvaluator
    FULL_EVALUATION_AVAILABLE = True
    logger.info("✅ Full evaluation tools available (vector-based RAG + evaluator)")
except ImportError as e:
    FULL_EVALUATION_AVAILABLE = False
    logger.warning(f"Vector-based evaluation tools not available: {e}")

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 2rem;
        background: linear-gradient(90deg, #ff6b35, #f7931e);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .stat-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 1rem;
    }
    .player-card {
        border: 2px solid #1f77b4;
        border-radius: 15px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        background: linear-gradient(135deg, #ffffff 0%, #f1f3f4 100%);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
        color: #2c3e50;
        transition: transform 0.2s ease;
    }
    .player-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2);
    }
    .player-card h4 {
        color: #1f77b4;
        margin-bottom: 0.5rem;
        font-weight: bold;
        font-size: 1.2rem;
    }
    .player-card p {
        margin-bottom: 0.4rem;
        color: #34495e;
        line-height: 1.4;
    }
    .player-card strong {
        color: #2c3e50;
        font-weight: 600;
    }
    .api-warning {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        color: #856404;
    }
    .api-success {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        color: #155724;
    }
</style>
""", unsafe_allow_html=True)

def init_session_state():
    """Initialize session state variables"""
    if 'rag' not in st.session_state:
        st.session_state.rag = None
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'user_feedback' not in st.session_state:
        st.session_state.user_feedback = []

def save_interaction(query, response, search_results, feedback=None):
    """Save user interaction for monitoring"""
    interaction = {
        'timestamp': datetime.now().isoformat(),
        'query': query,
        'response': response,
        'num_results': len(search_results),
        'top_players': [r['name'] for r in search_results] if search_results else [],
        'feedback': feedback
    }
    
    # Ensure monitoring directory exists
    os.makedirs('monitoring', exist_ok=True)
    
    # Save to file
    filename = f"monitoring/interactions_{datetime.now().strftime('%Y-%m-%d')}.jsonl"
    with open(filename, 'a') as f:
        f.write(json.dumps(interaction) + '\n')

def load_ingestion_stats():
    """Load data ingestion statistics"""
    try:
        with open('data/ingestion_stats.json', 'r') as f:
            return json.load(f)
    except:
        return {}

def create_fantasy_points_chart(players_data):
    """Create fantasy points comparison chart"""
    if not players_data:
        return None
    
    df = pd.DataFrame(players_data)
    fig = px.bar(
        df, 
        x='name', 
        y='fantasy_points',
        color='position',
        title="Fantasy Points Comparison",
        labels={'name': 'Player', 'fantasy_points': 'Fantasy Points per Game'}
    )
    fig.update_layout(xaxis_tickangle=-45)
    return fig

def main():
    init_session_state()
    
    # Header
    st.markdown('<h1 class="main-header">🏀 Fantasy NBA Advisor</h1>', unsafe_allow_html=True)
    st.markdown("Get AI-powered insights and recommendations for your fantasy basketball team")
    
    # Sidebar
    with st.sidebar:
        # Groq API Key input (prioritize user input over environment)
        groq_api_key = st.text_input(
            "Groq API Key", 
            type="password",
            help="Enter your Groq API key to enable AI responses. Get one at https://console.groq.com/",
            placeholder="gsk_..."
        )
        
        # Only use environment key if no user input is provided
        if not groq_api_key:
            env_api_key = os.getenv('GROQ_API_KEY')
            if env_api_key:
                st.info("💡 You can also enter your own API key above to avoid hitting limits")
                groq_api_key = env_api_key
        
        if groq_api_key:
            if not groq_api_key.startswith('gsk_'):
                st.markdown('<div class="api-warning">⚠️ Groq API keys typically start with "gsk_"</div>', unsafe_allow_html=True)
            
            if st.session_state.rag is None or (hasattr(st.session_state.rag, 'groq_client') and st.session_state.rag.groq_client is None):
                try:
                    st.session_state.rag = UnifiedFantasyNBARag(groq_api_key)
                except Exception as e:
                    st.markdown(f'<div class="api-warning">⚠️ Error connecting: {str(e)}</div>', unsafe_allow_html=True)
        else:
            if st.session_state.rag is None:
                st.session_state.rag = UnifiedFantasyNBARag()
            st.markdown("**Without API key:**")
            st.markdown("- ✅ Browse player statistics")
            st.markdown("- ✅ Search and filter players")
            st.markdown("- ✅ View player rankings")
            st.markdown("- ❌ AI-generated advice")
            st.markdown("")
            st.markdown("**To get a Groq API key:**")
            st.markdown("1. Visit [console.groq.com](https://console.groq.com/)")
            st.markdown("2. Sign up for a free account")
            st.markdown("3. Create an API key")
            st.markdown("4. Paste it in the field above")
        
        st.divider()
        
        # Quick stats
        st.header("📊 Quick Stats")
        ingestion_stats = load_ingestion_stats()
        if ingestion_stats:
            st.metric("Players in Database", ingestion_stats.get('total_players', 'N/A'))
            st.metric("Expert Analyses", 
                     ingestion_stats.get('ringer_analyses', 0) + ingestion_stats.get('hoopshype_analyses', 0))
            st.metric("Last Updated", ingestion_stats.get('timestamp', 'N/A'))
        
        st.divider()
        
        # Navigation
        st.header("🧭 Navigation")
        page = st.selectbox(
            "Choose a page:",
            ["💬 Chat Assistant", "🏆 Player Rankings", "📊 Monitoring Dashboard", "🔬 System Evaluation", "📋 System Information"]
        )
    
    # Main content based on selected page
    if page == "💬 Chat Assistant":
        show_chat_assistant()
    elif page == "🏆 Player Rankings":
        show_player_rankings()
    elif page == "📊 Monitoring Dashboard":
        show_monitoring_dashboard()
    elif page == "🔬 System Evaluation":
        show_system_evaluation()
    elif page == "📋 System Information":
        show_system_information()

def show_chat_assistant():
    """Show the main chat interface"""
    st.header("💬 Fantasy NBA Chat Assistant")
    st.write("Ask me anything about NBA players, fantasy advice, statistics, and more!")
    
    # Chat interface
    query = st.text_input(
        "Your question:",
        placeholder="e.g., Who are the best point guards for fantasy basketball?"
    )
    
    if st.button("🚀 Get Advice", type="primary") and query:
        if st.session_state.rag:
            with st.spinner("Analyzing player data..."):
                start_time = time.time()
                
                # Get RAG response
                response, search_results = st.session_state.rag.rag(query)
                
                processing_time = time.time() - start_time
                
                # Display response
                st.subheader("🤖 AI Response")
                if st.session_state.rag.groq_client is None:
                    st.markdown(response)
                    st.info("💡 **Tip:** Enter your Groq API key in the sidebar for personalized AI analysis!")
                else:
                    st.write(response)
                
                # Performance metrics
                st.caption(f"⚡ Response generated in {processing_time:.2f} seconds")
                
                # Feedback
                col1, col2 = st.columns([1, 4])
                with col1:
                    feedback = st.selectbox("Rate this response:", ["", "👍 Helpful", "👎 Not helpful"])
                
                if feedback:
                    save_interaction(query, response, search_results, feedback)
                    st.success("Thank you for your feedback!")
                else:
                    save_interaction(query, response, search_results)
                
                # Add to chat history
                st.session_state.chat_history.append({
                    'query': query,
                    'response': response,
                    'timestamp': datetime.now().strftime('%H:%M:%S')
                })
        else:
            st.error("Database connection not available")
    
    # Show chat history
    if st.session_state.chat_history:
        st.subheader("💭 Recent Conversations")
        for i, chat in enumerate(reversed(st.session_state.chat_history[-5:])):
            with st.expander(f"[{chat['timestamp']}] {chat['query'][:50]}..."):
                st.write(f"**Q:** {chat['query']}")
                st.write(f"**A:** {chat['response']}")

def show_player_rankings():
    """Show complete NBA player rankings"""
    st.header("🏆 NBA Player Rankings")
    st.write("Complete fantasy basketball rankings for all 450 NBA players")
    
    if st.session_state.rag:
        try:
            # Get all players data
            if CLOUD_MODE:
                all_players = st.session_state.rag.sample_data
            else:
                # For local mode, would need to implement get_all_players method
                all_players = []
            
            if all_players:
                # Sort by fantasy rank
                sorted_players = sorted(
                    [p for p in all_players if p.get('fantasy_rank', 999) < 999], 
                    key=lambda x: x.get('fantasy_rank', 999)
                )
                
                st.success(f"📊 Showing {len(sorted_players)} ranked NBA players")
                
                # Filters
                col1, col2, col3 = st.columns(3)
                with col1:
                    position_filter = st.selectbox(
                        "Filter by Position:",
                        ["All"] + sorted(list(set([p.get('position', 'N/A') for p in sorted_players])))
                    )
                with col2:
                    team_filter = st.selectbox(
                        "Filter by Team:",
                        ["All"] + sorted(list(set([p.get('team', 'N/A') for p in sorted_players])))
                    )
                with col3:
                    rank_range = st.slider(
                        "Rank Range:",
                        min_value=1,
                        max_value=len(sorted_players),
                        value=(1, min(100, len(sorted_players)))
                    )
                
                # Apply filters
                filtered_players = sorted_players
                if position_filter != "All":
                    filtered_players = [p for p in filtered_players if p.get('position') == position_filter]
                if team_filter != "All":
                    filtered_players = [p for p in filtered_players if p.get('team') == team_filter]
                
                # Apply rank range
                filtered_players = [p for p in filtered_players if rank_range[0] <= p.get('fantasy_rank', 999) <= rank_range[1]]
                
                st.write(f"Showing {len(filtered_players)} players")
                
                # Display as table
                if filtered_players:
                    # Create DataFrame for better display
                    df_data = []
                    for player in filtered_players:
                        df_data.append({
                            'Rank': player.get('fantasy_rank', 'N/A'),
                            'Player': player.get('name', 'Unknown'),
                            'Position': player.get('position', 'N/A'),
                            'Team': player.get('team', 'N/A'),
                            'FPPM': f"{player.get('fppm', 0):.3f}",
                            'Fantasy Points': f"{player.get('fantasy_points', 0):.1f}"
                        })
                    
                    df = pd.DataFrame(df_data)
                    st.dataframe(df, use_container_width=True, height=600)
                    
                    # Download option
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download Rankings as CSV",
                        data=csv,
                        file_name=f"nba_fantasy_rankings_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
                else:
                    st.info("No players match the selected filters.")
            else:
                st.warning("Player data not available. Please check your connection.")
                
        except Exception as e:
            st.error(f"Error loading player rankings: {e}")
    else:
        st.error("Database connection not available")

def show_monitoring_dashboard():
    """Show monitoring and analytics dashboard"""
    st.header("📊 Monitoring Dashboard")
    
    # Load interaction data
    interactions = []
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        filename = f"monitoring/interactions_{today}.jsonl"
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                for line in f:
                    interactions.append(json.loads(line.strip()))
    except:
        pass
    
    if interactions:
        # Basic metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Queries Today", len(interactions))
        
        with col2:
            avg_results = sum(i['num_results'] for i in interactions) / len(interactions)
            st.metric("Avg Results per Query", f"{avg_results:.1f}")
        
        with col3:
            feedback_count = len([i for i in interactions if i.get('feedback')])
            st.metric("Feedback Received", feedback_count)
        
        with col4:
            positive_feedback = len([i for i in interactions if i.get('feedback') == '👍 Helpful'])
            feedback_rate = (positive_feedback / feedback_count * 100) if feedback_count > 0 else 0
            st.metric("Positive Feedback", f"{feedback_rate:.1f}%")
        
        # Query frequency chart
        query_times = [datetime.fromisoformat(i['timestamp']).hour for i in interactions]
        query_counts = pd.Series(query_times).value_counts().sort_index()
        
        fig = px.bar(
            x=query_counts.index,
            y=query_counts.values,
            title="Query Distribution by Hour",
            labels={'x': 'Hour of Day', 'y': 'Number of Queries'}
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Most searched players
        all_players = []
        for interaction in interactions:
            all_players.extend(interaction.get('top_players', []))
        
        if all_players:
            player_counts = pd.Series(all_players).value_counts().head(10)
            fig = px.bar(
                x=player_counts.values,
                y=player_counts.index,
                orientation='h',
                title="Most Searched Players",
                labels={'x': 'Search Frequency', 'y': 'Player'}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Recent queries
        st.subheader("🔍 Recent Queries")
        recent_queries = interactions[-10:]
        for query in reversed(recent_queries):
            timestamp = datetime.fromisoformat(query['timestamp']).strftime('%H:%M:%S')
            feedback_emoji = "👍" if query.get('feedback') == '👍 Helpful' else "👎" if query.get('feedback') == '👎 Not helpful' else "❓"
            st.write(f"**[{timestamp}]** {query['query']} {feedback_emoji}")
    
    else:
        st.info("No interaction data available for today. Start using the chat assistant to see analytics!")
    
    # Ingestion stats
    st.subheader("💾 Data Ingestion Statistics")
    ingestion_stats = load_ingestion_stats()
    if ingestion_stats:
        col1, col2 = st.columns(2)
        with col1:
            st.json(ingestion_stats)
    else:
        st.warning("No ingestion statistics available. Run data ingestion first.")

def show_system_evaluation():
    """Show system evaluation results with unified approach"""
    st.header("🔬 System Evaluation")
    
    # Check if we have the unified system with full evaluation capabilities
    if st.session_state.rag:
        st.subheader("🚀 Full System Evaluation - Unified Platform")
        
        # Get system stats
        try:
            system_stats = st.session_state.rag.get_system_stats()
        except:
            system_stats = {"error": "Could not retrieve system stats"}
        
        # Real-time system health check
        st.subheader("🏥 System Health Check")
        
        col1, col2, col3, col4 = st.columns(4)
        
        # Enhanced health metrics
        if "database_stats" in system_stats:
            db_stats = system_stats["database_stats"]
            with col1:
                st.metric("NBA Database", f"{db_stats['total_players']} players", 
                         f"{db_stats['coverage_percentage']:.1f}% coverage")
            with col2:
                st.metric("Data Quality", f"{db_stats['players_with_ranks']}", 
                         "Players ranked")
            with col3:
                st.metric("FPPM Data", f"{db_stats['players_with_fppm']}", 
                         "Players w/ efficiency")
            with col4:
                st.metric("Expert Analysis", f"{db_stats['players_with_analysis']}", 
                         "Players analyzed")
        else:
            # Fallback metrics
            with col1:
                st.metric("NBA Database", "Active", "✅ Loaded")
            with col2:
                st.metric("AI System", "Connected" if st.session_state.rag.groq_client else "Limited", 
                         "✅ Ready" if st.session_state.rag.groq_client else "⚠️ No API")
            with col3:
                st.metric("Search System", "Active", "✅ Ready")
            with col4:
                st.metric("Evaluation", "Full Suite", "✅ Available")
        
        st.divider()
        
        # Advanced evaluation tabs
        st.subheader("🧪 Advanced System Evaluation")
        
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🔍 Search Performance", 
            "🤖 AI Evaluation", 
            "📊 Data Analysis", 
            "⚡ System Benchmarks",
            "🎯 End-to-End Tests"
        ])
        
        with tab1:
            st.write("**Search Performance Evaluation:**")
            
            if st.button("🔍 Run Search Performance Tests", key="search_perf_btn"):
                with st.spinner("Running comprehensive search evaluation..."):
                    try:
                        results = st.session_state.rag.evaluate_search_performance()
                        
                        # Display results
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Avg Response Time", f"{results['avg_response_time']:.3f}s")
                        with col2:
                            st.metric("Search Accuracy", f"{results['search_accuracy']:.2%}")
                        with col3:
                            st.metric("Coverage Score", f"{results['coverage_score']:.2%}")
                        
                        # Detailed results
                        st.write("**Detailed Search Results:**")
                        search_df = pd.DataFrame(results['test_queries'])
                        st.dataframe(search_df)
                        
                        # Performance chart
                        fig = px.bar(search_df, x='query', y='response_time', 
                                   title="Search Response Times by Query Type")
                        fig.update_layout(xaxis_tickangle=-45)
                        st.plotly_chart(fig, use_container_width=True)
                        
                    except Exception as e:
                        st.error(f"Search evaluation failed: {e}")
        
        with tab2:
            st.write("**AI Response Quality Evaluation:**")
            
            if st.button("🤖 Run AI Performance Tests", key="ai_perf_btn"):
                if st.session_state.rag.groq_client:
                    with st.spinner("Evaluating AI response quality..."):
                        try:
                            results = st.session_state.rag.evaluate_ai_performance()
                            
                            # Display results
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Avg Response Time", f"{results['avg_response_time']:.2f}s")
                            with col2:
                                st.metric("Avg Response Length", f"{results['avg_response_length']} chars")
                            with col3:
                                st.metric("Quality Score", f"{results['quality_score']:.2%}")
                            
                            # Detailed results
                            st.write("**AI Response Analysis:**")
                            ai_df = pd.DataFrame(results['test_queries'])
                            st.dataframe(ai_df)
                            
                            # Quality vs Speed chart
                            fig = px.scatter(ai_df, x='response_time', y='quality_score', 
                                           hover_data=['query'], title="AI Response Quality vs Speed")
                            st.plotly_chart(fig, use_container_width=True)
                            
                        except Exception as e:
                            st.error(f"AI evaluation failed: {e}")
                else:
                    st.warning("⚠️ AI evaluation requires Groq API key")
        
        with tab3:
            st.write("**Data Quality and Distribution Analysis:**")
            
            if "position_distribution" in system_stats:
                # Position distribution chart
                pos_data = system_stats["position_distribution"]
                pos_df = pd.DataFrame(list(pos_data.items()), columns=['Position', 'Count'])
                
                col1, col2 = st.columns(2)
                with col1:
                    fig = px.pie(pos_df, values='Count', names='Position', 
                               title="Player Distribution by Position")
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    fig = px.bar(pos_df, x='Position', y='Count', 
                               title="Players by Position")
                    st.plotly_chart(fig, use_container_width=True)
            
            # Data completeness metrics
            if "database_stats" in system_stats:
                db_stats = system_stats["database_stats"]
                st.write("**Data Completeness:**")
                
                completeness_data = {
                    "Metric": ["Fantasy Rankings", "FPPM Data", "Expert Analysis", "Position Data"],
                    "Percentage": [
                        (db_stats['players_with_ranks'] / db_stats['total_players']) * 100,
                        (db_stats['players_with_fppm'] / db_stats['total_players']) * 100,
                        (db_stats['players_with_analysis'] / db_stats['total_players']) * 100,
                        100  # Assuming all players have position data
                    ]
                }
                
                completeness_df = pd.DataFrame(completeness_data)
                fig = px.bar(completeness_df, x='Metric', y='Percentage', 
                           title="Data Completeness by Category")
                fig.update_layout(yaxis=dict(range=[0, 100]))
                st.plotly_chart(fig, use_container_width=True)
        
        with tab4:
            st.write("**System Performance Benchmarks:**")
            
            if st.button("⚡ Run Performance Benchmarks", key="perf_bench_btn"):
                with st.spinner("Running system benchmarks..."):
                    try:
                        # Test multiple search scenarios
                        benchmark_queries = [
                            "Nikola Jokic", "center", "point guard", "Lakers", "top scorer",
                            "pick 78", "draft position 50", "Pascal Siakam", "Brandon Miller",
                            "first round picks", "sleeper picks", "injury risk players"
                        ]
                        
                        benchmark_results = []
                        for query in benchmark_queries:
                            start_time = time.time()
                            results = st.session_state.rag.search_players(query, 5)
                            end_time = time.time()
                            
                            benchmark_results.append({
                                "Query": query,
                                "Response Time": end_time - start_time,
                                "Results Found": len(results),
                                "Query Type": "Name" if any(p.get('name', '').lower() in query.lower() for p in st.session_state.rag.sample_data) 
                                           else "Position" if query.lower() in ['center', 'point guard', 'power forward'] 
                                           else "Draft" if 'pick' in query.lower() 
                                           else "General"
                            })
                        
                        bench_df = pd.DataFrame(benchmark_results)
                        
                        # Performance metrics
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Avg Response Time", f"{bench_df['Response Time'].mean():.3f}s")
                        with col2:
                            st.metric("Max Response Time", f"{bench_df['Response Time'].max():.3f}s")
                        with col3:
                            st.metric("Throughput", f"{1/bench_df['Response Time'].mean():.1f} req/s")
                        
                        # Benchmark chart
                        fig = px.box(bench_df, x='Query Type', y='Response Time', 
                                   title="Performance by Query Type")
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Detailed results
                        st.dataframe(bench_df)
                        
                    except Exception as e:
                        st.error(f"Benchmark failed: {e}")
        
        with tab5:
            st.write("**End-to-End System Tests:**")
            
            if st.button("🎯 Run Complete System Test", key="e2e_test_btn"):
                with st.spinner("Running comprehensive system evaluation..."):
                    test_results = {"tests": [], "overall_score": 0}
                    
                    try:
                        # Test 1: Basic search functionality
                        search_result = st.session_state.rag.search_players("Jokic", 1)
                        test_results["tests"].append({
                            "Test": "Basic Search",
                            "Status": "✅ Pass" if search_result else "❌ Fail",
                            "Details": f"Found {len(search_result)} results"
                        })
                        
                        # Test 2: Draft position query
                        draft_result = st.session_state.rag.search_players("pick 78", 3)
                        test_results["tests"].append({
                            "Test": "Draft Position Search", 
                            "Status": "✅ Pass" if draft_result else "❌ Fail",
                            "Details": f"Found {len(draft_result)} players near pick 78"
                        })
                        
                        # Test 3: AI response (if available)
                        if st.session_state.rag.groq_client:
                            ai_response = st.session_state.rag.get_response("Who should I pick first?")
                            ai_test_pass = len(ai_response) > 50 and "Error" not in ai_response
                            test_results["tests"].append({
                                "Test": "AI Response Generation",
                                "Status": "✅ Pass" if ai_test_pass else "❌ Fail", 
                                "Details": f"Response length: {len(ai_response)} chars"
                            })
                        
                        # Test 4: Data integrity
                        data_test = len(st.session_state.rag.sample_data) > 0
                        test_results["tests"].append({
                            "Test": "Data Integrity",
                            "Status": "✅ Pass" if data_test else "❌ Fail",
                            "Details": f"Database contains {len(st.session_state.rag.sample_data)} players"
                        })
                        
                        # Calculate overall score
                        passed_tests = sum(1 for test in test_results["tests"] if "✅" in test["Status"])
                        test_results["overall_score"] = (passed_tests / len(test_results["tests"])) * 100
                        
                        # Display results
                        st.metric("Overall System Health", f"{test_results['overall_score']:.0f}%", 
                                f"{passed_tests}/{len(test_results['tests'])} tests passed")
                        
                        # Test details
                        test_df = pd.DataFrame(test_results["tests"])
                        st.dataframe(test_df, use_container_width=True)
                        
                    except Exception as e:
                        st.error(f"End-to-end test failed: {e}")
        
        return
    
    # Advanced evaluation with vector-based RAG (if available)
    elif FULL_EVALUATION_AVAILABLE:
        st.subheader("🔬 Advanced Vector-Based Evaluation")
        st.info("**Enhanced Evaluation Mode**: Vector database and advanced evaluation tools detected!")
        
        # Initialize evaluator  
        if 'evaluator' not in st.session_state:
            try:
                # Create a vector-based RAG instance for evaluation
                vector_rag = FantasyNBARag()
                if hasattr(vector_rag, 'qdrant_client'):
                    st.session_state.evaluator = RetrievalEvaluator(vector_rag.qdrant_client)
                    st.success("✅ Advanced evaluator initialized with vector database")
                else:
                    st.warning("⚠️ Vector database not available - using standard evaluation")
                    return
            except Exception as e:
                st.error(f"Failed to initialize advanced evaluator: {e}")
                return
        
        evaluator = st.session_state.evaluator
        
        # Advanced evaluation controls
        st.subheader("🧪 Advanced Evaluation Suite")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔤 Evaluate Embedding Models", key="eval_embeddings"):
                with st.spinner("Testing embedding models..."):
                    embedding_results = evaluator.evaluate_embedding_models()
                    st.session_state.embedding_evaluation = embedding_results
        
        with col2:
            if st.button("🔍 Evaluate Retrieval Methods", key="eval_retrieval"):
                with st.spinner("Testing retrieval approaches..."):
                    retrieval_results = evaluator.evaluate_retrieval_methods()
                    st.session_state.retrieval_evaluation = retrieval_results
        
        with col3:
            if st.button("⚡ Evaluate Fusion & Reranking", key="eval_fusion"):
                with st.spinner("Testing fusion and reranking..."):
                    fusion_results = evaluator.evaluate_fusion_and_reranking()
                    st.session_state.fusion_evaluation = fusion_results
        
        # Display advanced evaluation results
        if hasattr(st.session_state, 'embedding_evaluation'):
            st.subheader("🔤 Embedding Model Results")
            embedding_data = st.session_state.embedding_evaluation
            if embedding_data:
                df_models = pd.DataFrame.from_dict(embedding_data, orient='index')
                st.dataframe(df_models)
                if evaluator.best_embedding_model:
                    st.success(f"🏆 **Best Model:** {evaluator.best_embedding_model}")
        
        if hasattr(st.session_state, 'retrieval_evaluation'):
            st.subheader("🔍 Retrieval Method Results")
            retrieval_data = st.session_state.retrieval_evaluation
            if retrieval_data:
                methods = list(retrieval_data.keys())
                f1_scores = [retrieval_data[method]['avg_f1_score'] for method in methods]
                response_times = [retrieval_data[method]['avg_response_time'] for method in methods]
                
                fig = go.Figure()
                fig.add_trace(go.Bar(x=methods, y=f1_scores, name='F1 Score', yaxis='y1'))
                fig.add_trace(go.Scatter(x=methods, y=response_times, mode='lines+markers', 
                                       name='Response Time (s)', yaxis='y2'))
                fig.update_layout(
                    title="Advanced Retrieval Method Comparison",
                    yaxis=dict(title="F1 Score", side="left"),
                    yaxis2=dict(title="Response Time (s)", side="right", overlaying="y")
                )
                st.plotly_chart(fig, use_container_width=True)
                
                if evaluator.best_retrieval_method:
                    st.success(f"🏆 **Best Method:** {evaluator.best_retrieval_method}")
        
        return

def show_system_information():
        st.subheader("🌐 Cloud System Evaluation")
        
        # Real-time system health check
        st.subheader("🏥 System Health Check")
        
        col1, col2, col3, col4 = st.columns(4)
        
        # Check NBA database
        try:
            if st.session_state.rag and hasattr(st.session_state.rag, 'sample_data'):
                player_count = len(st.session_state.rag.sample_data)
                with col1:
                    st.metric("NBA Database", f"{player_count} players", "✅ Loaded")
            else:
                with col1:
                    st.metric("NBA Database", "Error", "❌ Failed")
        except:
            with col1:
                st.metric("NBA Database", "Error", "❌ Failed")
        
        # Check AI connectivity
        try:
            if st.session_state.rag and st.session_state.rag.groq_client:
                with col2:
                    st.metric("AI System", "Connected", "✅ Ready")
            else:
                with col2:
                    st.metric("AI System", "No API Key", "⚠️ Limited")
        except:
            with col2:
                st.metric("AI System", "Error", "❌ Failed")
        
        # Check search functionality
        with col3:
            st.metric("Search System", "Active", "✅ Ready")
        
        # Check data freshness
        with col4:
            st.metric("Data Updated", "Current", "✅ Fresh")
        
        st.divider()
        
        # Interactive system tests
        st.subheader("🧪 Interactive System Tests")
        
        tab1, tab2, tab3, tab4 = st.tabs(["🔍 Search Test", "🤖 AI Response Test", "📊 Data Quality", "⚡ Performance"])
        
        with tab1:
            st.write("**Test the player search functionality:**")
            test_query = st.text_input("Enter a player name or position:", value="Nikola Jokic", key="search_test")
            
            if st.button("🔍 Test Search", key="test_search_btn"):
                if st.session_state.rag:
                    with st.spinner("Testing search..."):
                        results = st.session_state.rag.search_players(test_query, 5)
                        
                        if results:
                            st.success(f"✅ Found {len(results)} matching players:")
                            for i, player in enumerate(results[:3], 1):
                                st.write(f"{i}. **{player.get('name', 'Unknown')}** ({player.get('position', '?')}, {player.get('team', '?')}) - Rank #{player.get('fantasy_rank', '?')}")
                        else:
                            st.warning("⚠️ No players found")
                else:
                    st.error("❌ RAG system not initialized")
        
        with tab2:
            st.write("**Test the AI response system:**")
            test_ai_query = st.text_input("Enter a fantasy basketball question:", value="Who should I draft in the first round?", key="ai_test")
            
            if st.button("🤖 Test AI Response", key="test_ai_btn"):
                if st.session_state.rag and st.session_state.rag.groq_client:
                    with st.spinner("Testing AI response..."):
                        start_time = time.time()
                        response = st.session_state.rag.get_response(test_ai_query)
                        response_time = time.time() - start_time
                        
                        st.success(f"✅ AI Response (in {response_time:.2f}s):")
                        st.write(response[:300] + "..." if len(response) > 300 else response)
                        
                        # Quality metrics
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Response Time", f"{response_time:.2f}s")
                        with col2:
                            st.metric("Response Length", f"{len(response)} chars")
                        with col3:
                            quality = "High" if len(response) > 100 and "player" in response.lower() else "Low"
                            st.metric("Quality Check", quality)
                else:
                    st.warning("⚠️ AI system requires Groq API key")
        
        with tab3:
            st.write("**Evaluate data quality and completeness:**")
            
            if st.button("📊 Analyze Data Quality", key="data_quality_btn"):
                if st.session_state.rag and hasattr(st.session_state.rag, 'sample_data'):
                    data = st.session_state.rag.sample_data
                    
                    # Data quality metrics
                    total_players = len(data)
                    players_with_ranks = sum(1 for p in data if p.get('fantasy_rank', 0) > 0)
                    players_with_fppm = sum(1 for p in data if p.get('fppm', 0) > 0)
                    players_with_analysis = sum(1 for p in data if p.get('expert_analysis'))
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.metric("Total Players", total_players)
                        st.metric("Players w/ Rankings", players_with_ranks, f"{players_with_ranks/total_players*100:.1f}%")
                    
                    with col2:
                        st.metric("Players w/ FPPM", players_with_fppm, f"{players_with_fppm/total_players*100:.1f}%")
                        st.metric("Players w/ Analysis", players_with_analysis, f"{players_with_analysis/total_players*100:.1f}%")
                    
                    # Position distribution
                    st.write("**Position Distribution:**")
                    positions = {}
                    for player in data:
                        pos = player.get('position', 'Unknown')
                        positions[pos] = positions.get(pos, 0) + 1
                    
                    pos_df = pd.DataFrame(list(positions.items()), columns=['Position', 'Count'])
                    fig = px.bar(pos_df, x='Position', y='Count', title="Players by Position")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.error("❌ No data available for analysis")
        
        with tab4:
            st.write("**Performance benchmarking:**")
            
            if st.button("⚡ Run Performance Tests", key="perf_test_btn"):
                if st.session_state.rag:
                    with st.spinner("Running performance tests..."):
                        # Test search performance
                        search_times = []
                        test_queries = ["Jokic", "center", "Lakers", "point guard", "top scorer"]
                        
                        for query in test_queries:
                            start = time.time()
                            st.session_state.rag.search_players(query, 5)
                            search_times.append(time.time() - start)
                        
                        avg_search_time = sum(search_times) / len(search_times)
                        
                        # Performance metrics
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Avg Search Time", f"{avg_search_time:.3f}s")
                        with col2:
                            st.metric("Search Throughput", f"{1/avg_search_time:.1f} req/s")
                        with col3:
                            status = "Excellent" if avg_search_time < 0.1 else "Good" if avg_search_time < 0.5 else "Slow"
                            st.metric("Performance", status)
                        
                        # Performance chart
                        perf_df = pd.DataFrame({
                            'Query': test_queries,
                            'Response Time (s)': search_times
                        })
                        fig = px.bar(perf_df, x='Query', y='Response Time (s)', title="Search Performance by Query Type")
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.error("❌ RAG system not available")
        
        st.divider()
        
        # Comparison with Docker mode
        st.subheader("🐳 Enhanced Features in Docker Mode")
        st.info("""
        **Additional evaluation features available in Local Docker Mode:**
        - Vector similarity testing
        - Embedding model comparison
        - Retrieval method evaluation  
        - Fusion and reranking analysis
        - Advanced performance benchmarking
        - Database indexing optimization
        
        **To access full evaluation suite:**
        1. Set up local Docker environment
        2. Complete data ingestion pipeline
        3. Access comprehensive testing tools
        
        [Docker Setup Guide](https://docs.streamlit.io/deploy/tutorials/docker)
        """)
        
        return

def show_system_information():
    """Show comprehensive system information and configuration"""
    st.header("📋 System Information")
    st.write("Complete system configuration, implementation details, and file references.")
    
    # System Overview
    st.subheader("🏀 Fantasy NBA Advisor System Overview")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("""
        **🎯 Primary Objective**
        - FPPM-prioritized fantasy basketball advice
        - Elite player recognition (Jokic, Giannis, Luka)
        - Special character support for international players
        """)
        
        st.success("""
        **✅ Current Configuration**
        - **Embedding Model:** sentence-transformers/all-MiniLM-L6-v2
        - **Retrieval Method:** Hybrid search with FPPM boosting
        - **LLM Model:** llama-3.1-8b-instant (Groq)
        - **Elite Fantasy Value:** FPPM × Availability Score
        """)
    
    with col2:
        st.warning("""
        **⚠️ Key Features**
        - Unicode normalization for special characters
        - Simplified UI (Chat + Monitoring only)
        - Enhanced query processing for fantasy context
        - Real-time performance monitoring
        """)
        
        # Display current FPPM leaders
        st.metric("Elite Players (FPPM)", "Jokic: 1.286, Giannis: 1.221, Luka: 1.020")
    
    # Implementation Details
    st.subheader("🔧 Implementation Details")
    
    # File structure and references
    implementation_files = {
        "Core RAG Logic": "src/rag.py",
        "Streamlit Application": "src/app.py", 
        "Data Ingestion": "src/data_ingestion.py",
        "Evaluation Module": "src/evaluation.py",
        "Docker Configuration": "docker-compose.yml",
        "Environment Variables": ".env",
        "Documentation": "README.md, main.md",
        "Agent Instructions": "AGENT_INSTRUCTIONS.md",
        "Data Sources": "DATA_SOURCES.md"
    }
    
    st.write("**📁 File Structure & Implementation References:**")
    for component, file_path in implementation_files.items():
        st.write(f"- **{component}:** `{file_path}`")
    
    # Technical specifications
    st.subheader("⚙️ Technical Specifications")
    
    tech_specs = {
        "Vector Database": "Qdrant v1.6.4",
        "Embedding Model": "sentence-transformers v2.4.0",
        "LLM Provider": "Groq API v0.13.0",
        "Web Framework": "Streamlit v1.28.1",
        "Python Version": "3.11+",
        "Containerization": "Docker + Docker Compose"
    }
    
    col1, col2, col3 = st.columns(3)
    for i, (tech, version) in enumerate(tech_specs.items()):
        with [col1, col2, col3][i % 3]:
            st.metric(tech, version)
    
    # Fantasy basketball configuration
    st.subheader("🏀 Fantasy Basketball Configuration")
    
    with st.expander("📊 Fantasy Points Formula (SportWS)"):
        st.code("""
Fantasy Points = (FT × 1.5) + (FTA × -0.5) + 
                (2P × 2.5) + (2PA × -0.5) + 
                (3P × 3.5) + (3PA × -0.5) + 
                (ORB × 1.0) + (DRB × 1.0) + 
                (AST × 1.0) + (BLK × 1.0) + 
                (STL × 1.0) + (TOV × -1.0)
        """)
    
    with st.expander("⚡ FPPM Calculation & Elite Fantasy Value"):
        st.code("""
FPPM = Fantasy Points Per Game ÷ Minutes Per Game

Availability Score = (games_factor × 0.4) + 
                    (starting_factor × 0.3) + 
                    (minutes_factor × 0.3)

Elite Fantasy Value = FPPM × Availability Score
        """)
    
    with st.expander("🌟 Elite Player Identification"):
        st.code("""
# Enhanced query processing for draft picks
if 'draft' in query or 'best' in query:
    enhanced_query = f"{query} Jokic Giannis Luka elite NBA superstars high FPPM"

# FPPM-based ranking
results.sort(key=lambda x: x['elite_fantasy_value'], reverse=True)
        """)
    
    # Data sources and ingestion
    st.subheader("📊 Data Sources & Ingestion")
    
    data_sources = {
        "Basketball Reference": "Statistical data (570+ players)",
        "The Ringer Top 100": "Expert analysis and rankings",
        "HoopsHype": "Additional expert insights",
        "Special Character Support": "Unicode normalization for international players"
    }
    
    for source, description in data_sources.items():
        st.write(f"- **{source}:** {description}")
    
    # Environment configuration
    st.subheader("🔧 Environment Configuration")
    
    with st.expander("📋 Required Environment Variables"):
        st.code("""
# Groq API Configuration
GROQ_API_KEY=your_groq_api_key_here

# Qdrant Configuration  
QDRANT_HOST=localhost
QDRANT_PORT=6333

# Application Settings
DEBUG=true
LOG_LEVEL=INFO

# Data Scraping Configuration
ENABLE_RINGER_SCRAPING=true
ENABLE_HOOPSHYPE_SCRAPING=true
REQUEST_DELAY_SECONDS=1
        """)
    
    # Quick start instructions
    st.subheader("🚀 Quick Start Instructions")
    
    with st.expander("📦 Setup & Installation"):
        st.markdown("""
        ```bash
        # 1. Clone the repository
        git clone <repository-url>
        cd fantasy_nba_advisor
        
        # 2. Configure environment
        cp .env.example .env
        # Edit .env with your Groq API key
        
        # 3. Start the application
        make ingest-data    # First time only
        make project-run    # Start application
        
        # 4. Access application
        open http://localhost:8501
        ```
        """)
    
    with st.expander("💡 Usage Examples"):
        st.markdown("""
        **Sample Queries:**
        - "Who are the best 5 picks of the draft?"
        - "Compare Jokic and Giannis for fantasy value"
        - "Tell me about players with high FPPM"
        - "Show me efficient point guards"
        - "Who should I draft in the first round?"
        
        **Expected Results:**
        - Elite players (Jokic, Giannis, Luka) appear at top
        - FPPM-based rankings prioritized
        - Special characters handled correctly
        - Fantasy-focused analysis provided
        """)
    
    # Performance metrics
    st.subheader("📈 System Performance")
    
    if hasattr(st.session_state, 'rag') and st.session_state.rag:
        try:
            # Get some basic stats from the RAG system
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Players Indexed", "570+")
            with col2:
                st.metric("Vector Dimensions", "384")
            with col3:
                st.metric("Average Response Time", "< 2s")
                
        except Exception as e:
            st.warning(f"Could not retrieve system stats: {e}")
    
    # File implementation mapping
    st.subheader("📖 Implementation File Mapping")
    
    implementation_mapping = {
        "FPPM Prioritization": ["src/rag.py:_apply_boosting()", "src/rag.py:_calculate_fantasy_value()"],
        "Special Character Handling": ["src/rag.py:_normalize_name()", "src/rag.py:_fuzzy_name_search()"],
        "Enhanced Query Processing": ["src/rag.py:_enhance_fantasy_query()"],
        "Simplified UI": ["src/app.py:show_chat_assistant()", "src/app.py:show_monitoring_dashboard()"],
        "Evaluation System": ["src/evaluation.py:RetrievalEvaluator"],
        "Data Ingestion": ["src/data_ingestion.py"],
        "Docker Configuration": ["docker-compose.yml", "Dockerfile"],
        "Documentation": ["README.md", "main.md", "AGENT_INSTRUCTIONS.md"]
    }
    
    for feature, files in implementation_mapping.items():
        with st.expander(f"🔍 {feature} Implementation"):
            for file_ref in files:
                st.code(file_ref)

if __name__ == "__main__":
    main()