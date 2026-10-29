"""
Chat with the helpdesk in the terminal.

    python src/chat.py                # single agent (base version)
    python src/chat.py --agent multi  # multi-agent version (added by Person 2)
Type 'exit' to quit.
"""
import argparse
import sys

import config
from runner import ask


def load_agent(name: str):
    if name == "multi":
        from multi_agent.agent import root_agent
    else:
        from single_agent.agent import root_agent
    return root_agent


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent", default="single", choices=["single", "multi"])
    args = parser.parse_args()
    agent = load_agent(args.agent)
    print(f"IIT Jodhpur Academic Helpdesk ({args.agent} agent, model={config.CHAT_MODEL}). Type 'exit' to quit.\n")
    while True:
        q = input("You: ").strip()
        if q.lower() in {"exit", "quit"}:
            break
        if not q:
            continue
        r = ask(agent, q)
        print(f"\nHelpdesk: {r['answer']}\n   [tools: {', '.join(r['tools_used']) or 'none'} | {r['seconds']} s]\n")


if __name__ == "__main__":
    main()
