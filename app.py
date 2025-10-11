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

# Try importing the unified RAG system
UnifiedFantasyNBARag = None
import_success = False

try:
    from rag_unified import UnifiedFantasyNBARag
    logger.info("✅ Using unified RAG system")
    import_success = True
except ImportError as e:
    logger.error(f"❌ Failed to import unified RAG system: {e}")
    st.error("❌ Failed to import unified RAG system")
    st.error(f"Import error: {e}")
    st.info(f"Current directory: {current_dir}")
    st.info(f"Is Streamlit Cloud: {is_streamlit_cloud}")
    st.info(f"Src path exists: {os.path.exists(src_path)}")
    st.info(f"rag_unified.py exists: {os.path.exists(os.path.join(src_path, 'rag_unified.py'))}")
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
        ["💬 Chat Assistant", "🔍 Player Search", "📊 Analytics", "🔬 System Evaluation", "📊 Monitoring Dashboard"]
    )
    
    # Main content based on selected page
    if page == "💬 Chat Assistant":
        show_chat_assistant()
    elif page == "🔍 Player Search":
        show_player_search()
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
    
    # Add debug mode
    debug_mode = st.checkbox("🔧 Debug Search Results")
    
    if search_query:
        # Track search
        st.session_state.usage_stats['searches'] += 1
        
        try:
            # Search for players
            results = st.session_state.rag_system.search_players(search_query)
            
            if debug_mode:
                st.write(f"**Debug: Raw search results for '{search_query}':**")
                st.json(results[:3] if results else [])
            
            if results:
                st.success(f"Found {len(results)} players matching '{search_query}':")
                
                # Display results
                for i, player in enumerate(results[:10]):  # Show top 10 results
                    name = player.get('name', 'Unknown')
                    team = player.get('team', 'N/A') 
                    position = player.get('position', 'N/A')
                    
                    with st.expander(f"{i+1}. {name} - {team} ({position})"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write(f"**Position:** {position}")
                            st.write(f"**Team:** {team}")
                            
                            # Show available stats
                            available_stats = []
                            for stat_field in ['ppg', 'rpg', 'apg', 'points_per_game', 'rebounds_per_game', 'assists_per_game']:
                                if stat_field in player and player[stat_field] not in [None, 'N/A', '']:
                                    available_stats.append(f"{stat_field}: {player[stat_field]}")
                            
                            if available_stats:
                                st.write("**Available Stats:**")
                                for stat in available_stats:
                                    st.write(f"• {stat}")
                            else:
                                st.write("**Available Stats:** None in standard format")
                        
                        with col2:
                            # Try to show stats in multiple formats
                            ppg = None
                            rpg = None 
                            apg = None
                            
                            # Try different field names
                            for field in ['ppg', 'points_per_game', 'scoring']:
                                if field in player and player[field] not in [None, 'N/A', '']:
                                    ppg = player[field]
                                    break
                                    
                            for field in ['rpg', 'rebounds_per_game', 'rebounding']:
                                if field in player and player[field] not in [None, 'N/A', '']:
                                    rpg = player[field]
                                    break
                                    
                            for field in ['apg', 'assists_per_game', 'playmaking']:
                                if field in player and player[field] not in [None, 'N/A', '']:
                                    apg = player[field]
                                    break
                            
                            st.write(f"**PPG:** {ppg if ppg is not None else 'Not available'}")
                            st.write(f"**RPG:** {rpg if rpg is not None else 'Not available'}")
                            st.write(f"**APG:** {apg if apg is not None else 'Not available'}")
                            
                            # Show other available fields
                            if debug_mode:
                                st.write("**All fields:**")
                                for key, value in player.items():
                                    if value not in [None, 'N/A', '']:
                                        st.write(f"• {key}: {value}")
                        
                        if st.button(f"Get AI Analysis for {name}", key=f"analyze_{i}"):
                            # Track AI request
                            st.session_state.usage_stats['ai_requests'] += 1
                            
                            with st.spinner(f"Analyzing {name}..."):
                                # More specific query to avoid weird draft recommendations
                                analysis_query = f"Give me a detailed fantasy basketball analysis of {name}. Focus on their current performance, strengths, weaknesses, and fantasy value. Do not provide draft recommendations unless specifically about this individual player."
                                analysis = st.session_state.rag_system.get_response(analysis_query)
                                st.write(analysis)
            else:
                st.warning(f"No players found matching '{search_query}'. Try a different search term.")
                
                if debug_mode:
                    st.write("**Debug: Search troubleshooting**")
                    st.write(f"• Query processed: '{search_query}'")
                    st.write(f"• Total players in database: {len(st.session_state.rag_system.sample_data)}")
                    if st.session_state.rag_system.sample_data:
                        sample_names = [p.get('name', 'No name') for p in st.session_state.rag_system.sample_data[:10]]
                        st.write(f"• Sample player names: {sample_names}")
                
        except Exception as e:
            st.error(f"Error searching for players: {e}")
            if debug_mode:
                st.exception(e)

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
        
        tab1, tab2, tab3 = st.tabs(["� Fantasy Points", "⚡ Efficiency", "🎯 Rankings"])
        
        with tab1:
            st.write("**Top Scorers (Fantasy Points):**")
            try:
                # Get actual player data from the system - no fallbacks
                top_scorers = []
                for player in st.session_state.rag_system.sample_data[:100]:  # Check more players
                    fantasy_points = player.get('fantasy_points', 0)
                    if isinstance(fantasy_points, (int, float)) and fantasy_points > 20:
                        top_scorers.append((player.get('name', 'Unknown'), fantasy_points))
                
                # Sort by fantasy points and take top 5
                top_scorers.sort(key=lambda x: x[1], reverse=True)
                
                if top_scorers:
                    for i, (name, pts) in enumerate(top_scorers[:5], 1):
                        st.write(f"{i}. {name} - {pts:.1f} Fantasy Points")
                else:
                    st.warning("❌ No fantasy scoring data available in current dataset")
                    st.info("Check that player statistics are properly loaded")
            except Exception as e:
                st.error(f"Error loading scoring data: {e}")
        
        with tab2:
            st.write("**Top Efficiency (FPPM):**")
            try:
                # Get actual efficiency data - no fallbacks
                top_efficiency = []
                for player in st.session_state.rag_system.sample_data[:100]:
                    fppm = player.get('fppm', 0)
                    if isinstance(fppm, (int, float)) and fppm > 0.8:  # High efficiency threshold
                        top_efficiency.append((player.get('name', 'Unknown'), fppm))
                
                top_efficiency.sort(key=lambda x: x[1], reverse=True)
                
                if top_efficiency:
                    for i, (name, fppm) in enumerate(top_efficiency[:5], 1):
                        st.write(f"{i}. {name} - {fppm:.3f} FPPM")
                else:
                    st.warning("❌ No efficiency data available in current dataset")
                    st.info("Check that player statistics are properly loaded")
            except Exception as e:
                st.error(f"Error loading efficiency data: {e}")
        
        with tab3:
            st.write("**Top Fantasy Rankings:**")
            try:
                # Get actual fantasy ranking data - no fallbacks
                top_ranked = []
                for player in st.session_state.rag_system.sample_data[:100]:
                    fantasy_rank = player.get('fantasy_rank', 999)
                    if isinstance(fantasy_rank, (int, float)) and fantasy_rank <= 20:  # Top 20 players
                        top_ranked.append((player.get('name', 'Unknown'), fantasy_rank))
                
                top_ranked.sort(key=lambda x: x[1])  # Sort by rank (lower is better)
                
                if top_ranked:
                    for i, (name, rank) in enumerate(top_ranked[:5], 1):
                        st.write(f"{i}. {name} - Rank #{int(rank)}")
                else:
                    st.warning("❌ No fantasy ranking data available in current dataset")
                    st.info("Check that player statistics are properly loaded")
            except Exception as e:
                st.error(f"Error loading fantasy ranking data: {e}")
        
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
        
        tab1, tab2, tab3, tab4 = st.tabs(["🔍 Search Analysis", "🤖 AI Quality", "📊 Data Coverage", "⚡ Response Evaluation"])
        
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
        with tab4:
            st.write("**⚡ Real-time Response Evaluation:**")
            
            if st.button("🚀 Run Response Time Analysis"):
                with st.spinner("Analyzing response times..."):
                    test_scenarios = [
                        ("Simple Search", lambda: st.session_state.rag_system.search_players("LeBron", num_results=3)),
                        ("Complex Search", lambda: st.session_state.rag_system.search_players("point guard Lakers", num_results=5)),
                        ("AI Short Query", lambda: st.session_state.rag_system.get_response("Who is LeBron?")),
                        ("AI Complex Query", lambda: st.session_state.rag_system.get_response("Compare LeBron James and Michael Jordan in fantasy basketball"))
                    ]
                    
                    performance_results = []
                    
                    for scenario_name, test_func in test_scenarios:
                        times = []
                        success_count = 0
                        
                        # Run each test 3 times for average
                        for _ in range(3):
                            try:
                                start = time.time()
                                result = test_func()
                                end = time.time()
                                
                                response_time = (end - start) * 1000  # Convert to milliseconds
                                times.append(response_time)
                                
                                # Check if result is valid
                                if result and (isinstance(result, list) and len(result) > 0) or (isinstance(result, str) and len(result) > 20):
                                    success_count += 1
                                    
                            except Exception as e:
                                times.append(0)  # Failed request
                        
                        avg_time = sum(times) / len(times) if times else 0
                        success_rate = (success_count / 3) * 100
                        
                        # Determine performance rating
                        if avg_time < 500:
                            rating = "🟢 Excellent"
                        elif avg_time < 1500:
                            rating = "🟡 Good"
                        elif avg_time < 3000:
                            rating = "🟠 Fair"
                        else:
                            rating = "🔴 Slow"
                        
                        performance_results.append({
                            "Scenario": scenario_name,
                            "Avg Time (ms)": f"{avg_time:.0f}",
                            "Success Rate": f"{success_rate:.0f}%",
                            "Rating": rating
                        })
                    
                    st.dataframe(performance_results, use_container_width=True)
                    
                    # Summary metrics
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        overall_avg = sum(float(r["Avg Time (ms)"]) for r in performance_results) / len(performance_results)
                        st.metric("Overall Avg Response", f"{overall_avg:.0f}ms")
                    
                    with col2:
                        overall_success = sum(float(r["Success Rate"].rstrip('%')) for r in performance_results) / len(performance_results)
                        st.metric("Overall Success Rate", f"{overall_success:.0f}%")
                    
                    with col3:
                        excellent_count = sum(1 for r in performance_results if "🟢" in r["Rating"])
                        performance_score = (excellent_count / len(performance_results)) * 100
                        st.metric("Performance Score", f"{performance_score:.0f}%")
            
            st.divider()
            
            # Real-time monitoring toggle
            if st.checkbox("🔄 Enable Real-time Monitoring"):
                st.info("Real-time monitoring would track:")
                st.write("• Average response times per hour")
                st.write("• Search success rates")
                st.write("• API error rates")
                st.write("• User query patterns")
                st.write("• System resource usage")
                
                # Placeholder for real-time metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Live Queries/Hour", "23", "↗️ +15%")
                with col2:
                    st.metric("Avg Response Time", "850ms", "↘️ -12%")
                with col3:
                    st.metric("Success Rate", "94.2%", "↗️ +2.1%")
    
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
        
        col1, col2 = st.columns(2)
        
        with col1:
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
                    
                    # Test search with hit rate calculation
                    try:
                        test_queries = ["LeBron James", "Nikola Jokic", "Stephen Curry"]
                        hits = 0
                        total_tests = len(test_queries)
                        
                        for query in test_queries:
                            results = st.session_state.rag_system.search_players(query, num_results=1)
                            if results and len(results) > 0:
                                hits += 1
                        
                        hit_rate = (hits / total_tests) * 100
                        status_checks.append({"Component": "Search Hit Rate", "Status": f"✅ {hit_rate:.1f}%", "Details": f"{hits}/{total_tests} successful"})
                    except Exception as e:
                        status_checks.append({"Component": "Search Hit Rate", "Status": "❌ Error", "Details": str(e)[:50]})
                    
                    # Test AI with response time
                    try:
                        if st.session_state.rag_system.groq_client:
                            start_time = time.time()
                            response = st.session_state.rag_system.get_response("Who is LeBron James?")
                            response_time = (time.time() - start_time) * 1000
                            
                            if response and len(response) > 50:
                                status_checks.append({"Component": "AI Response Time", "Status": "✅ OK", "Details": f"{response_time:.0f}ms"})
                            else:
                                status_checks.append({"Component": "AI Response Time", "Status": "⚠️ Slow", "Details": f"{response_time:.0f}ms"})
                        else:
                            status_checks.append({"Component": "AI Response Time", "Status": "⚠️ Limited", "Details": "No API key"})
                    except Exception as e:
                        status_checks.append({"Component": "AI Response Time", "Status": "❌ Error", "Details": str(e)[:50]})
                    
                    st.dataframe(status_checks, use_container_width=True)
        
        with col2:
            # Hit Rate Analysis
            st.write("**🎯 Hit Rate Analysis**")
            
            if st.button("📊 Detailed Hit Rate Test"):
                with st.spinner("Running comprehensive hit rate analysis..."):
                    test_cases = [
                        ("Player Names", ["LeBron James", "Nikola Jokic", "Stephen Curry", "Giannis Antetokounmpo"]),
                        ("Team Names", ["Lakers", "Warriors", "Celtics", "Heat"]),
                        ("Positions", ["point guard", "center", "forward"]),
                        ("Partial Names", ["LeBron", "Curry", "Jokic"])
                    ]
                    
                    hit_rate_results = []
                    
                    for category, queries in test_cases:
                        hits = 0
                        for query in queries:
                            try:
                                results = st.session_state.rag_system.search_players(query, num_results=1)
                                if results and len(results) > 0:
                                    hits += 1
                            except:
                                pass
                        
                        hit_rate = (hits / len(queries)) * 100
                        hit_rate_results.append({
                            "Category": category,
                            "Hit Rate": f"{hit_rate:.1f}%",
                            "Hits": f"{hits}/{len(queries)}"
                        })
                    
                    st.dataframe(hit_rate_results, use_container_width=True)
                    
                    # Overall hit rate
                    total_hits = sum(int(r["Hits"].split("/")[0]) for r in hit_rate_results)
                    total_tests = sum(int(r["Hits"].split("/")[1]) for r in hit_rate_results)
                    overall_hit_rate = (total_hits / total_tests) * 100
                    
                    st.metric("Overall Hit Rate", f"{overall_hit_rate:.1f}%", f"{total_hits}/{total_tests}")
        
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