import sys
import os
import re
import asyncio
import subprocess
from pathlib import Path
from typing import List
from dotenv import load_dotenv
import warnings
import shutil

from semantic_kernel.agents import Agent, AgentGroupChat, ChatCompletionAgent
from semantic_kernel.agents.strategies.termination.termination_strategy import TerminationStrategy
from semantic_kernel.agents.strategies.selection.kernel_function_selection_strategy import (
    KernelFunctionSelectionStrategy,
)
from semantic_kernel.connectors.ai.open_ai.services.azure_chat_completion import AzureChatCompletion
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.kernel import Kernel
from semantic_kernel.functions.kernel_function_from_prompt import KernelFunctionFromPrompt
from semantic_kernel.functions.kernel_arguments import KernelArguments

# Load environment variables from .env file
load_dotenv()

# DEV TOGGLE - Set to False to suppress Git diagnostic messages
DEV_MODE = True
# ROOT_TOGGLE = True means output to project root, False means UI folder
ROOT_TOGGLE = True

# Paths to possible script locations
def find_git_root(path: Path) -> Path:
    current = path.resolve()
    for parent in [current] + list(current.parents):
        if (parent / ".git").exists():
            return parent
    raise RuntimeError("No .git directory found!")
PROJECT_ROOT = find_git_root(Path(__file__))
print(">>> REAL Project Root:", PROJECT_ROOT)
SCRIPT_IN_ROOT = PROJECT_ROOT / "push_to_github.sh"
SCRIPT_IN_UI = PROJECT_ROOT / "src" / "ui" / "push_to_github.sh"

def find_push_script():
    if SCRIPT_IN_ROOT.exists():
        return SCRIPT_IN_ROOT
    elif SCRIPT_IN_UI.exists():
        return SCRIPT_IN_UI
    else:
        return None

PUSH_SCRIPT = find_push_script()

# Fenced block HTML extraction pattern
_HTML_RE = re.compile(r"```html(.*?)```", re.DOTALL | re.IGNORECASE)

# Output file destination - save in current directory but consider project structurce
if ROOT_TOGGLE:
    HTML_OUTPUT_FILE = PROJECT_ROOT / "index.html" # This will be in src/ui/
else:
    HTML_OUTPUT_FILE = Path(__file__).parent / "index.html" # This will be in project root

# --- Helper function to extract HTML ---
def _extract_html(text: str) -> str:
    match = _HTML_RE.search(text)
    if match:
        return match.group(1).strip()
    # fallback: if not in code block, return everything
    return text.strip()

# --- Git Diagnostic Function ---
def diagnose_git_setup():
    """Diagnose Git setup and repository status."""
    if not DEV_MODE:
        return
        
    print("🔍 GIT DIAGNOSTIC REPORT")
    print("=" * 50)
    
    try:
        # Check current directory
        print(f"📁 Current directory: {os.getcwd()}")
        print(f"📁 Project root: {PROJECT_ROOT}")
        
        # Check if .git exists
        git_dir = PROJECT_ROOT / ".git"
        print(f"📁 Git directory exists: {git_dir.exists()}")
        
        # Check if index.html exists
        print(f"📄 index.html at output path ({HTML_OUTPUT_FILE}): {HTML_OUTPUT_FILE.exists()}")

        # Only run git commands if we're in a git repo
        if git_dir.exists():
            # Git status
            original_dir = os.getcwd()
            os.chdir(PROJECT_ROOT)
            
            commands_to_run = [
                (["git", "status", "--porcelain"], "Git Status (short)"),
                (["git", "remote", "-v"], "Git Remotes"),
                (["git", "branch", "--show-current"], "Current Branch"),
                (["git", "log", "--oneline", "-3"], "Recent Commits"),
            ]
            
            for cmd, description in commands_to_run:
                print(f"\n🔍 {description}:")
                try:
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        cwd=str(PROJECT_ROOT),
                        timeout=10
                    )
                    
                    if result.returncode == 0:
                        output = result.stdout.strip()
                        if output:
                            print(f"✅ {output}")
                        else:
                            print("✅ (no output - this might be normal)")
                    else:
                        print(f"❌ Error: {result.stderr}")
                        
                except subprocess.TimeoutExpired:
                    print("⏱️ Command timed out")
                except Exception as e:
                    print(f"❌ Exception: {e}")
            
            os.chdir(original_dir)
        else:
            print("⚠️ Not in a Git repository - Git commands skipped")
        
        print("\n" + "=" * 50)
        
    except Exception as e:
        print(f"❌ Diagnostic failed: {e}")

# --- Approval Termination Strategy ---
class ApprovalTerminationStrategy(TerminationStrategy):
    async def should_agent_terminate(self, agent: Agent, history: List[ChatMessageContent]) -> bool:
        # Look at the last 5 messages for a ProductOwner approval
        for message in reversed(history[-5:]):
            # If the ProductOwner says "READY FOR USER APPROVAL", end the conversation
            if (getattr(message, "name", None) == "ProductOwner"
                and message.content
                and "READY FOR USER APPROVAL" in message.content.strip().upper()):
                return True
        # Otherwise, keep going
        return False

# --- Enhanced Agent Selection Strategy ---
def create_agent_selection_strategy(kernel: Kernel) -> KernelFunctionSelectionStrategy:
    """Create the agent selection strategy with improved logic."""
    
    selection_prompt = """
You are managing a web development workflow with three agents:
- BusinessAnalyst: Gathers requirements (asks questions, waits for user responses)
- SoftwareEngineer: Creates HTML/CSS/JS code based on requirements
- ProductOwner: Reviews and approves/rejects the final code

CONVERSATION HISTORY:
{{$chat_history}}

SELECTION RULES (follow strictly in order):
1. If the last message is from User answering questions -> BusinessAnalyst should ask follow-up OR conclude with "Requirements are clear. Ready for development."
2. If BusinessAnalyst indicated requirements gathering is complete (e.g., said something like "Requirements are clear", "Ready for development", or anything similar) -> SoftwareEngineer

3. If SoftwareEngineer provided code (contains ```html) -> ProductOwner  
4. If ProductOwner requested changes/feedback -> SoftwareEngineer
5. If ProductOwner said "APPROVED" -> conversation ends
6. If BusinessAnalyst keeps repeating without user response -> SoftwareEngineer (assume requirements gathered)

IMPORTANT: 
- BusinessAnalyst should NOT speak twice in a row unless user responded
- If BusinessAnalyst already asked a question and no user response, move to SoftwareEngineer
- Look at the ACTUAL last speaker, not just the content

Based on the conversation history above, who should speak next?
Return ONLY one word: BusinessAnalyst, SoftwareEngineer, or ProductOwner
"""

    selection_function = KernelFunctionFromPrompt(
        function_name="select_next_agent",
        description="Selects the next agent to participate in the conversation",
        prompt=selection_prompt,
    )

    def parse_agent_selection(result) -> str:
        """Parse the selection result to return a valid agent name."""
        result_str = str(result).strip().upper()
        # Accept partial or fuzzy matches
        if "SOFTWAREENGINEER" in result_str:
            return "SoftwareEngineer"
        if "ENGINEER" in result_str:
                return "SoftwareEngineer"
        if "PRODUCTOWNER" in result_str:
            return "ProductOwner"
        return "BusinessAnalyst"

    return KernelFunctionSelectionStrategy(
        kernel=kernel,
        function=selection_function,
        arguments=KernelArguments(chat_history=""),
        result_parser=parse_agent_selection,
    )

# --- Create Individual Agents ---
def create_business_analyst(kernel: Kernel) -> ChatCompletionAgent:
    """Create the Business Analyst agent."""
    return ChatCompletionAgent(
        kernel=kernel,
        name="BusinessAnalyst",
        instructions="""
You are a Business Analyst. Upon receiving the user's initial request, immediately generate a detailed requirements document and project plan for the Software Engineer and Product Owner. 

If any requirement is unclear or missing, make reasonable assumptions and proceed. 
DO NOT ask the user questions or wait for any reply.
Summarize the requirements and end your message with: "Requirements are clear. Ready for development."
"""
    )

def create_software_engineer(kernel: Kernel) -> ChatCompletionAgent:
    """Create the Software Engineer agent."""
    return ChatCompletionAgent(
        kernel=kernel,
        name="SoftwareEngineer",
        instructions="""
You are a Software Engineer. Your goal is to create a web app using HTML, CSS, and JavaScript based on the requirements provided by the Business Analyst.

REQUIREMENTS:
- Create a complete, fully working application.
- Use modern, clean styling.
- Make it responsive.
- Include all necessary functionality as specified.
- Present all code in a single code block, using this format: ```html [your code here] ```
- After the code block, say: "Implementation complete. Ready for review."

If anything is unclear, make reasonable assumptions. Do NOT ask the BusinessAnalyst or user any questions.
Focus on creating something that actually works and looks professional.
"""
    )

def create_product_owner(kernel: Kernel) -> ChatCompletionAgent:
    """Create the Product Owner agent."""
    return ChatCompletionAgent(
        kernel=kernel,
        name="ProductOwner",
        instructions="""
You are the Product Owner.
When it is your turn, carefully review the latest code provided by the Software Engineer and compare it against the requirements from the Business Analyst and the original user request.

Steps:
- If the code block is missing, or the code is incomplete or incorrect, REJECT and give *specific feedback* on what's missing.
- If the code meets ALL requirements and is in a single complete ```html ... ``` code block, respond with your evaluation and end with:

READY FOR USER APPROVAL

Do NOT approve anything incomplete, missing, or not in the correct format. Do NOT give code, only review and make decisions.
"""
    )

# --- Enhanced Git Push Automation ---
async def execute_git_push():
    """Execute Git push with improved error handling and output display."""
    try:
        if DEV_MODE:
            print(f"🔍 Current working directory: {os.getcwd()}")
            print(f"🔍 Project root directory: {PROJECT_ROOT}")
        
        # Store original directory
        original_dir = os.getcwd()
        
        # Ensure we're working from the project root
        os.chdir(PROJECT_ROOT)
        if DEV_MODE:
            print(f"✅ Changed to project root: {os.getcwd()}")
        
        # Check if we're in a git repository
        git_dir = PROJECT_ROOT / ".git"
        if not git_dir.exists():
            print(f"❌ Error: Not in a Git repository at {PROJECT_ROOT}")
            os.chdir(original_dir)
            return False
            
        # Check if index.html exists in project root
            OUTPUT_FILE = HTML_OUTPUT_FILE  # Use the toggle-selected file as your working output

            if not OUTPUT_FILE.exists():
                print(f"❌ Error: No HTML file found at {OUTPUT_FILE}")
                os.chdir(original_dir)
                return False
        
        print("🚀 Executing Git operations...")
        
        # Show current git status
        if DEV_MODE:
            print("📊 Current git status:")
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                cwd=str(PROJECT_ROOT)
            )
            
            if result.returncode == 0:
                if result.stdout.strip():
                    print(f"Status output:\n{result.stdout}")
                else:
                    print("✅ Working directory is clean")
            else:
                print(f"⚠️ Could not get git status: {result.stderr}")
        
        # Add the file
        if DEV_MODE:
            print("📝 Adding index.html to staging...")
        result = subprocess.run(
            ["git", "add", "index.html"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT)
        )
        
        if result.returncode != 0:
            print(f"❌ Git add failed: {result.stderr}")
            os.chdir(original_dir)
            return False
        else:
            if DEV_MODE:
                print("✅ Git add successful")
            
        # Check if there are changes to commit
        if DEV_MODE:
            print("🔍 Checking for staged changes...")
        result = subprocess.run(
            ["git", "diff", "--staged", "--quiet"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT)
        )
        
        if result.returncode == 0:
            print("ℹ️ No changes to commit (file might already be up to date)")
            os.chdir(original_dir)
            return True
        
        # Show what's staged
        if DEV_MODE:
            result = subprocess.run(
                ["git", "diff", "--staged", "--name-only"],
                capture_output=True,
                text=True,
                cwd=str(PROJECT_ROOT)
            )
            
            if result.returncode == 0 and result.stdout.strip():
                print(f"📄 Files staged for commit: {result.stdout.strip()}")
        
        # Create commit with timestamp
        import datetime
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        commit_message = f"Auto-deploy: Updated web app - {timestamp}"
        
        if DEV_MODE:
            print("💾 Committing changes...")
        result = subprocess.run(
            ["git", "commit", "-m", commit_message],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT)
        )
        
        if result.returncode != 0:
            print(f"❌ Git commit failed:")
            print(f"   stderr: {result.stderr}")
            print(f"   stdout: {result.stdout}")
            os.chdir(original_dir)
            return False
        else:
            if DEV_MODE:
                print("✅ Git commit successful")
                if result.stdout.strip():
                    print(f"   Commit output: {result.stdout}")
            
        # Get current branch
        if DEV_MODE:
            print("🔍 Getting current branch...")
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT)
        )
        
        if result.returncode != 0:
            print(f"❌ Could not get current branch: {result.stderr}")
            os.chdir(original_dir)
            return False
            
        current_branch = result.stdout.strip()
        if DEV_MODE:
            print(f"📍 Current branch: {current_branch}")
        
        # Check if remote exists
        if DEV_MODE:
            print("🔍 Checking remote repository...")
            result = subprocess.run(
                ["git", "remote", "-v"],
                capture_output=True,
                text=True,
                cwd=str(PROJECT_ROOT)
            )
            
            if result.returncode == 0:
                if result.stdout.strip():
                    print(f"🌐 Remote repositories:\n{result.stdout}")
                else:
                    print("⚠️ No remote repositories configured")
            else:
                print(f"⚠️ Could not get remote info: {result.stderr}")
        
        # Push to the current branch
        print(f"⬆️  Pushing to origin/{current_branch}...")
        result = subprocess.run(
            ["git", "push", "origin", current_branch],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT)
        )
        
        # Always show output regardless of success/failure
        if DEV_MODE:
            print(f"📤 Push command completed with return code: {result.returncode}")
        
        if result.stdout:
            print(f"✅ Push stdout:\n{result.stdout}")
        
        if result.stderr:
            print(f"📝 Push stderr:\n{result.stderr}")
        
        # Restore original directory
        os.chdir(original_dir)
        
        if result.returncode == 0:
            print("🎉 Successfully pushed to GitHub!")
            print("🌐 Changes are now live on your repository")
            return True
        else:
            print("❌ Push failed - see output above for details")
            return False
            
    except Exception as e:
        print(f"❌ Error during Git push: {e}")
        import traceback
        traceback.print_exc()
        # Restore original directory in case of exception
        try:
            os.chdir(original_dir)
        except:
            pass
        return False

# --- Alternative function using the shell script ---
async def execute_git_push_with_script():
    """Execute Git push using the shell script in either allowed location."""
    if PUSH_SCRIPT is None:
        print(f"❌ No push_to_github.sh found in root or src/ui!")
        return False

    def find_git_bash():
        # Hardcoded known Git Bash locations
        possible_paths = [
            shutil.which("bash"),  # whatever's in PATH first
            r"C:\Program Files\Git\bin\bash.exe",
            r"C:\Program Files (x86)\Git\bin\bash.exe"
        ]
        # Return the first one that both exists AND contains 'Git' in the path (extra check)
        for b in possible_paths:
            if b and os.path.exists(b) and "Git" in b:
                return b
        # Last resort: try any that exists (maybe user changed install path)
        for b in possible_paths:
            if b and os.path.exists(b):
                return b
        return None

    git_bash = find_git_bash()
    print("GIT BASH resolved at:", git_bash)
    if not git_bash:
        print("❌ Could not find Git Bash! Please check your PATH or install location.")
        return False

    # print(">>> Root at:", PROJECT_ROOT)
    # print("Root script at:", SCRIPT_IN_ROOT)
    # print("UI script at:", SCRIPT_IN_UI)
    # print("Root script exists:", SCRIPT_IN_ROOT.exists())
    # print("UI script exists:", SCRIPT_IN_UI.exists())

    print(f"🚀 Executing push script: {PUSH_SCRIPT}")

    result = subprocess.run(
        [git_bash, str(PUSH_SCRIPT)],
        capture_output=True,
        text=True,
        cwd=str(PUSH_SCRIPT.parent),
        encoding="utf-8",
        errors="replace"
    )

    print(f"📤 Script completed with return code: {result.returncode}")
    if result.stdout:
        print(f"📝 Script output:\n{result.stdout}")
    if result.stderr:
        print(f"⚠️ Script errors:\n{result.stderr}")

    return result.returncode == 0

# --- Enhanced Multi-Agent Workflow ---
async def run_multi_agent(user_input: str):
    print("=" * 60)
    print("🚀 MULTI-AGENT WEB DEVELOPMENT WORKFLOW")
    print("=" * 60)
    print(f"📝 User Request: {user_input}")
    print("=" * 60)
    
    # Kernel and services
    kernel = Kernel()
    kernel.add_service(
        AzureChatCompletion(
            deployment_name=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"),
            endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        )
    )
    
    business_analyst = create_business_analyst(kernel)
    software_engineer = create_software_engineer(kernel)
    product_owner = create_product_owner(kernel)
    selection_strategy = create_agent_selection_strategy(kernel)
    termination_strategy = ApprovalTerminationStrategy()
    
    chat = AgentGroupChat(
        agents=[business_analyst, software_engineer, product_owner],
        selection_strategy=selection_strategy,
        termination_strategy=termination_strategy,
    )
    
    # Add initial user message
    initial_message = ChatMessageContent(
        role=AuthorRole.USER, 
        content=user_input
    )
    await chat.add_chat_message(initial_message)
    
    # Print agent messages as required
    message_count = 0
    last_agent_name = None
    business_analyst_questions = 0
    ready_for_user_approval = False
    ba_asked = False

    async for content in chat.invoke():
        agent_name = getattr(content, 'name', 'Unknown')

        # Skip repeated BusinessAnalyst messages (logic kept from your version)
        if agent_name == "BusinessAnalyst":
            if ba_asked:
                continue
            else:
                ba_asked = True

        # Reset BA flag if user responds
        if agent_name == "User":
            ba_asked = False

        message_count += 1
        last_agent_name = agent_name

        # Track speaker transitions
        if agent_name == "BusinessAnalyst":
            business_analyst_questions += 1

        print(f"# {content.role} - {content.name or '*'}: '{content.content}'")
        print("-" * 60)

        print(f"📊 Messages: {message_count}")
        print(f"✅ Last agent: {agent_name}")
        print(f"⌛ Processing...\n")

        # Check for ProductOwner approval
        if agent_name == "ProductOwner" and "READY FOR USER APPROVAL" in content.content.upper():
            ready_for_user_approval = True
            print("🎯 READY FOR USER APPROVAL detected!")
            break

        # Enhanced chat history for selection strategy
        history_for_selection = []
        for i, msg in enumerate(chat.history[-8:]):  # Last 8 messages
            speaker = "User" if (hasattr(msg, 'role') and msg.role == AuthorRole.USER) else getattr(msg, 'name', 'Unknown')
            history_for_selection.append(f"{speaker}: {msg.content[:200]}...")  # Truncate long messages
        context_info = f"\nContext: BusinessAnalyst has asked {business_analyst_questions} questions. Last speaker: {agent_name}"
        selection_strategy.arguments = KernelArguments(
            chat_history="\n".join(history_for_selection) + context_info
        )

        # Safety checks
        if message_count > 20:
            print("⚠️ Safety limit reached. Ending conversation.")
            break
        if agent_name == "BusinessAnalyst" and business_analyst_questions > 2:
            print("⚠️ BusinessAnalyst asked too many questions. Moving to development.")
            completion_msg = ChatMessageContent(
                role=AuthorRole.ASSISTANT,
                content="Requirements are clear based on the initial request. Ready for development."
            )
            completion_msg.name = "BusinessAnalyst"
            await chat.add_chat_message(completion_msg)
            ba_asked = False  # Reset the flag

        last_speaker = agent_name

    # Check for approval (if ProductOwner's last message contains it)
    approval_in_history = any(
        getattr(m, "name", None) == "ProductOwner" and m.content and "READY FOR USER APPROVAL" in m.content.upper()
        for m in chat.history[-5:]
    )
    if approval_in_history:
        print("Type 'APPROVED' to finalize and push to GitHub, or anything else to exit:")
        user_approval = input().strip()
        if user_approval.upper() == "APPROVED":
            # Extract HTML code from SoftwareEngineer messages
            html_code = None
            for message in chat.history:
                if getattr(message, 'name', None) == "SoftwareEngineer":
                    extracted_html = _extract_html(message.content)
                    if extracted_html and len(extracted_html) > 50:
                        html_code = extracted_html
                        break
            if html_code:
                HTML_OUTPUT_FILE.write_text(html_code, encoding="utf-8")
                print(f"💾 Saved HTML to: {HTML_OUTPUT_FILE.resolve()}")
                git_response = input("Do you want to push to GitHub? (y/N): ").strip().lower()
                if git_response in ['y', 'yes']:
                    await execute_git_push_with_script()
                else:
                    print("📝 Git push skipped by user.")
            else:
                print("❌ No valid HTML code found.")
        else:
            print("❌ Solution not approved. Exiting without saving.")
    else:
        print("❌ The Product Owner did NOT approve. Workflow incomplete.")
    print("=" * 60)
    print("🎉 MULTI-AGENT WORKFLOW COMPLETED")
    print("=" * 60)

    # Collect all chat messages (for Streamlit) before returning
    streamlit_messages = []
    for m in chat.history:
        streamlit_messages.append({
            "role": getattr(m, 'name', getattr(m, 'role', 'assistant')),
            "content": getattr(m, 'content', str(m))
        })
    return streamlit_messages    

# --- Main execution ---
async def main():
    """Main entry point with user input handling."""
    try:
        print("\n🤖 Multi-Agent Web Development System")
        print("=" * 50)
        
        # Run diagnostic first
        diagnose_git_setup()
        
        user_request = input("\nWhat would you like to build? ")
        
        if not user_request.strip():
            print("❌ No request provided. Exiting...")
            return
            
        await run_multi_agent(user_request)
        
    except KeyboardInterrupt:
        print("\n🛑 Workflow interrupted by user")
    except Exception as e:
        print(f"❌ Fatal error in workflow: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("🔄 Cleaning up resources...")
        await asyncio.sleep(0.1)

if __name__ == "__main__":
    if os.name == 'nt':
        try:
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        except AttributeError:
            pass

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nGoodbye! 👋")
    except Exception as e:
        print(f"Application error: {e}")
    finally:
        # Suppress resource warnings (if any) during shutdown
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")

if os.name == 'nt':
    # Suppress stderr on exit to hide annoying closed errors
    sys.stderr = open(os.devnull, 'w')