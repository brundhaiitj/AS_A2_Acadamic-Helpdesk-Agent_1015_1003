"""
Runs a question through any ADK agent and returns the answer plus the tools it used.
Used by chat.py, the tests and (later) the evaluation scripts.

    from runner import ask
    from single_agent.agent import root_agent
    result = ask(root_agent, "What is the slot for Autonomous Systems?")
"""
import asyncio
import re
import time

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

THINK_RE = re.compile(r"<think>.*?</think>", re.S)


async def ask_async(agent, question: str, app_name: str = "academic_helpdesk") -> dict:
    session_service = InMemorySessionService()
    runner = Runner(app_name=app_name, agent=agent, session_service=session_service)
    session = await session_service.create_session(app_name=app_name, user_id="student")
    message = types.Content(role="user", parts=[types.Part(text=question)])

    tool_calls, agents_used, answer = [], [], ""
    start = time.time()
    async for event in runner.run_async(user_id="student", session_id=session.id, new_message=message):
        if event.author and event.author != "user" and event.author not in agents_used:
            agents_used.append(event.author)
        for call in event.get_function_calls() or []:
            tool_calls.append({"tool": call.name, "args": dict(call.args or {})})
        if event.is_final_response() and event.content and event.content.parts:
            text = "".join(p.text or "" for p in event.content.parts)
            if text.strip():
                answer = text
    answer = THINK_RE.sub("", answer).strip()
    return {
        "question": question,
        "answer": answer,
        "tools_used": [t["tool"] for t in tool_calls],
        "tool_calls": tool_calls,
        "agents_used": agents_used,
        "seconds": round(time.time() - start, 1),
    }


def ask(agent, question: str) -> dict:
    return asyncio.run(ask_async(agent, question))
