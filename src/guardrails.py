"""
Safety net callbacks shared by all agents (single and multi-agent).

Small local models sometimes reply "I don't know" WITHOUT calling log_unanswered,
or invent a fake citation such as "[Source: log_unanswered]". These callbacks make
refusals reliable and hide the model's private "thinking" text:
  - strip_thinking       : removes <think>...</think> reasoning from every model reply
  - after_tool_callback  : remembers that log_unanswered was already called
  - after_model_callback : if the final answer is a refusal and nothing was logged,
                           logs the user's question automatically and returns the
                           standard refusal text (without a fake source).
"""
import re

from google.genai import types

from prompts import REFUSAL
from tools import log_unanswered

REFUSAL_MARKERS = ["i don't know", "i do not know", "outside what i can help", "logged your question",
                   "not able to answer", "cannot answer", "can't answer"]


THINK_TAG = re.compile(r"<think>.*?</think>", re.S)


def strip_thinking(callback_context, llm_response):
    """Remove the model's private reasoning so only the final answer is shown
    (in adk web, in chat.py and in the evaluation)."""
    content = llm_response.content
    if not content or not content.parts:
        return None
    has_call = any(getattr(p, "function_call", None) for p in content.parts)
    new_parts, changed = [], False
    for part in content.parts:
        if part.text is not None and not getattr(part, "function_call", None):
            if has_call:                       # text next to a tool call is only reasoning
                changed = True
                continue
            text = THINK_TAG.sub("", part.text)
            if "</think>" in text:
                text = text.split("</think>")[-1]
            text = text.strip()
            if text != part.text:
                changed = True
                part = types.Part(text=text)
            if not text:
                continue
        new_parts.append(part)
    if not changed:
        return None
    llm_response.content = types.Content(role="model", parts=new_parts or [types.Part(text="")])
    return llm_response


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
    visible = text.lower()
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


def clean_model_reply(callback_context, llm_response):
    """Use this as after_model_callback: strips thinking, then makes refusals reliable."""
    cleaned = strip_thinking(callback_context, llm_response) or llm_response
    final = ensure_refusal_logged(callback_context, cleaned)
    if final is not None:
        return final
    return cleaned if cleaned is not llm_response or cleaned.content is not None else None