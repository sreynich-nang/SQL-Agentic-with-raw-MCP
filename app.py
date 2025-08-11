# app.py
"""Main Streamlit application for AI SQL Dashboard Agent"""

import streamlit as st
import asyncio
import sys
import os
from typing import List, Dict, Any

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.chat_agent import run_agent
from agents.dashboard_agent import run_dashboard_agent
from utils.display import display_html_dashboard
from utils.env_utils import load_env, check_env_vars

load_env()

def check_environment():
    """Check if all required environment variables are set"""
    required_vars = [
        'DB_HOST', 'DB_PORT', 'DB_USERNAME', 'DB_PASSWORD', 'DB_NAME',
        'MODEL_ID', 'MODEL_API_KEY'
    ]
    
    try:
        check_env_vars(required_vars)
        return True, "Environment configured correctly"
    except ValueError as e:
        return False, str(e)

def initialize_session_state():
    """Initialize Streamlit session state variables"""
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'dashboard_html' not in st.session_state:
        st.session_state.dashboard_html = None
    if 'dashboard_generated' not in st.session_state:
        st.session_state.dashboard_generated = False

async def handle_chat_message(user_input: str) -> str:
    """Handle chat message asynchronously"""
    try:
        response = await run_agent(user_input)
        return response
    except Exception as e:
        return f"Error: {str(e)}"

async def handle_dashboard_generation() -> str:
    """Handle dashboard generation asynchronously"""
    try:
        html_content = await run_dashboard_agent()
        return html_content
    except Exception as e:
        return f"""
        <html>
        <head><title>Error</title></head>
        <body>
            <h1>Dashboard Generation Failed</h1>
            <p>Error: {str(e)}</p>
            <p>Please ensure the MCP server is running and the database is accessible.</p>
        </body>
        </html>
        """

def run_async(coro):
    """Helper to run async functions in Streamlit"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(coro)

def main():
    """Main Streamlit application"""
    st.set_page_config(
        page_title="AI SQL Dashboard Agent",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session state
    initialize_session_state()
    
    # Sidebar for configuration and status
    with st.sidebar:
        st.title("🤖 AI SQL Dashboard")
        st.markdown("---")
        
        # Environment status
        env_ok, env_message = check_environment()
        if env_ok:
            st.success("Environment configured")
        else:
            st.error(f"{env_message}")
            st.info("Please check your .env file configuration")
        
        st.markdown("---")
        
        # Model info
        model_id = os.getenv('MODEL_ID', 'Not configured')
        st.info(f"**Model:** {model_id}")
        
        # Database info  
        db_name = os.getenv('DB_NAME', 'Not configured')
        db_host = os.getenv('DB_HOST', 'Not configured')
        st.info(f"**Database:** {db_name}@{db_host}")
        
        st.markdown("---")
        
        # Instructions
        st.markdown("""
        ### Instructions:
        1. **Chat Tab**: Ask natural language questions about your database
        2. **Dashboard Tab**: Generate interactive dashboards
        
        ### Prerequisites:
        - MCP server running on port 8000
        - Database accessible and populated
        - Valid API keys in .env file
        """)
        
        # Clear chat button
        if st.button("🗑️ Clear Chat History"):
            st.session_state.messages = []
            st.rerun()
    
    # Main content area
    st.title("AI SQL Dashboard Agent")
    st.markdown("Ask questions about your database or generate interactive dashboards!")
    
    chat_tab, dashboard_tab, about_tab = st.tabs(["💬 Chat", "📊 Dashboard", "ℹ️ About"]) # Create tabs
    
    # Chat Tab
    with chat_tab:
        st.header("Chat with your Database")
        
        if not env_ok:
            st.error("Please configure your environment variables before using the chat feature.")
        else:
            # Display chat messages
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
            
            # Chat input
            if prompt := st.chat_input("Ask a question about your database..."):
                # Add user message to chat history
                st.session_state.messages.append({"role": "user", "content": prompt})
                
                # Display user message
                with st.chat_message("user"):
                    st.markdown(prompt)
                
                # Generate and display assistant response
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        try:
                            response = run_async(handle_chat_message(prompt))
                            st.markdown(response)
                            
                            # Add assistant response to chat history
                            st.session_state.messages.append({"role": "assistant", "content": response})
                        
                        except Exception as e:
                            error_msg = f"Error processing your request: {str(e)}"
                            st.error(error_msg)
                            st.session_state.messages.append({"role": "assistant", "content": error_msg})
    
    # Dashboard Tab
    with dashboard_tab:
        st.header("Generate Database Dashboard")
        
        if not env_ok:
            st.error("Please configure your environment variables before generating dashboards.")
        else:
            col1, col2 = st.columns([1, 4])
            
            with col1:
                if st.button("🔄 Generate Dashboard", type="primary"):
                    with st.spinner("Analyzing database and generating dashboard..."):
                        try:
                            st.session_state.dashboard_html = run_async(handle_dashboard_generation())
                            st.session_state.dashboard_generated = True
                            st.success("Dashboard generated successfully!")
                        except Exception as e:
                            st.error(f"Failed to generate dashboard: {str(e)}")
                
                if st.session_state.dashboard_generated and st.button("📥 Download HTML"):
                    if st.session_state.dashboard_html:
                        st.download_button(
                            label="Download Dashboard HTML",
                            data=st.session_state.dashboard_html,
                            file_name="dashboard.html",
                            mime="text/html"
                        )
            
            with col2:
                if st.session_state.dashboard_generated and st.session_state.dashboard_html:
                    st.markdown("### Generated Dashboard")
                    display_html_dashboard(st.session_state.dashboard_html, height=700)
                else:
                    st.info("Click 'Generate Dashboard' to create an interactive dashboard from your database.")
    
    # About Tab
    with about_tab:
        st.header("About AI SQL Dashboard Agent")
        
        st.markdown("""
        This application demonstrates an AI-powered SQL dashboard system that can:
        
        ### Features:
        - **Natural Language Queries**: Ask questions in plain English and get SQL results
        - **Automatic Dashboard Generation**: AI analyzes your database and creates visualizations
        - **Secure Database Access**: Read-only access through MCP (Model Context Protocol) server
        - **Multi-Model Support**: Works with Gemini 1.5-Flash models
        
        ### Architecture:
        1. **Streamlit Frontend**: User interface for chat and dashboard display
        2. **AI Agents**: Convert natural language to SQL and generate dashboards
        3. **MCP SQL Server**: read-only database access layer
        4. **PostgreSQL Database**: Your data source
        
        ### Setup Requirements:
        - PostgreSQL database with sample data
        - MCP server running on localhost:8000
        - Valid API keys for your chosen LLM provider
        - Properly configured .env file
        
        ### Security:
        - Only SELECT queries are allowed (no data modification)
        - Schema-level validation of all queries
        - Timeout protection for long-running queries
        
        ### Technology Stack:
        - **Frontend**: Streamlit
        - **Backend**: Python with asyncio
        - **Database**: PostgreSQL with asyncpg
        - **AI Models**: Gemini 1.5-Flash API
        - **Protocol**: MCP (Model Context Protocol)
        """)
        
        st.markdown("---")
        st.markdown("**Version**: 1.0.0 | **License**: MIT")

if __name__ == "__main__":
    main()