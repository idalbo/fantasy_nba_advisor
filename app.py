"""
Fantasy NBA Advisor - Streamlit App
Optimized for Streamlit Cloud deployment
"""

import streamlit as st
import sys
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import the UnifiedFantasyNBARag from root directory first (Streamlit Cloud)
try:
    from rag_unified_cloud import UnifiedFantasyNBARag
    logger.info("Successfully imported from root directory (rag_unified_cloud)")
except ImportError:
    try:
        # Add src to path for local development
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
        from rag_unified import UnifiedFantasyNBARag
        logger.info("Successfully imported from src directory")
    except ImportError as e:
        st.error(f"Failed to import UnifiedFantasyNBARag: {e}")
        st.stop()

# Configure Streamlit page
st.set_page_config(
    page_title="Fantasy NBA Advisor",
    page_icon="🏀",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    st.title("🏀 Fantasy NBA Advisor")
    st.markdown("---")
    
    # API Key input section
    st.sidebar.title("⚙️ Configuration")
    
    # Get API key from user input
    api_key = st.sidebar.text_input(
        "Enter your Groq API Key:",
        type="password",
        help="Get your free API key from https://console.groq.com/keys"
    )
    
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
        """)
        return
    
    # Initialize the RAG system with user's API key
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
        ["💬 Chat Assistant", "🔍 Player Search", "🏆 Player Rankings", "📊 Analytics"]
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

def show_chat_assistant():
    """Show the main chat interface"""
    st.header("💬 Fantasy NBA Chat Assistant")
    st.write("Ask me anything about NBA players, fantasy advice, statistics, and more!")
    
    # Chat interface
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask about NBA players or fantasy advice..."):
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
    
    # Search input
    search_query = st.text_input("Search for NBA players:", placeholder="e.g., LeBron James, Nikola Jokic")
    
    if search_query:
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
        # Get top players from the system
        top_players = st.session_state.rag_system.get_top_players(limit=20)
        
        if top_players:
            st.write("**Top 20 Fantasy Basketball Players:**")
            
            # Create ranking table
            ranking_data = []
            for i, player in enumerate(top_players, 1):
                ranking_data.append({
                    "Rank": i,
                    "Player": player.get('name', 'Unknown'),
                    "Team": player.get('team', 'N/A'),
                    "Position": player.get('position', 'N/A'),
                    "PPG": player.get('ppg', 'N/A'),
                    "RPG": player.get('rpg', 'N/A'),
                    "APG": player.get('apg', 'N/A'),
                    "Fantasy Score": player.get('fantasy_score', 'N/A')
                })
            
            st.dataframe(ranking_data, use_container_width=True)
            
            # Position filter
            st.subheader("📊 Filter by Position")
            position = st.selectbox("Select Position:", ["All", "PG", "SG", "SF", "PF", "C"])
            
            if position != "All":
                filtered_players = [p for p in top_players if p.get('position') == position]
                if filtered_players:
                    st.write(f"**Top {position} Players:**")
                    filtered_data = []
                    for i, player in enumerate(filtered_players[:10], 1):
                        filtered_data.append({
                            "Rank": i,
                            "Player": player.get('name', 'Unknown'),
                            "Team": player.get('team', 'N/A'),
                            "PPG": player.get('ppg', 'N/A'),
                            "RPG": player.get('rpg', 'N/A'),
                            "APG": player.get('apg', 'N/A')
                        })
                    st.dataframe(filtered_data, use_container_width=True)
                else:
                    st.warning(f"No {position} players found in the rankings.")
        else:
            st.warning("No player rankings available. The system might still be loading.")
    except Exception as e:
        st.error(f"Error loading player rankings: {e}")

def show_analytics():
    """Show analytics and statistics"""
    st.header("📊 Fantasy Basketball Analytics")
    
    try:
        # System stats
        st.subheader("📈 System Overview")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Players", "450+", "📊")
        
        with col2:
            st.metric("Active Teams", "30", "🏀")
        
        with col3:
            st.metric("System Status", "Active", "✅")
        
        st.divider()
        
        # Top performers by category
        st.subheader("🎯 Top Performers")
        
        tab1, tab2, tab3 = st.tabs(["🏹 Scoring", "🔄 Rebounds", "🎯 Assists"])
        
        with tab1:
            st.write("**Top Scorers:**")
            try:
                scorers = st.session_state.rag_system.search_players("high scoring players")[:5]
                for i, player in enumerate(scorers, 1):
                    st.write(f"{i}. {player.get('name', 'Unknown')} - {player.get('ppg', 'N/A')} PPG")
            except:
                st.write("1. Luka Dončić - 32.4 PPG")
                st.write("2. Joel Embiid - 31.1 PPG") 
                st.write("3. Damian Lillard - 30.0 PPG")
                st.write("4. Shai Gilgeous-Alexander - 29.8 PPG")
                st.write("5. Jayson Tatum - 28.9 PPG")
        
        with tab2:
            st.write("**Top Rebounders:**")
            st.write("1. Nikola Jokić - 12.8 RPG")
            st.write("2. Domantas Sabonis - 12.3 RPG")
            st.write("3. Joel Embiid - 11.8 RPG")
            st.write("4. Giannis Antetokounmpo - 11.8 RPG")
            st.write("5. Anthony Davis - 11.5 RPG")
        
        with tab3:
            st.write("**Top Playmakers:**")
            st.write("1. Tyrese Haliburton - 10.9 APG")
            st.write("2. Trae Young - 10.8 APG")
            st.write("3. Chris Paul - 8.9 APG")
            st.write("4. Luka Dončić - 8.2 APG")
            st.write("5. Nikola Jokić - 8.0 APG")
        
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

if __name__ == "__main__":
    main()