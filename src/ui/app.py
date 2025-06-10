import streamlit as st
import asyncio
import logging
import sys
import os
import traceback as tb_module
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)

# Add            if st.but            if st.button("🔄 Reset", help="Clear conversation history"):on("⏹️ Stop & Reset", help="Stop current agent processing and clear conversation", type="primary"):the current directory to Python path
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
    tb_module.print_exc()

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
            
            # Escape HTML content to display as text
            import html
            escaped_message = html.escape(message)
            
            st.markdown(f"""
            <div class="agent-message">
                <strong>{icon} {display_name}:</strong><br>
                <pre style="white-space: pre-wrap; background: #f8f9fa; padding: 10px; border-radius: 5px; margin-top: 5px;">{escaped_message}</pre>
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
        
    if "reset_requested" not in st.session_state:
        st.session_state.reset_requested = False
        
    if "awaiting_approval" not in st.session_state:
        st.session_state.awaiting_approval = False
        
    if "approval_data" not in st.session_state:
        st.session_state.approval_data = None
        
    if "deployment_result" not in st.session_state:
        st.session_state.deployment_result = None
        
    if "safety_limit_reached" not in st.session_state:
        st.session_state.safety_limit_reached = False
    
    if "should_auto_scroll" not in st.session_state:
        st.session_state.should_auto_scroll = False
    
    # Header section with reset button
    col1, col2 = st.columns([4, 1])
    with col2:
        # Show different button text/behavior based on processing state
        if st.session_state.multi_agent_processing:
            # If agents are running, offer to stop them
            if st.button("� Stop & Reset", help="Stop current agent processing and clear conversation", type="primary"):
                # Set reset request flag - this will be checked during processing
                st.session_state.reset_requested = True
                st.session_state.multi_agent_processing = False  # Signal to stop processing
                
                # Also clear any pending request to prevent restart
                if hasattr(st.session_state, 'pending_request'):
                    delattr(st.session_state, 'pending_request')
                
                # Reset ALL session state variables immediately
                st.session_state.multi_agent_history = []
                st.session_state.awaiting_approval = False
                st.session_state.approval_data = None
                st.session_state.deployment_result = None
                st.session_state.safety_limit_reached = False
                st.session_state.should_auto_scroll = False
                st.session_state.reset_requested = False  # Clear the flag after reset
                st.success("⏹️ **Agent processing stopped and conversation reset!**")
                st.rerun()
        else:
            # If agents are not running, show normal reset button
            if st.button("�🔄 Reset", help="Clear conversation history"):
                # Reset ALL session state variables to ensure clean restart
                st.session_state.multi_agent_history = []
                st.session_state.multi_agent_processing = False  # CRITICAL: Reset processing state
                st.session_state.awaiting_approval = False
                st.session_state.approval_data = None
                st.session_state.deployment_result = None
                st.session_state.safety_limit_reached = False
                st.session_state.should_auto_scroll = False
                st.session_state.reset_requested = False
                st.rerun()
    
    # Display chat history
    display_chat_history(st.session_state.multi_agent_history)
    
    # Show deployment result if available
    if st.session_state.deployment_result:
        st.markdown("---")
        st.markdown("### 🎉 **DEPLOYMENT COMPLETED!**")
        st.success("✅ Your web application has been successfully deployed to GitHub!")
        
        result_data = st.session_state.deployment_result
        
        # Create columns for better layout
        col1, col2 = st.columns(2)
        
        with col1:
            if "github_link" in result_data:
                st.markdown(f"### 🔗 **[View Your Live Web App]({result_data['github_link']})**")
                st.caption("🌐 GitHub Pages website")
                
                st.info("💡 **If you see an old version:** GitHub Pages can take 5-10 minutes to update. "
                       "Try refreshing the page or use Ctrl+F5 to bypass browser cache. "
                       "The latest code is always in your GitHub repository.")
                
                # Commented out - GitHub Pages setup no longer needed  
                # st.info("💡 **If you get a 404 error:** GitHub Pages may not be enabled yet. "
                #        "Go to your repository → Settings → Pages → Select 'Deploy from a branch' → Choose 'main' branch.")
                
                # Commented out - GitHub Pages setup link no longer needed
                # repo_url = result_data.get('repo_url', '')
                # if repo_url:
                #     if repo_url.endswith('.git'):
                #         repo_url = repo_url[:-4]
                #     settings_url = f"{repo_url}/settings/pages"
                #     st.markdown(f"🔧 **[Enable GitHub Pages Here]({settings_url})**")
            
            # Repository link
            repo_url = result_data.get('repo_url', '')
            if repo_url:
                st.markdown(f"📂 **[Repository]({repo_url})**")
                
                # Use the source link if available, otherwise construct it
                if "github_source_link" in result_data:
                    source_link = result_data["github_source_link"]
                else:
                    # Fallback: construct source link
                    if repo_url.endswith('.git'):
                        repo_url = repo_url[:-4]
                    source_link = f"{repo_url}/blob/main/index.html"
                
                st.markdown(f"📄 **[View Source Code on GitHub]({source_link})**")
                
                # Use raw link if available, otherwise construct it
                if "github_raw_link" in result_data:
                    download_link = result_data["github_raw_link"]
                else:
                    # Fallback: construct raw link
                    if repo_url.endswith('.git'):
                        repo_url = repo_url[:-4]
                    download_link = f"{repo_url}/raw/main/index.html"
                
                st.markdown(f"⬇️ **[View/Download from GitHub]({download_link})**")
                st.caption("Opens the file - use browser's 'Save As' to download")
                st.info("💡 **To download:** Right-click the link above → 'Save link as...' or visit the link and use Ctrl+S")
        
        with col2:
            st.markdown("### 📥 **Download Options**")
            
            # Download button for HTML file
            if "file_size" in result_data:
                st.info(f"📊 File size: {result_data['file_size']}")
            
            # Try to read the HTML file for download - with better error handling
            html_content = None
            try:
                import os
                # First, try the current working directory
                html_file_path = os.path.join(os.getcwd(), "index.html")
                if os.path.exists(html_file_path):
                    with open(html_file_path, 'r', encoding='utf-8') as f:
                        html_content = f.read()
                else:
                    # Try the project root directory
                    project_root = os.path.dirname(os.path.dirname(__file__))
                    html_file_path = os.path.join(project_root, "index.html")
                    if os.path.exists(html_file_path):
                        with open(html_file_path, 'r', encoding='utf-8') as f:
                            html_content = f.read()
            except Exception as e:
                st.warning(f"Could not read local HTML file: {str(e)}")
            
            # Fallback to stored HTML content if local file not available
            if not html_content and "html_content" in result_data:
                html_content = result_data["html_content"]
            
            if html_content:
                st.download_button(
                    label="💾 Download HTML File",
                    data=html_content,
                    file_name="index.html",
                    mime="text/html",
                    help="Download the HTML file to your computer"
                )
            else:
                st.warning("📁 Local HTML file not available for download")
                st.info("💡 Use the 'View/Download from GitHub' link above (right-click → 'Save link as...')")
            
        st.balloons()
        
        if st.button("🔄 Start New Project"):
            # Reset ALL session state variables to ensure clean restart
            st.session_state.multi_agent_history = []
            st.session_state.multi_agent_processing = False  # CRITICAL: Reset processing state
            st.session_state.awaiting_approval = False
            st.session_state.approval_data = None
            st.session_state.deployment_result = None
            st.session_state.safety_limit_reached = False
            st.session_state.should_auto_scroll = False
            st.session_state.reset_requested = False
            st.rerun()
        
        st.markdown("---")
    
    # Show approval interface if needed
    if st.session_state.awaiting_approval and st.session_state.approval_data:
        st.markdown("---")
        
        # Scroll button at the very top - COMMENTED OUT (doesn't work properly in Streamlit)
        # col1, col2 = st.columns([4, 1])
        # with col1:
        #     st.markdown("### 🎯 **Project Ready for Approval!**")
        # with col2:
        #     scroll_clicked = st.button("⬇️ To Bottom", key="scroll_to_approval", type="secondary")
        
        st.markdown("### 🎯 **Project Ready for Approval!**")
        st.success("The Product Owner has reviewed the code and says it's ready!")
        
        # Auto-scroll script - COMMENTED OUT (doesn't work properly in Streamlit)
        # if scroll_clicked or st.session_state.should_auto_scroll:
        #     st.session_state.should_auto_scroll = False  # Reset flag
        #     st.markdown("""
        #     <script>
        #     // Use a more reliable scroll method for Streamlit
        #     function scrollToPageBottom() {
        #         // Wait for the page to fully render
        #         setTimeout(function() {
        #             // Try different scroll approaches
        #             var maxScroll = Math.max(
        #                 document.body.scrollHeight,
        #                 document.body.offsetHeight,
        #                 document.documentElement.clientHeight,
        #                 document.documentElement.scrollHeight,
        #                 document.documentElement.offsetHeight
        #             );
        #             
        #             // Direct scroll to the calculated bottom
        #             window.scrollTo(0, maxScroll);
        #             
        #             // If in an iframe (like Streamlit), also try parent
        #             if (window.parent && window.parent !== window) {
        #                 try {
        #                     var parentMaxScroll = Math.max(
        #                         window.parent.document.body.scrollHeight,
        #                         window.parent.document.body.offsetHeight,
        #                         window.parent.document.documentElement.clientHeight,
        #                         window.parent.document.documentElement.scrollHeight,
        #                         window.parent.document.documentElement.offsetHeight
        #                     );
        #                     window.parent.scrollTo(0, parentMaxScroll);
        #                 } catch(e) {
        #                     // Ignore cross-origin errors
        #                 }
        #             }
        #         }, 300);
        #     }
        #     scrollToPageBottom();
        #     </script>
        #     """, unsafe_allow_html=True)
        
        # st.info("⬇️ **Scroll down to see the approval form below, or use the button above!**")
        
        # Clear warning about the requirement
        st.error("🚨 **MANUAL DECISION REQUIRED:** Type 'APPROVED' to deploy to GitHub, or anything else to reject and start fresh!")
        st.info("💡 **How it works:**\n- Type 'APPROVED' → Deploys to GitHub\n- Type anything else (like 'no', 'reject', 'cancel') → Rejects project and starts new\n- This ensures you have full control over deployments")
        
        # Add examples for clarity
        with st.expander("📋 **Examples of what to type:**"):
            col1, col2 = st.columns(2)
            with col1:
                st.success("**✅ To APPROVE and deploy:**\n- `APPROVED`\n- `approved`\n- `Approved`")
            with col2:
                st.warning("**❌ To REJECT and start new:**\n- `no`\n- `reject`\n- `cancel`\n- `start over`\n- Any other text")
        
        # Use a form for terminal-like behavior
        with st.form(key="approval_form"):
            approval_text = st.text_input(
                "⌨️ Make your decision:",
                placeholder="Type APPROVED to deploy, or anything else to reject...",
                key="approval_input_form",
                help="Type 'APPROVED' to deploy to GitHub, or any other text to reject and start fresh"
            )
            
            # Auto-focus the input field for easier typing
            st.markdown("""
            <script>
            setTimeout(function() {
                // Find the approval input field and focus it
                var inputs = window.parent.document.querySelectorAll('input[aria-label*="Type \'APPROVED\'"]');
                if (inputs.length > 0) {
                    inputs[0].focus();
                    inputs[0].select(); // Also select any existing text
                }
                
                // Fallback: try to find by placeholder text
                if (inputs.length === 0) {
                    var allInputs = window.parent.document.querySelectorAll('input[placeholder*="APPROVED"]');
                    if (allInputs.length > 0) {
                        allInputs[0].focus();
                        allInputs[0].select();
                    }
                }
            }, 500);
            </script>
            """, unsafe_allow_html=True)
            
            # Single submit button that handles both approval and rejection
            submitted = st.form_submit_button("✅ Submit Decision", use_container_width=True)
            
            if submitted:
                if approval_text.strip().upper() == "APPROVED":
                    with st.spinner("🚀 Deploying to GitHub..."):
                        st.info(f"✅ User typed '{approval_text.strip()}' - Proceeding with deployment...")
                        
                        # Enhanced debugging section
                        with st.expander("🔍 **Debug Information**", expanded=True):
                            st.write("📋 **Environment Check:**")
                            import os
                            env_vars = ['GITHUB_PAT', 'GITHUB_USERNAME', 'GITHUB_REPO_URL']
                            for var in env_vars:
                                value = os.getenv(var)
                                if var == 'GITHUB_PAT' and value:
                                    st.write(f"   🔐 {var}: {'*' * 8}...{value[-4:]} (masked)")
                                elif value:
                                    st.write(f"   ✅ {var}: {value}")
                                else:
                                    st.write(f"   ❌ {var}: NOT SET")
                            
                            # Check if running in Azure
                            azure_indicators = ['WEBSITE_SITE_NAME', 'WEBSITE_RESOURCE_GROUP', 'APPSETTING_WEBSITE_SITE_NAME']
                            in_azure = any(os.getenv(var) for var in azure_indicators)
                            st.write(f"   🌐 Running in Azure: {in_azure}")
                            
                            st.write(f"\n📋 **Session State:**")
                            st.write(f"   Chat history length: {len(st.session_state.approval_data) if st.session_state.approval_data else 0}")
                            st.write(f"   Awaiting approval: {st.session_state.awaiting_approval}")
                            st.write(f"   Has deployment result: {st.session_state.deployment_result is not None}")
                        
                        try:
                            from multi_agent import handle_approval
                            
                            st.write("🔍 **Starting approval process...**")
                            
                            html_code, result_message = asyncio.run(
                                handle_approval(st.session_state.approval_data, approval_text.strip())
                            )
                            
                            st.write("🔍 **Approval process completed:**")
                            st.write(f"   HTML code length: {len(html_code) if html_code else 0}")
                            st.write(f"   Result message length: {len(result_message) if result_message else 0}")
                            st.write(f"   Result preview: {result_message[:200]}{'...' if len(result_message or '') > 200 else ''}")
                            
                            if html_code:
                                # Store deployment result for persistent display
                                deployment_data = {
                                    "success": True,
                                    "message": result_message,
                                    "file_size": f"{len(html_code)} characters",
                                    "html_content": html_code  # Store HTML content for download
                                }
                                
                                # Extract GitHub links from result message
                                github_link = None
                                github_source_link = None
                                github_raw_link = None
                                
                                if "View your live app:" in result_message:
                                    github_link = result_message.split("View your live app: ")[1].split("\n")[0]
                                if "View source code:" in result_message:
                                    github_source_link = result_message.split("View source code: ")[1].split("\n")[0]
                                if "Direct download:" in result_message:
                                    github_raw_link = result_message.split("Direct download: ")[1].split("\n")[0]
                                
                                if github_link:
                                    deployment_data["github_link"] = github_link
                                if github_source_link:
                                    deployment_data["github_source_link"] = github_source_link
                                if github_raw_link:
                                    deployment_data["github_raw_link"] = github_raw_link
                                
                                # Extract repo URL
                                import os
                                repo_url = os.getenv('GITHUB_REPO_URL', '')
                                if repo_url:
                                    deployment_data["repo_url"] = repo_url
                                
                                st.write("🔍 **Storing deployment result:**")
                                st.write(f"   Keys: {list(deployment_data.keys())}")
                                st.write(f"   GitHub link: {deployment_data.get('github_link', 'Not found')}")
                                st.write(f"   Repo URL: {deployment_data.get('repo_url', 'Not found')}")
                                
                                st.session_state.deployment_result = deployment_data
                                st.success("🎉 **DEPLOYMENT SUCCESSFUL!** Check above for details.")
                            else:
                                st.error(f"❌ No HTML code returned: {result_message}")
                                
                        except Exception as e:
                            error_details = tb_module.format_exc()
                            st.error(f"❌ Deployment error: {str(e)}")
                            
                            with st.expander("🔍 **Full Error Details**", expanded=False):
                                st.code(error_details)
                            
                        st.session_state.awaiting_approval = False
                        st.session_state.approval_data = None
                        
                        st.write("🔍 **Session state after approval:**")
                        st.write(f"   deployment_result exists: {st.session_state.deployment_result is not None}")
                        st.write(f"   awaiting_approval: {st.session_state.awaiting_approval}")
                        
                        st.write("🔄 **Rerunning Streamlit...**")
                        st.rerun()
                else:
                    # Any input other than "APPROVED" is treated as rejection
                    if approval_text.strip():  # If user typed something
                        st.warning(f"❌ **PROJECT REJECTED:** You typed '{approval_text.strip()}' instead of 'APPROVED'")
                        st.info("🔄 **Starting fresh:** Since you didn't approve, we'll start a new project...")
                        
                        # Reset ALL session state variables for a new project
                        st.session_state.multi_agent_history = []
                        st.session_state.multi_agent_processing = False
                        st.session_state.awaiting_approval = False
                        st.session_state.approval_data = None
                        st.session_state.deployment_result = None
                        st.session_state.safety_limit_reached = False
                        st.session_state.should_auto_scroll = False
                        st.session_state.reset_requested = False
                        
                        st.success("✨ **Ready for new project!** You can now enter a new request below.")
                        st.rerun()
                    else:
                        # Empty input - show guidance
                        st.error("❌ **No input detected!** You must type something to make a decision.")
                        st.info("💡 **Instructions:**\n- Type 'APPROVED' to deploy to GitHub\n- Type anything else (like 'no', 'reject', etc.) to reject and start fresh")
    
    # Show processing status if needed
    elif st.session_state.multi_agent_processing:
        st.info("🔄 **Processing:** Multi-agent collaboration in progress...")
        
        # Show a more detailed workflow progress
        st.markdown("""
        **Current Workflow:**
        1. 🔍 **Business Analyst** - Analyzing requirements and creating specifications
        2. 💻 **Software Engineer** - Writing code based on specifications  
        3. 🎯 **Product Owner** - Reviewing solution and deciding on approval
        """)
        
        st.warning("⏳ This process may take 2-5 minutes depending on complexity...")
        st.info("📊 **Progress tracking:** Check the terminal/console for real-time message updates")
        st.info("💡 **When finished:** The page will update with either an approval form or retry options. You may need to scroll down to see them!")
    
    # Show safety limit interface if needed
    if st.session_state.safety_limit_reached:
        st.markdown("---")
        
        # Scroll button at the very top - COMMENTED OUT (doesn't work properly in Streamlit)
        # col1, col2 = st.columns([4, 1])
        # with col1:
        #     st.markdown("### 🚨 **Safety Limit Reached!**")
        # with col2:
        #     scroll_clicked = st.button("⬇️ To Bottom", key="scroll_to_safety", type="secondary")
        
        st.markdown("### 🚨 **Safety Limit Reached!**")
        st.error("**The conversation exceeded 20 messages.** This usually happens when the agents get stuck in a loop or the requirements are too complex.")
            
        # Auto-scroll on first load or when scroll button is clicked - COMMENTED OUT (doesn't work properly)
        # if scroll_clicked or st.session_state.should_auto_scroll:
        #     st.session_state.should_auto_scroll = False  # Reset flag
        #     st.markdown("""
        #     <script>
        #     // Use a more reliable scroll method for Streamlit
        #     function scrollToPageBottom() {
        #         // Wait for the page to fully render
        #         setTimeout(function() {
        #             // Try different scroll approaches
        #             var maxScroll = Math.max(
        #                 document.body.scrollHeight,
        #                 document.body.offsetHeight,
        #                 document.documentElement.clientHeight,
        #                 document.documentElement.scrollHeight,
        #                 document.documentElement.offsetHeight
        #             );
        #             
        #             // Direct scroll to the calculated bottom
        #             window.scrollTo(0, maxScroll);
        #             
        #             // If in an iframe (like Streamlit), also try parent
        #             if (window.parent && window.parent !== window) {
        #                 try {
        #                     var parentMaxScroll = Math.max(
        #                         window.parent.document.body.scrollHeight,
        #                         window.parent.document.body.offsetHeight,
        #                         window.parent.document.documentElement.clientHeight,
        #                         window.parent.document.documentElement.scrollHeight,
        #                         window.parent.document.documentElement.offsetHeight
        #                     );
        #                     window.parent.scrollTo(0, parentMaxScroll);
        #                 } catch(e) {
        #                     // Ignore cross-origin errors
        #                 }
        #             }
        #         }, 300);
        #     }
        #     scrollToPageBottom();
        #     </script>
        #     """, unsafe_allow_html=True)
        
        # st.info("⬇️ **Scroll down to see the retry options below, or use the button above!**")
        
        st.warning("**What this means:**\n- The agents were unable to reach a solution within the safety limit\n- This is normal for very complex or unclear requirements")
        
        st.markdown("### 💡 **What to try next:**")
        col1, col2 = st.columns(2)
        
        with col1:
            st.info("""
            **Make your request simpler:**
            - Break down complex requests into smaller parts
            - Be more specific about what you want
            - Focus on core functionality first
            """)
        
        with col2:
            st.info("""
            **Try a different approach:**
            - Use different wording to describe your app
            - Specify fewer features initially
            - Provide clearer examples or references
            """)
        
        st.markdown("### 🔄 **Ready to try again?**")
        st.markdown("Click the button below to start fresh with a new request:")
        
        if st.button("🚀 Start New Project", type="primary", help="This will clear the conversation and let you start over"):
            # Reset ALL session state variables to ensure clean restart
            st.session_state.multi_agent_history = []
            st.session_state.multi_agent_processing = False
            st.session_state.awaiting_approval = False
            st.session_state.approval_data = None
            st.session_state.deployment_result = None
            st.session_state.safety_limit_reached = False
            st.session_state.should_auto_scroll = False
            st.session_state.reset_requested = False
            st.rerun()
        
        # Don't show the regular form when safety limit is reached
        return
    
    # Chat input form (only show if not awaiting approval AND not processing AND not safety limit reached)
    if not st.session_state.awaiting_approval and not st.session_state.multi_agent_processing and not st.session_state.safety_limit_reached:
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
                # Dynamic button text and state based on processing status
                if st.session_state.multi_agent_processing:
                    button_text = "⏳ Processing..."
                    button_disabled = True
                    button_type = "secondary"
                else:
                    button_text = "Send 📤"
                    button_disabled = False
                    button_type = "primary"
                
                send_clicked = st.form_submit_button(
                    button_text, 
                    use_container_width=True,
                    disabled=button_disabled,
                    type=button_type
                )
            
            if send_clicked and user_input.strip() and not st.session_state.multi_agent_processing:
                # Add user message immediately
                st.session_state.multi_agent_history.append({
                    "role": "user", 
                    "message": user_input.strip()
                })
                
                # Set processing state and store the request
                st.session_state.multi_agent_processing = True
                st.session_state.pending_request = user_input.strip()
                st.rerun()  # Force immediate rerun to hide the form and show processing status
    
    # Handle the actual processing in a separate section after UI update
    if st.session_state.multi_agent_processing and hasattr(st.session_state, 'pending_request'):
        # Check if reset was requested - if so, abort processing immediately
        if st.session_state.reset_requested:
            st.session_state.multi_agent_processing = False
            if hasattr(st.session_state, 'pending_request'):
                delattr(st.session_state, 'pending_request')
            st.rerun()
            return  # Exit early to prevent processing
            
        user_request = st.session_state.pending_request
        delattr(st.session_state, 'pending_request')  # Remove the pending request
        
        try:
            # Show processing status
            with st.spinner("🤖 Agents collaborating..."):
                progress_placeholder = st.empty()
                progress_placeholder.info("💭 Starting agent collaboration...")
                
                # Initialize session state for progress tracking
                st.session_state.current_message_count = 0
                
                # Run multi-agent system
                try:
                    result = asyncio.run(run_multi_agent(user_request, streamlit_mode=True))
                    
                    # Handle different result statuses
                    if isinstance(result, dict):
                        status = result.get("status", "unknown")
                        
                        if status == "awaiting_approval":
                            # Add the conversation messages to history
                            for response in result["messages"]:
                                if isinstance(response, dict) and "role" in response and "content" in response:
                                    role = response.get("role", "")
                                    if role and role.lower() != "user":
                                        st.session_state.multi_agent_history.append({
                                            "role": role,
                                            "message": response["content"]
                                        })
                            
                            # Set approval state
                            st.session_state.awaiting_approval = True
                            st.session_state.approval_data = result["chat_history"]
                            st.session_state.should_auto_scroll = True  # Trigger auto-scroll
                            
                        elif status == "safety_limit_reached":
                            # Handle safety limit scenario
                            for response in result["messages"]:
                                if isinstance(response, dict) and "role" in response and "content" in response:
                                    role = response.get("role", "")
                                    if role and role.lower() != "user":
                                        st.session_state.multi_agent_history.append({
                                            "role": role,
                                            "message": response["content"]
                                        })
                            
                            # Set safety limit reached flag
                            st.session_state.safety_limit_reached = True
                            st.session_state.should_auto_scroll = True  # Trigger auto-scroll
                                
                        elif status == "incomplete":
                            # Handle incomplete workflow
                            for response in result["messages"]:
                                if isinstance(response, dict) and "role" in response and "content" in response:
                                    role = response.get("role", "")
                                    if role and role.lower() != "user":
                                        st.session_state.multi_agent_history.append({
                                            "role": role,
                                            "message": response["content"]
                                        })
                            
                            st.error("❌ **Workflow Incomplete**")
                            st.warning(result.get("error_message", "The ProductOwner did not approve the solution."))
                            st.info("💡 **What to try:**\n- Provide more detailed requirements\n- Clarify specific features you need\n- Try rephrasing your request")
                            
                            if st.button("🔄 Try Again with Clearer Requirements", type="primary"):
                                # Reset ALL session state variables to ensure clean restart
                                st.session_state.multi_agent_history = []
                                st.session_state.multi_agent_processing = False
                                st.session_state.awaiting_approval = False
                                st.session_state.approval_data = None
                                st.session_state.deployment_result = None
                                st.session_state.safety_limit_reached = False
                                st.session_state.should_auto_scroll = False
                                st.session_state.reset_requested = False
                                st.rerun()
                                
                    elif result and isinstance(result, list):
                        # Normal completion without approval needed
                        for response in result:
                            if isinstance(response, dict) and "role" in response and "content" in response:
                                role = response.get("role", "")
                                if role and role.lower() != "user":
                                    st.session_state.multi_agent_history.append({
                                        "role": role,
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
                    tb_module.print_exc()
            
            st.session_state.multi_agent_processing = False
            st.rerun()
            
        except Exception as e:
            st.session_state.multi_agent_processing = False
            st.error(f"❌ An error occurred: {str(e)}")
            logging.error(f"Form submission error: {e}")
            tb_module.print_exc()
    
    # Footer
    st.markdown("---")
    st.markdown("🚀 **AI Workshop for Developers** - Powered by Multi-Agent AI System")

if __name__ == "__main__":
    main()