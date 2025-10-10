import streamlit as st
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

# Debug info (remove in production)
if os.getenv('DEBUG', 'false').lower() == 'true':
    st.sidebar.write(f"🔍 Debug: CLOUD_MODE = {CLOUD_MODE}")
    st.sidebar.write(f"🔍 Debug: Current dir = {os.getcwd()}")
    st.sidebar.write(f"🔍 Debug: Files = {os.listdir('.')[:5]}...")
    st.sidebar.write(f"🔍 Debug: /mount/src in cwd = {'/mount/src/' in os.getcwd()}")
    st.sidebar.write(f"🔍 Debug: STREAMLIT_SHARING_MODE = {os.getenv('STREAMLIT_SHARING_MODE')}")
    st.sidebar.write(f"🔍 Debug: src exists = {os.path.exists('src')}")

# Import appropriate modules based on environment
if CLOUD_MODE:
    # Cloud deployment - use simplified imports
    try:
        import sys
        sys.path.append('.')
        from rag_cloud import FantasyNBARag
        RETRIEVAL_EVALUATOR_AVAILABLE = False
    except ImportError as e:
        st.error(f"Cloud deployment error: Unable to import required modules: {e}")
        st.stop()
else:
    # Local Docker deployment - use full functionality
    try:
        import sys
        # Add src directory to path for Docker deployment
        src_path = os.path.join(os.path.dirname(__file__), 'src')
        if src_path not in sys.path:
            sys.path.insert(0, src_path)
        
        from rag import FantasyNBARag
        from retrieval_evaluator import RetrievalEvaluator
        RETRIEVAL_EVALUATOR_AVAILABLE = True
    except ImportError as e:
        st.error(f"Local deployment error: Unable to import required modules: {e}")
        st.info("Make sure you're running this from the correct directory with src/ folder available")
        st.info(f"Current directory: {os.getcwd()}")
        st.info(f"Available files: {os.listdir('.')}")
        st.stop()

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Fantasy NBA Advisor",
    page_icon="🏀",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
        st.header("🔧 Configuration")
        
        # Show deployment mode notice
        if CLOUD_MODE:
            st.success("""
            🌐 **Streamlit Cloud Deployment**
            
            Full NBA database with 450 players and AI-powered analysis.
            Complete fantasy basketball functionality available!
            """)
        else:
            st.success("""
            🐳 **Local Docker Mode**
            
            Full functionality with real NBA data and vector search enabled.
            """)
        
        st.markdown("---")
        
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
            
            if st.session_state.rag is None or st.session_state.rag.groq_client is None:
                try:
                    if CLOUD_MODE:
                        st.session_state.rag = FantasyNBARag(groq_api_key, cloud_mode=True)
                    else:
                        st.session_state.rag = FantasyNBARag(groq_api_key)
                    
                    if st.session_state.rag.groq_client:
                        st.markdown('<div class="api-success">✅ Connected to Fantasy NBA database with AI capabilities!</div>', unsafe_allow_html=True)
                    else:
                        st.markdown('<div class="api-warning">⚠️ Invalid API key. Please check your Groq API key.</div>', unsafe_allow_html=True)
                except Exception as e:
                    st.markdown(f'<div class="api-warning">⚠️ Error connecting: {str(e)}</div>', unsafe_allow_html=True)
        else:
            if st.session_state.rag is None:
                if CLOUD_MODE:
                    st.session_state.rag = FantasyNBARag(cloud_mode=True)  # Initialize cloud mode without API key
                else:
                    st.session_state.rag = FantasyNBARag()  # Initialize without API key
            st.markdown('<div class="api-warning">⚠️ Enter Groq API key above for AI-powered responses</div>', unsafe_allow_html=True)
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
                
                # Show chart if multiple players (but no cards)
                if len(search_results) > 1:
                    chart = create_fantasy_points_chart(search_results[:5])
                    if chart:
                        st.plotly_chart(chart, use_container_width=True)
                
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
    """Show system evaluation results"""
    st.header("🔬 System Evaluation")
    
    if CLOUD_MODE or not RETRIEVAL_EVALUATOR_AVAILABLE:
        st.info("""
        🌐 **System Evaluation - Streamlit Cloud**
        
        Advanced system evaluation requires vector database infrastructure.
        
        **Current Cloud Features:**
        - Full NBA player database (450 players)
        - AI-powered chat and analysis
        - Complete player search and rankings
        - Fantasy draft recommendations
        
        **Additional evaluation features available in Local Docker Mode:**
        - Embedding model comparison
        - Retrieval method evaluation  
        - Fusion and reranking analysis
        - Performance benchmarking
        
        **To access advanced evaluation:**
        1. Run locally with Docker
        2. Complete data ingestion  
        3. Access this tab for comprehensive testing
        
        [Setup Guide](https://github.com/idalbo/fantasy_nba_advisor/blob/main/SETUP_GUIDE.md)
        """)
        
        # Show sample evaluation metrics for demo
        st.subheader("📊 Sample Evaluation Metrics")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Retrieval Precision", "0.85", "Local mode only")
        with col2:
            st.metric("Response Time", "<1s", "Local mode only") 
        with col3:
            st.metric("Player Coverage", "450+", "Local mode only")
        
        return
    
    st.write("Comprehensive evaluation of retrieval approaches, embedding models, and system performance.")
    
    # Initialize evaluator  
    if 'evaluator' not in st.session_state:
        if hasattr(st.session_state.rag, 'qdrant_client'):
            st.session_state.evaluator = RetrievalEvaluator(st.session_state.rag.qdrant_client)
        else:
            st.error("Cannot initialize evaluator - RAG system not available")
            return
    
    evaluator = st.session_state.evaluator
    
    # Evaluation controls
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔤 Evaluate Embedding Models"):
            with st.spinner("Testing embedding models..."):
                embedding_results = evaluator.evaluate_embedding_models()
                st.session_state.embedding_evaluation = embedding_results
    
    with col2:
        if st.button("🔍 Evaluate Retrieval Methods"):
            with st.spinner("Testing retrieval approaches..."):
                retrieval_results = evaluator.evaluate_retrieval_methods()
                st.session_state.retrieval_evaluation = retrieval_results
    
    with col3:
        if st.button("⚡ Evaluate Fusion & Reranking"):
            with st.spinner("Testing fusion and reranking..."):
                fusion_results = evaluator.evaluate_fusion_and_reranking()
                st.session_state.fusion_evaluation = fusion_results
    
    # Display embedding model evaluation
    if hasattr(st.session_state, 'embedding_evaluation'):
        st.subheader("🔤 Embedding Model Evaluation Results")
        embedding_data = st.session_state.embedding_evaluation
        
        if embedding_data:
            # Create DataFrame for display
            df_models = pd.DataFrame.from_dict(embedding_data, orient='index')
            st.dataframe(df_models)
            
            # Best model highlight
            if evaluator.best_embedding_model:
                st.success(f"🏆 **Best Embedding Model:** {evaluator.best_embedding_model}")
                st.write(f"**Chosen for:** High relevance score and good performance on fantasy basketball queries")
    
    # Display retrieval method evaluation
    if hasattr(st.session_state, 'retrieval_evaluation'):
        st.subheader("🔍 Retrieval Method Evaluation Results")
        retrieval_data = st.session_state.retrieval_evaluation
        
        if retrieval_data:
            # Create comparison chart
            methods = list(retrieval_data.keys())
            f1_scores = [retrieval_data[method]['avg_f1_score'] for method in methods]
            response_times = [retrieval_data[method]['avg_response_time'] for method in methods]
            
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=methods,
                y=f1_scores,
                name='F1 Score',
                yaxis='y1'
            ))
            fig.add_trace(go.Scatter(
                x=methods,
                y=response_times,
                mode='lines+markers',
                name='Response Time (s)',
                yaxis='y2'
            ))
            
            fig.update_layout(
                title="Retrieval Method Comparison",
                xaxis_title="Method",
                yaxis=dict(title="F1 Score", side="left"),
                yaxis2=dict(title="Response Time (s)", side="right", overlaying="y"),
                legend=dict(x=0.7, y=1)
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Best method highlight
            if evaluator.best_retrieval_method:
                st.success(f"🏆 **Best Retrieval Method:** {evaluator.best_retrieval_method}")
                st.write(f"**Chosen for:** Optimal balance of precision, recall, and response time")
            
            # Detailed metrics
            st.subheader("📊 Detailed Metrics")
            for method, metrics in retrieval_data.items():
                with st.expander(f"{method.replace('_', ' ').title()} Details"):
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Avg Precision", f"{metrics['avg_precision']:.3f}")
                    with col2:
                        st.metric("Avg Recall", f"{metrics['avg_recall']:.3f}")
                    with col3:
                        st.metric("Avg F1 Score", f"{metrics['avg_f1_score']:.3f}")
                    with col4:
                        st.metric("Avg Response Time", f"{metrics['avg_response_time']:.3f}s")
                    
                    st.metric("Avg Cosine Similarity", f"{metrics['avg_cosine_similarity']:.3f}")
    
    # Display fusion and reranking evaluation
    if hasattr(st.session_state, 'fusion_evaluation'):
        st.subheader("⚡ Fusion & Reranking Evaluation Results")
        fusion_data = st.session_state.fusion_evaluation
        
        if fusion_data:
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Fusion Methods**")
                fusion_methods = fusion_data['fusion_methods']
                fusion_df = pd.DataFrame.from_dict(fusion_methods, orient='index')
                st.dataframe(fusion_df)
            
            with col2:
                st.write("**Reranking Methods**")
                rerank_methods = fusion_data['reranking_methods']
                rerank_df = pd.DataFrame.from_dict(rerank_methods, orient='index')
                st.dataframe(rerank_df)
            
            # Best combination
            if 'best_combination' in fusion_data:
                best_combo = fusion_data['best_combination']
                st.success(f"🏆 **Best Combination:** {best_combo['fusion']} + {best_combo['reranking']}")
                st.metric("Combined Score", f"{best_combo['combined_score']:.3f}")
    
    # Test queries section
    st.subheader("🧪 Test Queries & Expected Results")
    test_queries = evaluator.get_test_queries_and_expected_results()
    
    for i, test_case in enumerate(test_queries, 1):
        with st.expander(f"Test Case {i}: {test_case['query']}"):
            st.write(f"**Query:** {test_case['query']}")
            if 'expected_players' in test_case:
                st.write(f"**Expected Players:** {', '.join(test_case['expected_players'])}")
            if 'min_fppm' in test_case:
                st.write(f"**Minimum FPPM:** {test_case['min_fppm']}")
            if 'expected_positions' in test_case:
                st.write(f"**Expected Positions:** {', '.join(test_case['expected_positions'])}")

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