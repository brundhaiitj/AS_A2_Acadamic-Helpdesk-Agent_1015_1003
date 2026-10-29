"""
STEP: Ask the single agent 10 sample questions (in-scope, email and out-of-scope).

    python tests/test_agent.py
Saves results/single_agent_smoke_test.md and .csv  (about 3-8 minutes on a laptop)
"""
import csv

import _path  # noqa: F401
import config
from runner import ask
from single_agent.agent import root_agent

QUESTIONS = [
    "What is the attendance requirement to sit in the Major exam?",
    "How many Open Elective credits do I need to earn in order to get a B.Tech. degree?",
    "Within how many days must I apply for a make-up examination?",
    "What is the slot for the course Autonomous Systems?",
    "When are the Minor examinations in Semester I of 2026-27?",
    "How many 400 level electives have been floated by the Humanities department in this semester?",
    "Write an email to the course instructor of CSL7570 that I need leave for 2 days.",
    "What is the email ID of the instructor of EEL1010?",
    "What are the available dining options on the campus?",
    "What is the best way to reach the campus from Jodhpur city center?",
]


def main():
    md = [f"# Single agent smoke test (model: {config.CHAT_MODEL})\n"]
    rows = []
    for i, q in enumerate(QUESTIONS, 1):
        print(f"\n[{i}/{len(QUESTIONS)}] {q}")
        try:
            r = ask(root_agent, q)
        except Exception as e:
            r = {"answer": f"ERROR: {e}", "tools_used": [], "seconds": 0}
        print(f"  -> {r['answer'][:400]}")
        print(f"     tools: {r['tools_used']}  ({r['seconds']} s)")
        md += [f"## Q{i}. {q}", f"**Tools used:** {', '.join(r['tools_used']) or 'none'}  |  **Time:** {r['seconds']} s",
               "", r["answer"], ""]
        rows.append([q, r["answer"], ";".join(r["tools_used"]), r["seconds"]])

    config.RESULTS_DIR.mkdir(exist_ok=True)
    (config.RESULTS_DIR / "single_agent_smoke_test.md").write_text("\n".join(md), encoding="utf-8")
    with open(config.RESULTS_DIR / "single_agent_smoke_test.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["question", "answer", "tools_used", "seconds"])
        w.writerows(rows)
    print("\nSaved results/single_agent_smoke_test.md  |  check logs/unanswered_log.csv for the 2 refusals")


if __name__ == "__main__":
    main()
