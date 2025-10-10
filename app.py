"""
Fantasy NBA Advisor - Unified Streamlit App
Works seamlessly for both local development and Streamlit Cloud deployment
"""

import streamlit as st
import sys
import os
import logging
import time
from datetime import datetime

# Load environment variables for local/Docker development
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available (e.g., on Streamlit Cloud)
    pass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import unified modules for consistent functionality
import sys
import os

# Add multiple path options for robust import
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, 'src')
root_path = current_dir

# Check if we're on Streamlit Cloud (has /mount/src/ in path)
is_streamlit_cloud = '/mount/src/' in current_dir

# Add paths to sys.path if not already there
for path in [src_path, root_path]:
    if path not in sys.path:
        sys.path.insert(0, path)

# Try importing with detailed error handling
UnifiedFantasyNBARag = None
import_success = False

try:
    from rag_unified import UnifiedFantasyNBARag
    logger.info("✅ Using unified RAG system from src directory")
    import_success = True
except ImportError as e1:
    logger.warning(f"Failed to import from src: {e1}")
    try:
        from rag_unified_cloud import UnifiedFantasyNBARag
        logger.info("✅ Using unified RAG system from cloud copy")
        import_success = True
    except ImportError as e2:
        logger.error(f"Failed to import from root: {e2}")
        st.error("❌ Failed to import unified RAG system")
        st.error(f"Src import error: {e1}")
        st.error(f"Root import error: {e2}")
        st.info(f"Current directory: {current_dir}")
        st.info(f"Is Streamlit Cloud: {is_streamlit_cloud}")
        st.info(f"Src path exists: {os.path.exists(src_path)}")
        st.info(f"rag_unified.py exists: {os.path.exists(os.path.join(src_path, 'rag_unified.py'))}")
        st.info(f"rag_unified_cloud.py exists: {os.path.exists(os.path.join(root_path, 'rag_unified_cloud.py'))}")
        st.stop()

if not import_success or UnifiedFantasyNBARag is None:
    st.error("❌ UnifiedFantasyNBARag class not properly imported")
    st.stop()

# Configure Streamlit page
st.set_page_config(
    page_title="Fantasy NBA Advisor",
    page_icon="🏀",
    layout="wide",
    initial_sidebar_state="expanded"
)

def get_api_key():
    """Get API key from user input or environment (for local development)"""
    # For local development, try environment first
    env_api_key = os.getenv('GROQ_API_KEY') if not is_streamlit_cloud else None
    
    if env_api_key and not is_streamlit_cloud:
        # Local development with environment variable
        st.sidebar.success("🔑 Using API key from environment")
        st.sidebar.info("💡 You can also enter your own API key below to override")
        
    # Always show API key input for user override or cloud deployment
    user_api_key = st.sidebar.text_input(
        "Groq API Key:",
        type="password",
        help="Get your free API key from https://console.groq.com/keys",
        placeholder="gsk_..." if not env_api_key else "Optional: Override environment key"
    )
    
    # Return user input if provided, otherwise environment key
    return user_api_key if user_api_key else env_api_key

def main():
    st.title("🏀 Fantasy NBA Advisor")
    st.markdown("---")
    
    # Sidebar configuration
    st.sidebar.title("⚙️ Configuration")
    
    # Environment info (for debugging)
    if st.sidebar.checkbox("🔧 Show Debug Info"):
        st.sidebar.write(f"**Environment:** {'Streamlit Cloud' if is_streamlit_cloud else 'Local'}")
        st.sidebar.write(f"**Directory:** {current_dir}")
        st.sidebar.write(f"**Import:** {'✅ Success' if import_success else '❌ Failed'}")
    
    # Get API key
    api_key = get_api_key()
    
    if not api_key:
        st.info("👈 Please enter your Groq API key in the sidebar to start using the Fantasy NBA Advisor")
        st.markdown("""
        ### How to get your Groq API Key:
        1. Go to [Groq Console](https://console.groq.com/keys)
        2. Sign up for a free account
        3. Create a new API key
        4. Copy and paste it in the sidebar
        
        ### Features available:
        - 🔍 Search for NBA players
        - 📊 Get player statistics and analysis  
        - 🤖 AI-powered fantasy advice
        - 💡 Team composition recommendations
        - 🏆 Player rankings and analytics
        """)
        return
    
    # Initialize the RAG system with API key
    if 'rag_system' not in st.session_state or st.session_state.get('current_api_key') != api_key:
        try:
            with st.spinner("Initializing NBA Advisor..."):
                st.session_state.rag_system = UnifiedFantasyNBARag(groq_api_key=api_key)
                st.session_state.current_api_key = api_key
            st.success("✅ NBA Advisor initialized successfully!")
        except Exception as e:
            st.error(f"❌ Failed to initialize NBA Advisor: {e}")
            st.info("Please check your API key and try again")
            return
    
    # Sidebar navigation
    st.sidebar.divider()
    st.sidebar.header("🧭 Navigation")
    page = st.sidebar.selectbox(
        "Choose a page:",
        ["💬 Chat Assistant", "🔍 Player Search", "🏆 Player Rankings", "📊 Analytics", "🔬 System Evaluation", "📊 Monitoring Dashboard"]
    )
    
    # Main content based on selected page
    if page == "💬 Chat Assistant":
        show_chat_assistant()
    elif page == "🔍 Player Search":
        show_player_search()
    elif page == "🏆 Player Rankings":
        show_player_rankings()
    elif page == "📊 Analytics":
        show_analytics()
    elif page == "🔬 System Evaluation":
        show_system_evaluation()
    elif page == "📊 Monitoring Dashboard":
        show_monitoring_dashboard()

def show_chat_assistant():
    """Show the main chat interface"""
    st.header("💬 Fantasy NBA Chat Assistant")
    st.write("Ask me anything about NBA players, fantasy advice, statistics, and more!")
    
    # Initialize usage tracking
    if 'usage_stats' not in st.session_state:
        st.session_state.usage_stats = {
            'searches': 0,
            'ai_requests': 0,
            'pages_visited': set(),
            'start_time': time.time()
        }
    
    st.session_state.usage_stats['pages_visited'].add('Chat Assistant')
    
    # Chat interface
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask about NBA players or fantasy advice..."):
        # Track AI request
        st.session_state.usage_stats['ai_requests'] += 1
        
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate and display assistant response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response = st.session_state.rag_system.get_response(prompt)
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                except Exception as e:
                    error_msg = f"Sorry, I encountered an error: {e}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})

def show_player_search():
    """Show player search interface"""
    st.header("🔍 Player Search")
    
    # Initialize usage tracking
    if 'usage_stats' not in st.session_state:
        st.session_state.usage_stats = {
            'searches': 0,
            'ai_requests': 0,
            'pages_visited': set(),
            'start_time': time.time()
        }
    
    st.session_state.usage_stats['pages_visited'].add('Player Search')
    
    # Search input
    search_query = st.text_input("Search for NBA players:", placeholder="e.g., LeBron James, Nikola Jokic")
    
    if search_query:
        # Track search
        st.session_state.usage_stats['searches'] += 1
        
        try:
            # Search for players
            results = st.session_state.rag_system.search_players(search_query)
            
            if results:
                st.success(f"Found {len(results)} players matching '{search_query}':")
                
                # Display results
                for i, player in enumerate(results[:10]):  # Show top 10 results
                    with st.expander(f"{i+1}. {player.get('name', 'Unknown')} - {player.get('team', 'N/A')}"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write(f"**Position:** {player.get('position', 'N/A')}")
                            st.write(f"**Team:** {player.get('team', 'N/A')}")
                        
                        with col2:
                            st.write(f"**PPG:** {player.get('ppg', 'N/A')}")
                            st.write(f"**RPG:** {player.get('rpg', 'N/A')}")
                            st.write(f"**APG:** {player.get('apg', 'N/A')}")
                        
                        if st.button(f"Get AI Analysis for {player.get('name', 'Player')}", key=f"analyze_{i}"):
                            # Track AI request
                            st.session_state.usage_stats['ai_requests'] += 1
                            
                            with st.spinner("Analyzing player..."):
                                analysis = st.session_state.rag_system.get_response(f"Give me a detailed fantasy analysis of {player.get('name', 'this player')}")
                                st.write(analysis)
            else:
                st.warning(f"No players found matching '{search_query}'. Try a different search term.")
        except Exception as e:
            st.error(f"Error searching for players: {e}")

def show_player_rankings():
    """Show player rankings"""
    st.header("🏆 Player Rankings")
    
    try:
        # Get players from the system
        all_players = st.session_state.rag_system.sample_data if st.session_state.rag_system.sample_data else []
        
        if all_players:
            # Sort players by a fantasy score (PPG + RPG + APG for simplicity)
            ranked_players = []
            for player in all_players:
                ppg = player.get('ppg', 0) if isinstance(player.get('ppg'), (int, float)) else 0
                rpg = player.get('rpg', 0) if isinstance(player.get('rpg'), (int, float)) else 0
                apg = player.get('apg', 0) if isinstance(player.get('apg'), (int, float)) else 0
                
                fantasy_score = ppg + rpg + apg
                if fantasy_score > 0:  # Only include players with stats
                    ranked_players.append({
                        'name': player.get('name', 'Unknown'),
                        'team': player.get('team', 'N/A'),
                        'position': player.get('position', 'N/A'),
                        'ppg': ppg,
                        'rpg': rpg,
                        'apg': apg,
                        'fantasy_score': fantasy_score
                    })
            
            # Sort by fantasy score
            ranked_players.sort(key=lambda x: x['fantasy_score'], reverse=True)
            
            if ranked_players:
                st.write(f"**Top {min(20, len(ranked_players))} Fantasy Basketball Players:**")
                
                # Create ranking table
                ranking_data = []
                for i, player in enumerate(ranked_players[:20], 1):
                    ranking_data.append({
                        "Rank": i,
                        "Player": player['name'],
                        "Team": player['team'],
                        "Position": player['position'],
                        "PPG": player['ppg'],
                        "RPG": player['rpg'],
                        "APG": player['apg'],
                        "Fantasy Score": round(player['fantasy_score'], 1)
                    })
                
                st.dataframe(ranking_data, use_container_width=True)
                
                # Position filter
                st.subheader("📊 Filter by Position")
                position = st.selectbox("Select Position:", ["All", "PG", "SG", "SF", "PF", "C"])
                
                if position != "All":
                    filtered_players = [p for p in ranked_players if p['position'] == position]
                    if filtered_players:
                        st.write(f"**Top {position} Players:**")
                        filtered_data = []
                        for i, player in enumerate(filtered_players[:10], 1):
                            filtered_data.append({
                                "Rank": i,
                                "Player": player['name'],
                                "Team": player['team'],
                                "PPG": player['ppg'],
                                "RPG": player['rpg'],
                                "APG": player['apg']
                            })
                        st.dataframe(filtered_data, use_container_width=True)
                    else:
                        st.warning(f"No {position} players found in the rankings.")
            else:
                st.warning("No player statistics available for ranking. Using fallback data.")
                show_fallback_rankings()
        else:
            st.warning("No player data loaded. Using fallback rankings.")
            show_fallback_rankings()
            
    except Exception as e:
        st.error(f"Error loading player rankings: {e}")
        show_fallback_rankings()

def show_fallback_rankings():
    """Show fallback rankings when data is not available"""
    st.info("📊 Showing sample NBA player rankings:")
    
    fallback_data = [
        {"Rank": 1, "Player": "Nikola Jokić", "Team": "DEN", "Position": "C", "PPG": 24.5, "RPG": 11.8, "APG": 9.8},
        {"Rank": 2, "Player": "Luka Dončić", "Team": "DAL", "Position": "PG", "PPG": 32.4, "RPG": 8.6, "APG": 8.0},
        {"Rank": 3, "Player": "Joel Embiid", "Team": "PHI", "Position": "C", "PPG": 33.1, "RPG": 10.2, "APG": 4.2},
        {"Rank": 4, "Player": "Giannis Antetokounmpo", "Team": "MIL", "Position": "PF", "PPG": 31.1, "RPG": 11.8, "APG": 5.7},
        {"Rank": 5, "Player": "Jayson Tatum", "Team": "BOS", "Position": "SF", "PPG": 30.1, "RPG": 8.8, "APG": 4.9},
        {"Rank": 6, "Player": "Shai Gilgeous-Alexander", "Team": "OKC", "Position": "PG", "PPG": 31.4, "RPG": 4.8, "APG": 5.5},
        {"Rank": 7, "Player": "Damian Lillard", "Team": "MIL", "Position": "PG", "PPG": 24.3, "RPG": 4.4, "APG": 7.0},
        {"Rank": 8, "Player": "Anthony Davis", "Team": "LAL", "Position": "PF", "PPG": 25.9, "RPG": 12.5, "APG": 2.6},
        {"Rank": 9, "Player": "LeBron James", "Team": "LAL", "Position": "SF", "PPG": 25.7, "RPG": 7.3, "APG": 8.3},
        {"Rank": 10, "Player": "Stephen Curry", "Team": "GSW", "Position": "PG", "PPG": 26.4, "RPG": 4.5, "APG": 5.1}
    ]
    
    st.dataframe(fallback_data, use_container_width=True)

def show_analytics():
    """Show analytics and statistics"""
    st.header("📊 Fantasy Basketball Analytics")
    
    try:
        # System stats
        st.subheader("📈 System Overview")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_players = len(st.session_state.rag_system.sample_data) if st.session_state.rag_system.sample_data else 450
            st.metric("Total Players", f"{total_players}", "📊")
        
        with col2:
            st.metric("Active Teams", "30", "🏀")
        
        with col3:
            status = "✅ Active" if st.session_state.rag_system.groq_client else "⚠️ Limited"
            st.metric("System Status", status, "🔧")
        
        st.divider()
        
        # Top performers by category
        st.subheader("🎯 Top Performers")
        
        tab1, tab2, tab3 = st.tabs(["🏹 Scoring", "🔄 Rebounds", "🎯 Assists"])
        
        with tab1:
            st.write("**Top Scorers:**")
            try:
                # Get actual player data from the system
                top_scorers = []
                for player in st.session_state.rag_system.sample_data[:50]:  # Check first 50 players
                    ppg = player.get('ppg', 0)
                    if ppg and ppg != 'N/A' and isinstance(ppg, (int, float)) and ppg > 25:
                        top_scorers.append((player.get('name', 'Unknown'), ppg))
                
                # Sort by PPG and take top 5
                top_scorers.sort(key=lambda x: x[1], reverse=True)
                
                if top_scorers:
                    for i, (name, ppg) in enumerate(top_scorers[:5], 1):
                        st.write(f"{i}. {name} - {ppg} PPG")
                else:
                    # Fallback to known top scorers
                    fallback_scorers = [
                        ("Luka Dončić", 32.4),
                        ("Joel Embiid", 31.1),
                        ("Damian Lillard", 30.0),
                        ("Shai Gilgeous-Alexander", 29.8),
                        ("Jayson Tatum", 28.9)
                    ]
                    for i, (name, ppg) in enumerate(fallback_scorers, 1):
                        st.write(f"{i}. {name} - {ppg} PPG")
            except Exception as e:
                st.write("Top scoring leaders data temporarily unavailable")
                logger.error(f"Error getting top scorers: {e}")
        
        with tab2:
            st.write("**Top Rebounders:**")
            try:
                # Get actual rebounding data
                top_rebounders = []
                for player in st.session_state.rag_system.sample_data[:50]:
                    rpg = player.get('rpg', 0)
                    if rpg and rpg != 'N/A' and isinstance(rpg, (int, float)) and rpg > 10:
                        top_rebounders.append((player.get('name', 'Unknown'), rpg))
                
                top_rebounders.sort(key=lambda x: x[1], reverse=True)
                
                if top_rebounders:
                    for i, (name, rpg) in enumerate(top_rebounders[:5], 1):
                        st.write(f"{i}. {name} - {rpg} RPG")
                else:
                    # Fallback data
                    fallback_rebounders = [
                        ("Nikola Jokić", 12.8),
                        ("Domantas Sabonis", 12.3),
                        ("Joel Embiid", 11.8),
                        ("Giannis Antetokounmpo", 11.8),
                        ("Anthony Davis", 11.5)
                    ]
                    for i, (name, rpg) in enumerate(fallback_rebounders, 1):
                        st.write(f"{i}. {name} - {rpg} RPG")
            except Exception as e:
                st.write("Rebounding leaders data temporarily unavailable")
        
        with tab3:
            st.write("**Top Playmakers:**")
            try:
                # Get actual assists data  
                top_assists = []
                for player in st.session_state.rag_system.sample_data[:50]:
                    apg = player.get('apg', 0)
                    if apg and apg != 'N/A' and isinstance(apg, (int, float)) and apg > 7:
                        top_assists.append((player.get('name', 'Unknown'), apg))
                
                top_assists.sort(key=lambda x: x[1], reverse=True)
                
                if top_assists:
                    for i, (name, apg) in enumerate(top_assists[:5], 1):
                        st.write(f"{i}. {name} - {apg} APG")
                else:
                    # Fallback data
                    fallback_assists = [
                        ("Tyrese Haliburton", 10.9),
                        ("Trae Young", 10.8),
                        ("Chris Paul", 8.9),
                        ("Luka Dončić", 8.2),
                        ("Nikola Jokić", 8.0)
                    ]
                    for i, (name, apg) in enumerate(fallback_assists, 1):
                        st.write(f"{i}. {name} - {apg} APG")
            except Exception as e:
                st.write("Assist leaders data temporarily unavailable")
        
        st.divider()
        
        # Fantasy tips
        st.subheader("💡 Fantasy Tips")
        
        tips = [
            "🎯 **Target Multi-Category Players**: Look for players who contribute across multiple statistical categories",
            "📈 **Monitor Usage Rates**: High usage rate often correlates with fantasy production",
            "🏥 **Check Injury Reports**: Stay updated on player health status before making lineup decisions",
            "🔄 **Consider Matchups**: Some players perform better against certain team defenses",
            "📊 **Track Minutes**: Playing time is crucial for fantasy production"
        ]
        
        for tip in tips:
            st.markdown(tip)
    
    except Exception as e:
        st.error(f"Error loading analytics: {e}")

def show_system_evaluation():
    """Show system evaluation and testing"""
    st.header("🔬 System Evaluation")
    
    try:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🧪 System Tests")
            
            if st.button("🔍 Test Player Search"):
                with st.spinner("Testing search functionality..."):
                    test_query = "Nikola Jokic"
                    try:
                        results = st.session_state.rag_system.search_players(test_query, num_results=3)
                        if results:
                            st.success(f"✅ Search test passed: Found {len(results)} results for '{test_query}'")
                            for i, player in enumerate(results[:3], 1):
                                st.write(f"{i}. {player.get('name', 'Unknown')} ({player.get('team', 'N/A')})")
                        else:
                            st.warning("⚠️ Search test: No results found")
                    except Exception as e:
                        st.error(f"❌ Search test failed: {e}")
            
            if st.button("🤖 Test AI Response"):
                with st.spinner("Testing AI functionality..."):
                    try:
                        test_prompt = "Who is the best fantasy basketball player?"
                        response = st.session_state.rag_system.get_response(test_prompt)
                        if response and len(response) > 50:
                            st.success("✅ AI response test passed")
                            st.write("**Sample response:**")
                            st.write(response[:200] + "..." if len(response) > 200 else response)
                        else:
                            st.warning("⚠️ AI response test: Short or empty response")
                    except Exception as e:
                        st.error(f"❌ AI response test failed: {e}")
        
        with col2:
            st.subheader("📊 System Metrics")
            
            # Display system information
            st.metric("Data Source", "Loaded", "✅")
            st.metric("Players Available", len(st.session_state.rag_system.sample_data), "📈")
            
            groq_status = "✅ Connected" if st.session_state.rag_system.groq_client else "❌ Unavailable"
            st.metric("AI Service", groq_status, "🤖")
            
            # Performance metrics
            st.divider()
            st.subheader("⚡ Performance")
            
            if st.button("📈 Run Benchmark"):
                with st.spinner("Running performance benchmark..."):
                    import time
                    
                    # Search benchmark
                    start_time = time.time()
                    try:
                        results = st.session_state.rag_system.search_players("LeBron James", num_results=5)
                        search_time = time.time() - start_time
                        st.metric("Search Speed", f"{search_time:.2f}s", "🔍")
                    except:
                        st.metric("Search Speed", "Error", "❌")
                    
                    # Data load benchmark
                    data_size = len(st.session_state.rag_system.sample_data)
                    st.metric("Data Load", f"{data_size} players", "📊")
        
        st.divider()
        
        # Advanced evaluation
        st.subheader("🎯 Advanced Evaluation")
        
        tab1, tab2, tab3 = st.tabs(["🔍 Search Analysis", "🤖 AI Quality", "📊 Data Coverage"])
        
        with tab1:
            st.write("**Search Performance Analysis:**")
            
            test_queries = ["LeBron James", "Nikola Jokic", "Stephen Curry", "point guard", "Lakers"]
            
            if st.button("Run Search Tests"):
                results_summary = []
                for query in test_queries:
                    try:
                        results = st.session_state.rag_system.search_players(query, num_results=3)
                        results_summary.append({
                            "Query": query,
                            "Results": len(results),
                            "Status": "✅ Pass" if results else "❌ Fail"
                        })
                    except Exception as e:
                        results_summary.append({
                            "Query": query,
                            "Results": 0,
                            "Status": f"❌ Error: {str(e)[:30]}..."
                        })
                
                st.dataframe(results_summary, use_container_width=True)
        
        with tab2:
            st.write("**AI Response Quality:**")
            
            if st.button("Test AI Responses"):
                test_prompts = [
                    "Who is the best point guard?",
                    "Compare LeBron and Jordan",
                    "Best fantasy picks for tonight?"
                ]
                
                for prompt in test_prompts:
                    with st.expander(f"Test: {prompt}"):
                        try:
                            response = st.session_state.rag_system.get_response(prompt)
                            st.write(f"**Response length:** {len(response)} characters")
                            st.write(f"**Quality score:** {'✅ Good' if len(response) > 100 else '⚠️ Short'}")
                            st.write(f"**Preview:** {response[:150]}...")
                        except Exception as e:
                            st.error(f"Error: {e}")
        
        with tab3:
            st.write("**Data Coverage Analysis:**")
            
            # Analyze the loaded data
            if st.session_state.rag_system.sample_data:
                total_players = len(st.session_state.rag_system.sample_data)
                
                # Count players with stats
                players_with_stats = sum(1 for p in st.session_state.rag_system.sample_data 
                                       if p.get('ppg') and p.get('ppg') != 'N/A')
                
                st.metric("Total Players", total_players, "👥")
                st.metric("Players with Stats", players_with_stats, "📊")
                
                coverage_pct = (players_with_stats / total_players * 100) if total_players > 0 else 0
                st.metric("Data Coverage", f"{coverage_pct:.1f}%", "📈")
                
                # Sample data quality
                if st.button("Analyze Data Quality"):
                    sample_players = st.session_state.rag_system.sample_data[:10]
                    
                    st.write("**Sample player data:**")
                    for i, player in enumerate(sample_players, 1):
                        name = player.get('name', 'Unknown')
                        team = player.get('team', 'N/A')
                        ppg = player.get('ppg', 'N/A')
                        st.write(f"{i}. {name} ({team}) - {ppg} PPG")
    
    except Exception as e:
        st.error(f"Error in system evaluation: {e}")

def show_monitoring_dashboard():
    """Show monitoring and system health dashboard"""
    st.header("📊 Monitoring Dashboard")
    
    try:
        # System health overview
        st.subheader("🏥 System Health")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            health_status = "✅ Healthy" if st.session_state.rag_system else "❌ Error"
            st.metric("System Status", health_status, "🔧")
        
        with col2:
            api_status = "✅ Connected" if st.session_state.rag_system.groq_client else "❌ Disconnected"
            st.metric("API Status", api_status, "🔌")
        
        with col3:
            data_status = "✅ Loaded" if st.session_state.rag_system.sample_data else "❌ Missing"
            st.metric("Data Status", data_status, "📊")
        
        with col4:
            player_count = len(st.session_state.rag_system.sample_data) if st.session_state.rag_system.sample_data else 0
            st.metric("Players Loaded", player_count, "👥")
        
        st.divider()
        
        # Usage statistics
        st.subheader("📈 Usage Statistics")
        
        # Initialize session state for tracking
        if 'usage_stats' not in st.session_state:
            st.session_state.usage_stats = {
                'searches': 0,
                'ai_requests': 0,
                'pages_visited': set(),
                'start_time': time.time()
            }
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Search Queries", st.session_state.usage_stats['searches'], "🔍")
        
        with col2:
            st.metric("AI Requests", st.session_state.usage_stats['ai_requests'], "🤖")
        
        with col3:
            session_time = time.time() - st.session_state.usage_stats['start_time']
            st.metric("Session Time", f"{session_time/60:.1f} min", "⏱️")
        
        st.divider()
        
        # Real-time monitoring
        st.subheader("🔄 Real-time Monitoring")
        
        if st.button("🔄 Refresh Status"):
            with st.spinner("Checking system status..."):
                # Test all components
                status_checks = []
                
                # Test data loading
                try:
                    data_ok = len(st.session_state.rag_system.sample_data) > 0
                    status_checks.append({"Component": "Data Loading", "Status": "✅ OK" if data_ok else "❌ Error", "Details": f"{len(st.session_state.rag_system.sample_data)} players"})
                except Exception as e:
                    status_checks.append({"Component": "Data Loading", "Status": "❌ Error", "Details": str(e)[:50]})
                
                # Test search
                try:
                    search_results = st.session_state.rag_system.search_players("test", num_results=1)
                    status_checks.append({"Component": "Player Search", "Status": "✅ OK", "Details": f"Found {len(search_results)} results"})
                except Exception as e:
                    status_checks.append({"Component": "Player Search", "Status": "❌ Error", "Details": str(e)[:50]})
                
                # Test AI
                try:
                    if st.session_state.rag_system.groq_client:
                        status_checks.append({"Component": "AI Service", "Status": "✅ OK", "Details": "Connected"})
                    else:
                        status_checks.append({"Component": "AI Service", "Status": "⚠️ Limited", "Details": "No API key"})
                except Exception as e:
                    status_checks.append({"Component": "AI Service", "Status": "❌ Error", "Details": str(e)[:50]})
                
                st.dataframe(status_checks, use_container_width=True)
        
        st.divider()
        
        # Performance metrics
        st.subheader("⚡ Performance Metrics")
        
        # Memory usage (simplified)
        import sys
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**System Resources:**")
            player_data_size = len(str(st.session_state.rag_system.sample_data)) if st.session_state.rag_system.sample_data else 0
            st.metric("Data Size", f"{player_data_size/1024:.1f} KB", "💾")
            
            # Session state size
            session_size = len(str(st.session_state))
            st.metric("Session Size", f"{session_size/1024:.1f} KB", "🗄️")
        
        with col2:
            st.write("**Response Times:**")
            
            if st.button("🎯 Test Response Times"):
                # Search response time
                start = time.time()
                try:
                    st.session_state.rag_system.search_players("LeBron", num_results=3)
                    search_time = (time.time() - start) * 1000
                    st.metric("Search Time", f"{search_time:.0f}ms", "🔍")
                except:
                    st.metric("Search Time", "Error", "❌")
        
        # Logs section
        st.divider()
        st.subheader("📝 System Logs")
        
        if st.checkbox("Show Debug Logs"):
            st.write("**Recent Activity:**")
            
            log_entries = [
                f"✅ System initialized at session start",
                f"📊 Loaded {len(st.session_state.rag_system.sample_data) if st.session_state.rag_system.sample_data else 0} player records",
                f"🔑 API key {'configured' if st.session_state.rag_system.groq_client else 'not provided'}",
                f"🌐 Environment: {'Streamlit Cloud' if is_streamlit_cloud else 'Local Development'}",
                f"⏰ Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            ]
            
            for log in log_entries:
                st.text(log)
    
    except Exception as e:
        st.error(f"Error in monitoring dashboard: {e}")
        st.exception(e)

if __name__ == "__main__":
    main()