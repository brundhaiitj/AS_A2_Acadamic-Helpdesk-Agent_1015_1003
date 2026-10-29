"""
STEP: Run every tool once and check the output by eye.

    python tests/test_tools.py
Saves results/tools_test.md
"""
import json

import _path  # noqa: F401
import config
from tools import (count_electives, draft_email, get_instructor_email, log_unanswered,
                   lookup_course, search_documents)

CASES = [
    ("lookup_course", lookup_course, {"course": "Autonomous Systems"}),
    ("lookup_course", lookup_course, {"course": "MAL1010"}),
    ("count_electives", count_electives, {"department": "Humanities", "level": 400}),
    ("get_instructor_email", get_instructor_email, {"course_code": "CSL7570"}),
    ("draft_email", draft_email, {"course_code": "CSL7570", "purpose": "leave",
                                  "details": "2 days (30-31 October 2026) due to fever"}),
    ("log_unanswered", log_unanswered, {"question": "TEST: what are the dining options on campus?",
                                        "reason": "out of scope (tool test)"}),
    ("search_documents", search_documents, {"query": "attendance requirement major exam"}),
]


def short(result: dict) -> dict:
    if "results" in result:   # trim long passages for display
        result = dict(result)
        result["results"] = [{**r, "text": r["text"][:200] + "..."} for r in result["results"][:2]]
    return result


def main():
    lines = ["# Tool test results\n"]
    for name, fn, args in CASES:
        out = short(fn(**args))
        status = out.get("status", "")
        print(f"\n=== {name}({args}) -> {status}")
        print(json.dumps(out, indent=2, ensure_ascii=False)[:1500])
        lines += [f"## {name}({args})", "```json", json.dumps(out, indent=2, ensure_ascii=False), "```", ""]
    config.RESULTS_DIR.mkdir(exist_ok=True)
    (config.RESULTS_DIR / "tools_test.md").write_text("\n".join(lines), encoding="utf-8")
    print("\nSaved results/tools_test.md  |  email draft saved in outputs/email_drafts/  |  log in logs/unanswered_log.csv")


if __name__ == "__main__":
    main()
