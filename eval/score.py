"""
STEP (Person 2): automatically score every answer in results/raw_*.csv.

    python eval/score.py

Writes results/scored_all.csv with these columns per answer:
  accuracy_auto   1/0  key facts from eval/answer_keys.csv are present (and no wrong refusal)
  grounded        1/0  the [Source: ...] cites one of the expected documents (blank for out-of-scope)
  cited           1/0  the answer contains a [Source: ...] citation
  refused         1/0  the answer is the "I don't know" refusal
  refusal_correct 1/0  refused exactly when the question is out of scope
  logged          1/0  (out-of-scope only) question appears in logs/unanswered_log.csv
  tool_correct    1/0  the expected tool was called
  routing_correct 1/0  (multi-agent only) the question reached the right specialist agent
  manual_accuracy      EMPTY - fill 1 or 0 by hand only where you disagree with accuracy_auto

Re-running keeps anything you typed in manual_accuracy.
"""
import csv
import glob
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
import config  # noqa: E402
from prompts import REFUSAL  # noqa: E402

REFUSAL_MARKERS = ["i don't know", "i do not know", "outside what i can help", "logged your question"]


def read(path):
    return list(csv.DictReader(open(path, newline="", encoding="utf-8")))


def has_group(text, group):
    for alt in group.split("|"):
        alt = alt.strip()
        if alt.startswith("re:"):
            if re.search(alt[3:], text, re.I):
                return True
        elif alt.lower() in text:
            return True
    return False


def main():
    questions = {q["id"]: q for q in read(ROOT / "eval" / "questions.csv")}
    keys = {k["id"]: k for k in read(ROOT / "eval" / "answer_keys.csv")}
    titles = {s["file"]: s["title"].lower() for s in read(config.SOURCES_CSV)}
    logged_q = set()
    if config.UNANSWERED_LOG.exists():
        logged_q = {r["question"].strip().lower() for r in read(config.UNANSWERED_LOG)}

    out = config.RESULTS_DIR / "scored_all.csv"
    manual = {}
    if out.exists():
        for r in read(out):
            if r.get("manual_accuracy", "").strip():
                manual[(r["config"], r["run"], r["id"])] = r["manual_accuracy"].strip()

    raw = {}
    for path in sorted(glob.glob(str(config.RESULTS_DIR / "raw_*.csv"))):
        for r in read(path):
            key = (r["config"], r["run"], r["id"])
            if key in raw and not raw[key]["error"] and r["error"]:
                continue                     # keep the successful attempt
            raw[key] = r                     # a later retry replaces an earlier error

    rows = []
    for r in raw.values():
        if True:
            q, k = questions.get(r["id"]), keys.get(r["id"])
            if not q or not k:
                continue
            ans = (r["answer"] or "")
            low = ans.lower()
            in_scope = q["in_scope"].strip().lower() == "yes"
            refused = int(any(m in low for m in REFUSAL_MARKERS) or REFUSAL.lower() in low)
            cited = int("[source" in low)

            if not in_scope:
                acc = refused
            else:
                groups = [g for g in k["must_contain"].split(";") if g.strip()]
                acc = int(not refused and bool(ans) and all(has_group(low, g) for g in groups))

            grounded = ""
            if in_scope:
                cite_text = low[low.find("[source"):] if cited else ""
                expected = [e.strip() for e in q["expected_source"].split(";") if e.strip()]
                ok = False
                for e in expected:
                    if e == "courses.csv":
                        ok |= "courses.csv" in cite_text or "course & timetable" in cite_text
                    else:
                        t = titles.get(e, "")
                        ok |= bool(t) and (t[:30] in cite_text) or e.lower() in cite_text
                grounded = int(ok)

            tools = r["tools_used"].split(";") if r["tools_used"] else []
            agents = r["agents_used"].split(";") if r["agents_used"] else []
            tool_ok = int(q["expected_tool"] in tools) if in_scope else int(refused)
            routing = ""
            if r["agent"] == "multi":
                if in_scope:
                    routing = int(k["expected_agent"] in agents)
                else:
                    routing = int(not any(a.endswith("_agent") for a in agents))

            rows.append({
                **{c: r[c] for c in ["config", "agent", "model", "run", "id", "category", "question"]},
                "answer": ans, "tools_used": r["tools_used"], "agents_used": r["agents_used"],
                "seconds": r["seconds"], "error": r["error"],
                "accuracy_auto": acc, "grounded": grounded, "cited": cited, "refused": refused,
                "refusal_correct": int(refused == (0 if in_scope else 1)),
                "logged": "" if in_scope else int(r["question"].strip().lower() in logged_q),
                "tool_correct": tool_ok, "routing_correct": routing,
                "manual_accuracy": manual.get((r["config"], r["run"], r["id"]), ""),
            })

    if not rows:
        sys.exit("No results found. Run eval/run_eval.py first.")
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"Scored {len(rows)} answers -> results/scored_all.csv")
    print("Open it, read answers where accuracy_auto looks wrong, and type 1 or 0 in manual_accuracy.")
    print("Next: python eval/analyze.py")


if __name__ == "__main__":
    main()