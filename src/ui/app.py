import streamlit as st
import asyncio
import logging
import sys
import os
import traceback
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Try to import multi_agent module
try:
    from multi_agent import run_multi_agent
    MULTI_AGENT_AVAILABLE = True
    print("✅ Successfully imported multi_agent module")
except ImportError as e:
    MULTI_AGENT_AVAILABLE = False
    print(f"❌ Failed to import multi_agent: {e}")
    traceback.print_exc()

def display_chat_history(chat_history):
    """Display chat history with improved formatting."""
    if not chat_history:
        st.info("💬 No messages yet. Start a conversation!")
        return
    
    for i, chat in enumerate(chat_history):
        role = chat.get("role", "unknown").lower()
        message = chat.get("message", "")
        
        if role == "user":
            st.markdown(f"""
            <div class="user-message">
                <strong>👤 You:</strong><br>
                {message}
            </div>
            """, unsafe_allow_html=True)
            
        elif role == "system":
            st.error(f"🚨 System: {message}")
            
        else:
            # Format agent name for display
            agent_icons = {
                "businessanalyst": "📊",
                "softwareengineer": "👨‍💻", 
                "productowner": "🎯",
                "assistant": "🤖"
            }
            icon = agent_icons.get(role.lower(), "🤖")
            display_name = role.replace("assistant", "Assistant").title()
            
            st.markdown(f"""
            <div class="agent-message">
                <strong>{icon} {display_name}:</strong><br>
                {message.replace(chr(10), '<br>')}
            </div>
            """, unsafe_allow_html=True)

def main():
    """Main function to run the app."""
    st.set_page_config(
        page_title="Multi-Agent Web Development System", 
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS for better styling
    st.markdown("""
    <style>
    .stTextInput > div > div > input {
        background-color: #f0f2f6;
        border: 2px solid #e1e5e9;
        border-radius: 10px;
        padding: 10px;
    }
    .stButton > button {
        background-color: #ff4b4b;
        color: white;
        border-radius: 10px;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: 600;
    }
    .agent-message {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 10px;
        border-left: 4px solid #ff4b4b;
        background-color: #f8f9fa;
    }
    .user-message {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 10px;
        border-left: 4px solid #0066cc;
        background-color: #e3f2fd;
    }
    .success-message {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 10px;
        border-left: 4px solid #4caf50;
        background-color: #e8f5e8;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Title and description
    st.title("🤖 Multi-Agent Web Development System")
    
    # Show system status in sidebar
    st.sidebar.markdown("### 📊 System Status")
    if MULTI_AGENT_AVAILABLE:
        st.sidebar.success("✅ Multi-Agent System: Available")
    else:
        st.sidebar.error("❌ Multi-Agent System: Not Available")
        st.sidebar.info("Make sure multi_agent.py is in the same directory and all dependencies are installed.")
    
    # Instructions
    st.markdown("""
    **How it works:**
    1. **Business Analyst** 📊 - Analyzes your requirements
    2. **Software Engineer** 👨‍💻 - Creates the web application 
    3. **Product Owner** 🎯 - Reviews and approves the final code
    
    **Instructions:** Describe what web application you want to build. Be specific about features, styling, and functionality.
    
    **Example:** *"Create a todo app with add/delete functionality, modern design, and local storage"*
    """)
    
    # Check if multi-agent is available
    if not MULTI_AGENT_AVAILABLE:
        st.error("❌ Multi-Agent functionality is not available!")
        st.info("""
        **Troubleshooting:**
        - Make sure `multi_agent.py` is in the same directory as `app.py`
        - Verify all Azure OpenAI environment variables are set in your `.env` file
        - Install required packages: `pip install semantic-kernel python-dotenv`
        """)
        return
    
    # Initialize session state
    if "multi_agent_history" not in st.session_state:
        st.session_state.multi_agent_history = []
    
    if "multi_agent_processing" not in st.session_state:
        st.session_state.multi_agent_processing = False
    
    # Header section with reset button
    col1, col2 = st.columns([4, 1])
    with col2:
        if st.button("🔄 Reset", help="Clear conversation history"):
            st.session_state.multi_agent_history = []
            st.rerun()
    
    # Display chat history
    display_chat_history(st.session_state.multi_agent_history)
    
    # Show processing status if needed
    if st.session_state.multi_agent_processing:
        st.info("🔄 **Processing in progress...** Please wait for agents to complete their work.")
    
    # Chat input form
    with st.form(key="multi_agent_form", clear_on_submit=True):
        col1, col2 = st.columns([5, 1])
        with col1:
            user_input = st.text_input(
                "Message", 
                placeholder="Describe the web application you want to build...",
                key="user_input_multi_agent",
                label_visibility="collapsed"
            )
        with col2:
            send_clicked = st.form_submit_button("Send 📤", use_container_width=True)
        
        if send_clicked and user_input.strip() and not st.session_state.multi_agent_processing:
            try:
                st.session_state.multi_agent_processing = True
                
                # Add user message immediately
                st.session_state.multi_agent_history.append({
                    "role": "user", 
                    "message": user_input.strip()
                })
                
                # Show processing status
                with st.spinner("🤖 Agents are collaborating... This may take a few minutes."):
                    st.info("💡 **What's happening:**\n- Business Analyst is analyzing requirements\n- Software Engineer is coding\n- Product Owner is reviewing")
                    
                    # Run multi-agent system
                    try:
                        result = asyncio.run(run_multi_agent(user_input.strip()))
                        
                        # Process results
                        if result and isinstance(result, list):
                            for response in result:
                                if isinstance(response, dict) and "role" in response and "content" in response:
                                    # Skip user messages (already added)
                                    if response["role"].lower() != "user":
                                        st.session_state.multi_agent_history.append({
                                            "role": response["role"],
                                            "message": response["content"]
                                        })
                        else:
                            st.warning("⚠️ No response received from agents")
                            
                    except Exception as e:
                        st.error(f"❌ Multi-agent system error: {str(e)}")
                        st.session_state.multi_agent_history.append({
                            "role": "system",
                            "message": f"Error occurred: {str(e)}"
                        })
                        logging.error(f"Multi-agent error: {e}")
                        traceback.print_exc()
                
                st.session_state.multi_agent_processing = False
                st.rerun()
                
            except Exception as e:
                st.session_state.multi_agent_processing = False
                st.error(f"❌ An error occurred: {str(e)}")
                logging.error(f"Form submission error: {e}")
                traceback.print_exc()
    
    # Footer
    st.markdown("---")
    st.markdown("🚀 **AI Workshop for Developers** - Powered by Multi-Agent AI System")

if __name__ == "__main__":
    main()