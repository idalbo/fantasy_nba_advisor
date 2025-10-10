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
    initial_sidebar_state="collapsed"
)

# Custom CSS to hide sidebar
st.markdown("""
<style>
    .css-1d391kg {display: none;}
    .css-1aumxhk {display: none;}
    section[data-testid="stSidebar"] {display: none;}
    .stSidebar {display: none;}
</style>
""", unsafe_allow_html=True)

def main():
    st.title("🏀 Fantasy NBA Advisor")
    st.markdown("---")
    
    # Initialize the RAG system
    if 'rag_system' not in st.session_state:
        try:
            with st.spinner("Initializing NBA Advisor..."):
                st.session_state.rag_system = UnifiedFantasyNBARag()
            st.success("NBA Advisor initialized successfully!")
        except Exception as e:
            st.error(f"Failed to initialize NBA Advisor: {e}")
            return
    
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

if __name__ == "__main__":
    main()