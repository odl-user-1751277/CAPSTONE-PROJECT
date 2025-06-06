import os
import re
import asyncio
import subprocess
from pathlib import Path

from semantic_kernel.agents import AgentGroupChat, ChatCompletionAgent
from semantic_kernel.agents.strategies.termination.termination_strategy import TerminationStrategy
from semantic_kernel.agents.strategies.selection.kernel_function_selection_strategy import (
    KernelFunctionSelectionStrategy,
)
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.open_ai.services.azure_chat_completion import AzureChatCompletion
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.kernel import Kernel


HTML_OUTPUT_FILE = Path("index.html")
PUSH_SCRIPT      = Path("push_to_github.sh")

os.environ.setdefault(
    "AZURE_OPENAI_DEPLOYMENT_NAME",
    os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME", "gpt-4o")
)


_HTML_RE = re.compile(r"```html(.*?)```", re.DOTALL | re.IGNORECASE)

def _extract_html(text: str) -> str:
    """
    Return the first ```html fenced block from `text`.
    If none is found, return `text` unchanged.
    """
    m = _HTML_RE.search(text)
    return m.group(1).strip() if m else text.strip()


class ApprovalTerminationStrategy(TerminationStrategy):
    """A strategy for determining when an agent should terminate."""

    async def should_agent_terminate(self, agent, history):
        """Check if the agent should terminate.

        The conversation stops when the most-recent *user* message contains
        the literal word ‘APPROVED’ (case-insensitive).
        """
        for msg in reversed(history):
            if msg.role == AuthorRole.USER:
                return "APPROVED" in msg.content.upper()
        return False


async def run_multi_agent(input: str):
    """Implement the multi-agent system.

    Args:
        input (str): The initial request from the Product Owner / user.

    Returns:
        list[str]: All messages exchanged during the session (for logging or UI).
    """
    # Service -------------------------------------------------------------------
    kernel = Kernel()
    kernel.add_service(
        AzureChatCompletion(service_id="gpt-4o")
    )

    # Personas ------------------------------------------------------------------
    analyst = ChatCompletionAgent(
        kernel=kernel,
        name="BusinessAnalyst",
        instructions=(
            "You are a Business Analyst. Gather requirements from the user and "
            "relay clear specs to the Software Engineer. Ask clarifying "
            "questions when needed."
        ),
    )

    engineer = ChatCompletionAgent(
        kernel=kernel,
        name="SoftwareEngineer",
        instructions=(
            "You are a Software Engineer. Produce a COMPLETE, runnable web app "
            "using only HTML, CSS and vanilla JavaScript. Return the finished "
            "code inside a ```html fenced block."
        ),
    )

    owner = ChatCompletionAgent(
        kernel=kernel,
        name="ProductOwner",
        instructions=(
            "You are the Product Owner. Review the Engineer's solution. If it "
            "meets requirements, reply with the single word APPROVED. "
            "Otherwise, list concise change requests."
        ),
    )

    # Group chat with termination strategy -------------------------------------
    chat = AgentGroupChat(
        agents=[analyst, engineer, owner],
        selection_settings=KernelFunctionSelectionStrategy(kernel=kernel),
        execution_settings=ApprovalTerminationStrategy(),
    )

    # Kick off the dialogue with the user's request ----------------------------
    chat.add_chat_message(role=AuthorRole.USER, content=input)

    responses = []  # collect all messages for return

    # Stream conversation until APPROVED ---------------------------------------
    async for msg in chat.invoke():
        print(f"{msg.role} – {msg.name or '*'}: {msg.content!r}")
        responses.append(msg.content)

        if await chat.execution_settings.should_agent_terminate(None, chat.history):
            # Post-processing on approval ---------------------------------------
            engineer_msgs = [
                m.content for m in chat.history
                if m.author_name == "SoftwareEngineer"
            ]
            if engineer_msgs:                       # guard against empty list
                html_code = _extract_html(engineer_msgs[-1])
                HTML_OUTPUT_FILE.write_text(html_code, encoding="utf-8")
                print(f"✅  Wrote {HTML_OUTPUT_FILE.resolve()}")
                # optional Git push
                # subprocess.run(["bash", "push_to_github.sh"], check=True)
            break

    return responses


# ────────────────────────── quick manual test ---------------------------------
if __name__ == "__main__":
    asyncio.run(run_multi_agent("Build a single-page stopwatch in JS"))
#    asyncio.run(
#        run_multi_agent(
#            "Please build a simple calculator web app that supports +, −, ×, ÷."
#        )
#    )