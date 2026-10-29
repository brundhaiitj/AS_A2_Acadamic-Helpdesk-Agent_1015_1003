"""
STEP (Person 2): run the 30 evaluation questions through an agent several times.

    python eval/run_eval.py --agent multi  --runs 3                 # model from HELPDESK_MODEL
    python eval/run_eval.py --agent single --runs 1
    python eval/run_eval.py --agent multi  --runs 3 --model llama3.1:8b
    python eval/run_eval.py --agent multi  --runs 1 --ids Q01,Q13,Q25   # quick check

Results: results/raw_<agent>_<model>.csv  (one row per run x question).
It RESUMES automatically: if you stop it (Ctrl+C) and start the same command again,
finished rows are skipped.
"""
import argparse
import csv
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

ap = argparse.ArgumentParser()
ap.add_argument("--agent", choices=["single", "multi"], default="multi")
ap.add_argument("--runs", type=int, default=3)
ap.add_argument("--model", default=None, help="e.g. qwen3:8b or llama3.1:8b (default: HELPDESK_MODEL)")
ap.add_argument("--ids", default="", help="comma separated question ids to run (default: all)")
args = ap.parse_args()
if args.model:
    os.environ["HELPDESK_MODEL"] = args.model   # must be set before config is imported

import config  # noqa: E402
from runner import ask  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

FIELDS = ["config", "agent", "model", "run", "id", "category", "question", "answer",
          "tools_used", "agents_used", "seconds", "error", "timestamp"]


def load_agent(name):
    if name == "multi":
        from multi_agent.agent import root_agent
    else:
        from single_agent.agent import root_agent
    return root_agent


def main():
    agent = load_agent(args.agent)
    model = config.CHAT_MODEL
    cfg = f"{args.agent}_{model.replace(':', '-')}"
    out = config.RESULTS_DIR / f"raw_{cfg}.csv"
    config.RESULTS_DIR.mkdir(exist_ok=True)

    questions = list(csv.DictReader(open(ROOT / "eval" / "questions.csv", newline="", encoding="utf-8")))
    if args.ids:
        wanted = {i.strip() for i in args.ids.split(",")}
        questions = [q for q in questions if q["id"] in wanted]

    done = set()
    if out.exists():
        for r in csv.DictReader(open(out, newline="", encoding="utf-8")):
            if not r["error"]:
                done.add((r["run"], r["id"]))
    new_file = not out.exists()
    f = open(out, "a", newline="", encoding="utf-8")
    w = csv.DictWriter(f, fieldnames=FIELDS)
    if new_file:
        w.writeheader()

    total = args.runs * len(questions)
    n, start = 0, time.time()
    print(f"Config {cfg}: {len(questions)} questions x {args.runs} runs  ->  {out.relative_to(ROOT)}\n")
    for run in range(1, args.runs + 1):
        for q in questions:
            n += 1
            if (str(run), q["id"]) in done:
                continue
            print(f"[{n}/{total}] run {run} {q['id']}: {q['question'][:70]}")
            row = {"config": cfg, "agent": args.agent, "model": model, "run": run, "id": q["id"],
                   "category": q["category"], "question": q["question"], "error": "",
                   "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")}
            try:
                r = ask(agent, q["question"])
                row.update(answer=r["answer"], tools_used=";".join(r["tools_used"]),
                           agents_used=";".join(r["agents_used"]), seconds=r["seconds"])
                print(f"     -> {r['answer'][:150].replace(chr(10), ' ')}")
                print(f"        agents={r['agents_used']} tools={r['tools_used']} ({r['seconds']} s)")
            except Exception as e:
                row.update(answer="", tools_used="", agents_used="", seconds=0, error=str(e)[:300])
                print(f"     !! ERROR: {str(e)[:200]}")
            w.writerow(row)
            f.flush()
    f.close()
    print(f"\nFinished in {(time.time() - start) / 60:.1f} min. Next: python eval/score.py")


if __name__ == "__main__":
    main()