"""
BASE VERSION: one agent that has all the tools.

Run in the browser UI:   adk web src        (then pick 'single_agent')
Run in the terminal:     python src/chat.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # makes 'src' importable

import litellm
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

import config
from prompts import SINGLE_AGENT_INSTRUCTION
from guardrails import clean_model_reply, remember_logging
from tools import ALL_TOOLS

litellm.drop_params = True          # ignore settings a model does not support
litellm.suppress_debug_info = True  # hide "Provider List" messages

root_agent = Agent(
    name="academic_helpdesk",
    model=LiteLlm(model=config.litellm_model_name(), **config.litellm_model_kwargs()),
    description="IIT Jodhpur academic helpdesk: rules, curriculum, time table and instructor emails.",
    instruction=SINGLE_AGENT_INSTRUCTION,
    tools=ALL_TOOLS,
    after_tool_callback=remember_logging,      # see guardrails.py
    after_model_callback=clean_model_reply,
)