import streamlit as stimport streamlit as stimport streamlit as st

import pandas as pd

import plotly.express as pximport pandas as pdimport os

import plotly.graph_objects as go

import jsonimport plotly.express as pximport json

import os

import sysimport plotly.graph_objects as goimport subprocess

import time

from datetime import datetimeimport jsonfrom datetime import datetime

import logging

from dotenv import load_dotenvimport osfrom src.rag import FantasyNBARag



# Import cloud-compatible RAG systemimport sys

try:

    from rag_cloud import FantasyNBARagimport time# Page configuration

except ImportError:

    st.error("Unable to import RAG system. Please check deployment configuration.")from datetime import datetimest.set_page_config(

    st.stop()

import logging    page_title="Fantasy NBA Advisor",

# Load environment variables

load_dotenv()from dotenv import load_dotenv    page_icon="🏀",



# Configure logging    layout="centered"

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)# Add src directory to path for imports)



# Page configurationsys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

st.set_page_config(

    page_title="Fantasy NBA Advisor",def save_interaction(query: str, response: str, search_results: list):

    page_icon="🏀",

    layout="wide",try:    """Save user interaction for monitoring"""

    initial_sidebar_state="expanded"

)    from src.rag import FantasyNBARag    try:



# Custom CSSexcept ImportError:        # Simple interaction logging without importing monitoring module

st.markdown("""

<style>    # Fallback for cloud deployment        interaction_data = {

    .main > div {

        padding-top: 2rem;    from rag import FantasyNBARag            "query": query,

    }

    .stAlert {            "response": response[:200] + "..." if len(response) > 200 else response,

        margin-top: 1rem;

    }# Load environment variables            "num_results": len(search_results),

</style>

""", unsafe_allow_html=True)load_dotenv()            "timestamp": datetime.now().isoformat()



def initialize_rag_system():        }

    """Initialize the RAG system with cloud-compatible settings"""

    try:# Configure logging        

        groq_api_key = st.session_state.get('groq_api_key') or os.getenv('GROQ_API_KEY')

        logging.basicConfig(level=logging.INFO)        # Ensure monitoring directory exists

        if not groq_api_key:

            return Nonelogger = logging.getLogger(__name__)        os.makedirs("monitoring", exist_ok=True)

            

        # Initialize with cloud mode enabled        

        rag = FantasyNBARag(groq_api_key=groq_api_key, cloud_mode=True)

        return rag# Page configuration        # Save to daily log file

        

    except Exception as e:st.set_page_config(        filename = f"monitoring/interactions_{datetime.now().strftime('%Y-%m-%d')}.jsonl"

        st.error(f"❌ **Error initializing system**: {str(e)}")

        return None    page_title="Fantasy NBA Advisor",        with open(filename, 'a') as f:



def setup_sidebar():    page_icon="🏀",            f.write(json.dumps(interaction_data) + '\n')

    """Setup the sidebar with API key input and information"""

    with st.sidebar:    layout="wide",            

        st.title("🏀 Fantasy NBA Advisor")

        st.markdown("---")    initial_sidebar_state="expanded"    except Exception as e:

        

        # API Key Input)        print(f"Monitoring error: {e}")

        st.subheader("🔑 API Configuration")

        groq_api_key = st.text_input(

            "Groq API Key",

            type="password",# Custom CSSdef run_evaluation():

            help="Get your free API key from https://console.groq.com",

            key="groq_api_key_input"st.markdown("""    """Run system evaluation"""

        )

        <style>    try:

        if groq_api_key:

            st.session_state['groq_api_key'] = groq_api_key    .main > div {        result = subprocess.run(

            st.success("✅ API key configured!")

                padding-top: 2rem;            ["python", "main.py", "evaluate"],

        if st.button("🔄 Reset API Key"):

            if 'groq_api_key' in st.session_state:    }            capture_output=True,

                del st.session_state['groq_api_key']

            st.rerun()    .stAlert {            text=True,

        

        st.markdown("---")        margin-top: 1rem;            cwd="/Users/igor.dalbo/local_dev/fantasy_nba_advisor"

        

        # App Information    }        )

        st.subheader("ℹ️ About")

        st.markdown("""    .chat-message {        return result.stdout, result.returncode == 0

        **Fantasy NBA Advisor** provides AI-powered insights for fantasy basketball.

                padding: 1rem;    except Exception as e:

        **Features:**

        - 🎯 Smart draft recommendations        border-radius: 0.5rem;        return f"Evaluation error: {str(e)}", False

        - 🔍 Player analysis

        - 💬 AI-powered advice        margin: 1rem 0;

        - 📊 Fantasy metrics

        """)    }def run_monitoring():

        

        st.markdown("---")    .user-message {    """Run monitoring report"""

        

        # Sample Queries        background-color: #e8f4f8;    try:

        st.subheader("💡 Try These Queries")

        st.markdown("""        border-left: 4px solid #1f77b4;        result = subprocess.run(

        - "Who should I pick at position 10?"

        - "Best centers for fantasy"    }            ["python", "main.py", "monitor"],

        - "Show me elite players"

        - "Draft strategy advice"    .assistant-message {            capture_output=True,

        """)

        background-color: #f0f8f0;            text=True,

def show_cloud_notice():

    """Show notice about cloud limitations"""        border-left: 4px solid #2ca02c;            cwd="/Users/igor.dalbo/local_dev/fantasy_nba_advisor"

    st.info("""

    🌐 **Streamlit Cloud Demo**: Limited functionality. For full features run locally with Docker.    }        )

    

    📋 [Setup Guide](https://github.com/idalbo/fantasy_nba_advisor/blob/main/SETUP_GUIDE.md) | </style>        return result.stdout, result.returncode == 0

    🔗 [GitHub](https://github.com/idalbo/fantasy_nba_advisor)

    """)""", unsafe_allow_html=True)    except Exception as e:



def show_demo_data():        return f"Monitoring error: {str(e)}", False

    """Show sample data and functionality"""

    st.subheader("📊 Elite Fantasy Players (2024-25)")def initialize_rag_system():

    

    # Sample data    """Initialize the RAG system with cloud-compatible settings"""def main():

    sample_players = {

        'Rank': [1, 2, 3, 5, 6, 7, 8, 10],    try:    st.title("🏀 Fantasy NBA Advisor")

        'Player': ['Nikola Jokić', 'Giannis Antetokounmpo', 'Shai Gilgeous-Alexander', 

                   'Anthony Davis', 'Victor Wembanyama', 'Luka Dončić',         # For Streamlit Cloud, we'll use a mock or simplified data source    

                   'Jayson Tatum', 'LeBron James'],

        'Position': ['C', 'PF', 'PG', 'PF/C', 'C', 'PG', 'SF/PF', 'SF/PF'],        # Since we can't run Qdrant server on Streamlit Cloud    # Simple API key input

        'Team': ['DEN', 'MIL', 'OKC', 'LAL', 'SAS', 'DAL', 'BOS', 'LAL'],

        'FPPM': [1.286, 1.221, 1.129, 1.069, 1.068, 1.020, 0.98, 0.95]        groq_api_key = st.session_state.get('groq_api_key') or os.getenv('GROQ_API_KEY')    api_key = st.text_input("🔑 Groq API Key", type="password", value=os.getenv("GROQ_API_KEY", ""))

    }

                if api_key:

    df = pd.DataFrame(sample_players)

    st.dataframe(df, use_container_width=True, hide_index=True)        if not groq_api_key:        os.environ["GROQ_API_KEY"] = api_key

    

    # FPPM Chart            st.warning("⚠️ **Groq API Key Required**: Please enter your API key in the sidebar to enable AI features.")    

    fig = px.bar(

        df,             return None    # Initialize chat history

        x='Player', 

        y='FPPM',                 if "messages" not in st.session_state:

        color='FPPM',

        title='Fantasy Points Per Minute - Elite Players',        # Initialize with cloud-compatible settings        st.session_state.messages = []

        color_continuous_scale='viridis'

    )        rag = FantasyNBARag(groq_api_key=groq_api_key, cloud_mode=True)    

    fig.update_layout(xaxis_tickangle=-45)

    st.plotly_chart(fig, use_container_width=True)        return rag    # Display chat messages



def show_chat_interface():            st.header("💬 NBA Chat")

    """Show the chat interface"""

    st.subheader("💬 AI Fantasy Advisor")    except Exception as e:    for message in st.session_state.messages:

    

    # Initialize chat history        st.error(f"❌ **Error initializing system**: {str(e)}")        with st.chat_message(message["role"]):

    if "messages" not in st.session_state:

        st.session_state.messages = []        st.info("💡 **Note**: This app works best with local Docker setup. For full functionality, please run locally using the setup guide.")            st.markdown(message["content"])

    

    # Display chat messages        return None    

    for message in st.session_state.messages:

        with st.chat_message(message["role"]):    # Tabs for monitoring and evaluation

            st.markdown(message["content"])

    def setup_sidebar():    tab1, tab2 = st.tabs(["📊 Monitor", "🎯 Evaluate"])

    # Chat input

    if prompt := st.chat_input("Ask about fantasy basketball..."):    """Setup the sidebar with API key input and information"""    

        # Add user message to chat history

        st.session_state.messages.append({"role": "user", "content": prompt})    with st.sidebar:    with tab1:

        with st.chat_message("user"):

            st.markdown(prompt)        st.title("🏀 Fantasy NBA Advisor")        st.header("📊 System Monitoring")

        

        # Generate response        st.markdown("---")        

        with st.chat_message("assistant"):

            if 'groq_api_key' not in st.session_state or not st.session_state.get('groq_api_key'):                col1, col2 = st.columns(2)

                response = """

                ⚠️ **API Key Required**: Enter your Groq API key in the sidebar for AI responses.        # API Key Input        

                

                **Get free key**: https://console.groq.com        st.subheader("🔑 API Configuration")        with col1:

                

                **Sample advice**:        groq_api_key = st.text_input(            if st.button("🔄 Generate Report", use_container_width=True):

                - Elite players: Jokić, Giannis, SGA, Wemby

                - Focus on FPPM (Fantasy Points Per Minute)            "Groq API Key",                with st.spinner("Generating monitoring report..."):

                - Consider injury history and team situation

                """            type="password",                    output, success = run_monitoring()

            else:

                # Get AI response            help="Get your free API key from https://console.groq.com",                    if success:

                try:

                    rag = initialize_rag_system()            key="groq_api_key_input"                        st.success("✅ Report generated!")

                    if rag:

                        with st.spinner("Getting AI response..."):        )                        st.text(output)

                            response = rag.get_response(prompt)

                    else:                            else:

                        response = "❌ Unable to initialize AI system."

                except Exception as e:        if groq_api_key:                        st.error("❌ Report failed")

                    response = f"❌ Error: {str(e)}"

                        st.session_state['groq_api_key'] = groq_api_key                        st.text(output)

            st.markdown(response)

                        st.success("✅ API key configured!")        

        # Add assistant response to chat history

        st.session_state.messages.append({"role": "assistant", "content": response})                with col2:



def main():        if st.button("🔄 Reset API Key"):            st.metric("System Status", "🟢 Online")

    """Main application function"""

    setup_sidebar()            st.session_state['groq_api_key'] = None            st.metric("Database", "570 Players")

    

    st.title("🏀 Fantasy NBA Advisor")            st.rerun()    

    st.markdown("*AI-powered fantasy basketball insights*")

                with tab2:

    show_cloud_notice()

            st.markdown("---")        st.header("🎯 System Evaluation")

    # Create tabs

    tab1, tab2, tab3 = st.tabs(["💬 AI Chat", "📊 Data", "ℹ️ About"])                

    

    with tab1:        # App Information        col1, col2 = st.columns(2)

        show_chat_interface()

            st.subheader("ℹ️ About")        

    with tab2:

        show_demo_data()        st.markdown("""        with col1:

    

    with tab3:        **Fantasy NBA Advisor** provides AI-powered insights for fantasy basketball using real NBA data.            if st.button("🧪 Run Evaluation", use_container_width=True):

        st.markdown("""

        ## 🏀 Fantasy NBA Advisor                        with st.spinner("Running evaluation tests..."):

        

        Advanced RAG application for fantasy basketball insights using real NBA data.        **Features:**                    output, success = run_evaluation()

        

        ### 🌟 Features        - 🎯 Smart draft recommendations                    if success:

        - **Real NBA Data**: 450+ players with fantasy rankings

        - **Smart Recommendations**: Context-aware draft suggestions        - 🔍 Player filtering and analysis                        # Extract score from output

        - **Player Filtering**: Removes "already taken" players

        - **AI Analysis**: Expert fantasy insights        - 💬 AI-powered advice                        lines = output.strip().split('\n')

        - **Draft Intelligence**: Position-specific recommendations

                - 📊 Fantasy metrics and rankings                        score_line = [line for line in lines if "Overall score:" in line]

        ### 🚀 Full Setup (Local)

                                        if score_line:

        ```bash

        git clone https://github.com/idalbo/fantasy_nba_advisor.git        **Note**: Full functionality requires local setup with Docker.                            score = score_line[0].split("Overall score:")[-1].strip()

        cd fantasy_nba_advisor

        make ingest-data        """)                            st.success(f"✅ Evaluation Score: {score}")

        make project-run

        ```                                else:

        

        ### 🔗 Links        st.markdown("---")                            st.success("✅ Evaluation completed")

        - [GitHub Repository](https://github.com/idalbo/fantasy_nba_advisor)

        - [Setup Guide](https://github.com/idalbo/fantasy_nba_advisor/blob/main/SETUP_GUIDE.md)                                st.text(output)

        - [Get Groq API Key](https://console.groq.com)

        """)        # Sample Queries                    else:



if __name__ == "__main__":        st.subheader("💡 Sample Queries")                        st.error("❌ Evaluation failed")

    main()
        st.markdown("""                        st.text(output)

        Try these queries:        

        - "Who should I pick at position 10?"        with col2:

        - "Best centers for fantasy"            st.metric("Last Score", "0.36", delta="Without LLM")

        - "luka and giannis are taken, who's next?"            st.metric("Best Score", "0.54", delta="With LLM")

        - "Show me sleeper picks"    

        """)    # Chat input (must be at the end, outside all containers)

            if prompt := st.chat_input("Ask about NBA players..."):

        st.markdown("---")        if not api_key:

                    st.error("❌ Please enter your Groq API key first")

        # Setup Guide            return

        st.subheader("🚀 Full Setup")            

        st.markdown("""        with st.chat_message("user"):

        For complete functionality with real-time data:            st.markdown(prompt)

                st.session_state.messages.append({"role": "user", "content": prompt})

        1. **Clone the repo**: `git clone https://github.com/idalbo/fantasy_nba_advisor.git`        

        2. **Run locally**: `make ingest-data && make project-run`        with st.chat_message("assistant"):

        3. **Access**: `http://localhost:8501`            with st.spinner("🤔 Analyzing..."):

                        try:

        See [Setup Guide](https://github.com/idalbo/fantasy_nba_advisor/blob/main/SETUP_GUIDE.md) for details.                    rag = FantasyNBARag()

        """)                    response, search_results = rag.rag(prompt)

                    st.markdown(response)

def show_cloud_notice():                    if search_results:

    """Show notice about cloud limitations"""                        st.info(f"📊 Based on {len(search_results)} players")

    st.info("""                    save_interaction(prompt, response, search_results)

    🌐 **Streamlit Cloud Demo**: This is a demo version running on Streamlit Cloud.                     st.session_state.messages.append({"role": "assistant", "content": response})

    For full functionality with live NBA data ingestion and vector search, please run the application locally using Docker.                except Exception as e:

                        error_msg = f"❌ Error: {str(e)}"

    📋 **Local Setup**: See the [Setup Guide](https://github.com/idalbo/fantasy_nba_advisor/blob/main/SETUP_GUIDE.md) for complete installation instructions.                    st.error(error_msg)

    """)                    save_interaction(prompt, error_msg, [])



def show_demo_data():if __name__ == "__main__":

    """Show sample data and functionality"""    main()
    st.subheader("📊 Sample Fantasy Data")
    
    # Sample player data
    sample_players = {
        'Player': ['Nikola Jokić', 'Giannis Antetokounmpo', 'Luka Dončić', 'Shai Gilgeous-Alexander', 'Anthony Davis'],
        'Position': ['C', 'PF', 'PG', 'PG', 'PF/C'],
        'FPPM': [1.286, 1.221, 1.020, 1.129, 1.069],
        'Fantasy Rank': [1, 2, 7, 3, 5],
        'Team': ['DEN', 'MIL', 'DAL', 'OKC', 'LAL']
    }
    
    df = pd.DataFrame(sample_players)
    st.dataframe(df, use_container_width=True)
    
    # Sample chart
    fig = px.bar(df, x='Player', y='FPPM', title='Fantasy Points Per Minute (FPPM) - Elite Players')
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)

def show_chat_interface():
    """Show the chat interface"""
    st.subheader("💬 AI Fantasy Advisor")
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask about fantasy basketball..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate response
        with st.chat_message("assistant"):
            if 'groq_api_key' not in st.session_state or not st.session_state.get('groq_api_key'):
                response = """
                ⚠️ **API Key Required**: Please enter your Groq API key in the sidebar to get AI-powered responses.
                
                For demo purposes, here are some general tips:
                - Elite players like Jokić, Giannis, and Luka are top picks
                - Look for high Fantasy Points Per Minute (FPPM) values
                - Consider player availability and injury history
                - Balance star players with consistent role players
                """
            else:
                # Try to get AI response
                try:
                    rag = initialize_rag_system()
                    if rag:
                        response = rag.get_response(prompt)
                    else:
                        response = "❌ Unable to initialize AI system. Please check your API key and try again."
                except Exception as e:
                    response = f"❌ Error getting AI response: {str(e)}\n\nThis may be due to cloud deployment limitations. For full functionality, please run locally."
            
            st.markdown(response)
            
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})

def main():
    """Main application function"""
    # Setup sidebar
    setup_sidebar()
    
    # Main content
    st.title("🏀 Fantasy NBA Advisor")
    
    # Show cloud notice
    show_cloud_notice()
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["💬 AI Chat", "📊 Demo Data", "ℹ️ About"])
    
    with tab1:
        show_chat_interface()
    
    with tab2:
        show_demo_data()
    
    with tab3:
        st.markdown("""
        ## 🏀 Fantasy NBA Advisor
        
        An advanced RAG (Retrieval-Augmented Generation) application that provides expert insights 
        and advice for fantasy NBA players using real NBA data.
        
        ### 🌟 Key Features
        - **Real NBA Data**: 450+ players with complete fantasy rankings
        - **Smart Recommendations**: Context-aware draft suggestions
        - **Player Filtering**: Removes "already taken" players
        - **AI Analysis**: Conversational responses with expert insights
        - **Fantasy Metrics**: FPPM, fantasy points, availability scores
        
        ### 🚀 Full Local Setup
        
        For complete functionality:
        
        ```bash
        git clone https://github.com/idalbo/fantasy_nba_advisor.git
        cd fantasy_nba_advisor
        make ingest-data
        make project-run
        ```
        
        ### 📋 Requirements
        - Docker and Docker Compose
        - Groq API key (free from console.groq.com)
        - 4GB RAM, 2GB storage
        
        ### 🔗 Links
        - [GitHub Repository](https://github.com/idalbo/fantasy_nba_advisor)
        - [Setup Guide](https://github.com/idalbo/fantasy_nba_advisor/blob/main/SETUP_GUIDE.md)
        - [Get Groq API Key](https://console.groq.com)
        """)

if __name__ == "__main__":
    main()