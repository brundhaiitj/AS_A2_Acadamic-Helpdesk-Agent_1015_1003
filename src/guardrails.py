"""
Safety net callbacks shared by all agents (single and multi-agent).

Small local models sometimes reply "I don't know" WITHOUT calling log_unanswered,
or invent a fake citation such as "[Source: log_unanswered]". These callbacks make
refusals reliable:
  - after_tool_callback  : remembers that log_unanswered was already called
  - after_model_callback : if the final answer is a refusal and nothing was logged,
                           logs the user's question automatically and returns the
                           standard refusal text (without a fake source).
"""
from google.genai import types

from prompts import REFUSAL
from tools import log_unanswered

REFUSAL_MARKERS = ["i don't know", "i do not know", "outside what i can help", "logged your question",
                   "not able to answer", "cannot answer", "can't answer"]


def _flag(ctx) -> str:
    return f"logged_{ctx.invocation_id}"


def remember_logging(tool, args, tool_context, tool_response):
    if getattr(tool, "name", "") == "log_unanswered":
        tool_context.state[_flag(tool_context)] = True
    return None


def ensure_refusal_logged(callback_context, llm_response):
    content = llm_response.content
    if not content or not content.parts:
        return None
    if any(getattr(p, "function_call", None) for p in content.parts):
        return None                      # model is still calling tools
    text = "".join(p.text or "" for p in content.parts)
    visible = text.split("</think>")[-1].lower()
    if not any(m in visible for m in REFUSAL_MARKERS):
        return None
    if not callback_context.state.get(_flag(callback_context)):
        question = ""
        if callback_context.user_content and callback_context.user_content.parts:
            question = "".join(p.text or "" for p in callback_context.user_content.parts)
        log_unanswered(question, "refused by agent (auto-logged)")
        callback_context.state[_flag(callback_context)] = True
    llm_response.content = types.Content(role="model", parts=[types.Part(text=REFUSAL)])
    return llm_response
