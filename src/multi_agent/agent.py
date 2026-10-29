"""
MULTI-AGENT VERSION (Person 2)

    helpdesk_orchestrator  (routes the question, refuses out-of-scope questions)
        |-- policy_agent    rules, regulations, attendance, exams, credits, curriculum
        |-- schedule_agent  course slots, time table, electives, academic calendar dates
        |-- email_agent     instructor email IDs and email drafts (leave / make-up exam)

The orchestrator hands the question over with ADK's built-in transfer_to_agent.
All agents reuse Person 1's tools (src/tools.py) and safety callbacks (src/guardrails.py).

Run in the browser UI:   adk web src        (then pick 'multi_agent')
Run in the terminal:     python src/chat.py --agent multi
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # makes 'src' importable

import litellm
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

import config
from guardrails import clean_model_reply, remember_logging
from tools import (count_electives, draft_email, get_instructor_email, log_unanswered,
                   lookup_course, search_documents)
from multi_agent.prompts_multi import (EMAIL_INSTRUCTION, ORCHESTRATOR_INSTRUCTION,
                                       POLICY_INSTRUCTION, SCHEDULE_INSTRUCTION)

litellm.drop_params = True
litellm.suppress_debug_info = True


def _model():
    return LiteLlm(model=config.litellm_model_name(), **config.litellm_model_kwargs())


def _specialist(name, description, instruction, tools):
    return Agent(
        name=name,
        model=_model(),
        description=description,
        instruction=instruction,
        tools=tools,
        disallow_transfer_to_parent=True,    # the specialist answers; no ping-pong
        disallow_transfer_to_peers=True,
        after_tool_callback=remember_logging,
        after_model_callback=clean_model_reply,
    )


policy_agent = _specialist(
    "policy_agent",
    "Answers questions on academic rules and regulations, attendance, examinations, grading, "
    "leave and make-up exam rules, registration, credits, degree requirements and curriculum.",
    POLICY_INSTRUCTION,
    [search_documents, log_unanswered],
)

schedule_agent = _specialist(
    "schedule_agent",
    "Answers questions on course slots, time table, instructors of a course, electives floated "
    "this semester and academic calendar dates (exams, classes, breaks, deadlines).",
    SCHEDULE_INSTRUCTION,
    [lookup_course, count_electives, search_documents, log_unanswered],
)

email_agent = _specialist(
    "email_agent",
    "Finds the email ID of a course instructor and drafts emails to instructors "
    "(sick leave, leave of absence, permission for make-up exam).",
    EMAIL_INSTRUCTION,
    [get_instructor_email, draft_email, log_unanswered],
)

root_agent = Agent(
    name="helpdesk_orchestrator",
    model=_model(),
    description="IIT Jodhpur Academic Helpdesk front desk: routes questions to specialist agents.",
    instruction=ORCHESTRATOR_INSTRUCTION,
    tools=[log_unanswered],
    sub_agents=[policy_agent, schedule_agent, email_agent],
    after_tool_callback=remember_logging,
    after_model_callback=clean_model_reply,
)
