"""
STEP (Person 2): build the result tables and charts for the report.

    python eval/analyze.py

Reads results/scored_all.csv and writes:
  results/summary.md                 tables for the report (paste into the report)
  results/summary_by_config.csv      one row per agent+model configuration
  results/summary_by_category.csv    accuracy per question category
  results/consistency.csv            questions whose answer changed between runs
  results/chart_metrics.png          accuracy / groundedness / refusal per configuration
  results/chart_category.png         accuracy per category
"""
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
import config  # noqa: E402

RES = config.RESULTS_DIR


def pct(s):
    s = pd.to_numeric(s, errors="coerce").dropna()
    return round(100 * s.mean(), 1) if len(s) else None


def norm(text):
    text = str(text).lower()
    text = re.sub(r"\[source.*", "", text, flags=re.S)
    return re.sub(r"\W+", " ", text).strip()


def to_md(frame, index=True):
    try:
        return frame.to_markdown(index=index)
    except ImportError:                      # 'tabulate' not installed
        return "```\n" + frame.to_string(index=index) + "\n```"


def main():
    df = pd.read_csv(RES / "scored_all.csv", dtype=str).fillna("")
    df["accuracy"] = df.apply(lambda r: r["manual_accuracy"] if r["manual_accuracy"] in ("0", "1")
                              else r["accuracy_auto"], axis=1)
    in_scope = df["category"] != "out_of_scope"

    rows = []
    for cfg, g in df.groupby("config"):
        gi, go = g[g["category"] != "out_of_scope"], g[g["category"] == "out_of_scope"]
        rows.append({
            "config": cfg, "agent": g["agent"].iloc[0], "model": g["model"].iloc[0],
            "runs": g["run"].nunique(), "answers": len(g),
            "accuracy_%": pct(g["accuracy"]),
            "accuracy_in_scope_%": pct(gi["accuracy"]),
            "groundedness_%": pct(gi["grounded"]),
            "citation_present_%": pct(gi["cited"]),
            "correct_refusal_%": pct(go["refused"]),
            "false_refusal_%": pct(gi["refused"]),
            "refusals_logged_%": pct(go["logged"]),
            "tool_correct_%": pct(g["tool_correct"]),
            "routing_correct_%": pct(g["routing_correct"]) if (g["agent"] == "multi").any() else "",
            "avg_seconds": round(pd.to_numeric(g["seconds"], errors="coerce").mean(), 1),
            "errors": int((g["error"] != "").sum()),
        })
    by_cfg = pd.DataFrame(rows)
    by_cfg.to_csv(RES / "summary_by_config.csv", index=False)

    by_cat = (df.assign(acc=pd.to_numeric(df["accuracy"], errors="coerce"))
                .pivot_table(index="category", columns="config", values="acc", aggfunc="mean") * 100).round(1)
    by_cat.to_csv(RES / "summary_by_category.csv")

    cons = []
    for (cfg, qid), g in df.groupby(["config", "id"]):
        if g["run"].nunique() < 2:
            continue
        answers = {norm(a) for a in g["answer"]}
        accs = set(g["accuracy"])
        if len(answers) > 1 or len(accs) > 1:
            cons.append({"config": cfg, "id": qid, "question": g["question"].iloc[0],
                         "distinct_answers": len(answers),
                         "correctness_changed": "YES" if len(accs) > 1 else "no",
                         "accuracy_per_run": " / ".join(g.sort_values("run")["accuracy"]),
                         "answer_run1": g.sort_values("run")["answer"].iloc[0][:200],
                         "answer_last_run": g.sort_values("run")["answer"].iloc[-1][:200]})
    cons_df = pd.DataFrame(cons)
    cons_df.to_csv(RES / "consistency.csv", index=False)

    # charts
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        metrics = ["accuracy_%", "groundedness_%", "correct_refusal_%", "tool_correct_%"]
        plot = by_cfg.set_index("config")[metrics].apply(pd.to_numeric, errors="coerce")
        ax = plot.plot(kind="bar", figsize=(9, 4.5), rot=0, ylim=(0, 105))
        ax.set_ylabel("%")
        ax.set_title("Helpdesk evaluation by configuration")
        ax.legend(["Accuracy", "Groundedness", "Correct refusal", "Correct tool"], loc="lower right")
        plt.tight_layout()
        plt.savefig(RES / "chart_metrics.png", dpi=150)
        plt.close()
        ax = by_cat.plot(kind="bar", figsize=(9, 4.5), rot=0, ylim=(0, 105))
        ax.set_ylabel("Accuracy %")
        ax.set_title("Accuracy by question category")
        plt.tight_layout()
        plt.savefig(RES / "chart_category.png", dpi=150)
        plt.close()
    except Exception as e:
        print("Charts skipped:", e)

    md = ["# Evaluation summary\n", "## Metrics by configuration\n", to_md(by_cfg, index=False), "",
          "## Accuracy (%) by question category\n", to_md(by_cat), "",
          f"## Answers that changed between runs ({len(cons_df)} question/config pairs)\n",
          to_md(cons_df[["config", "id", "question", "distinct_answers", "correctness_changed",
                        "accuracy_per_run"]], index=False) if len(cons_df) else "No answer changed between runs.", ""]
    (RES / "summary.md").write_text("\n".join(md), encoding="utf-8")
    print(by_cfg.to_string(index=False))
    print(f"\n{len(cons_df)} question/config pairs changed between runs (results/consistency.csv)")
    print("Written: results/summary.md, chart_metrics.png, chart_category.png")


if __name__ == "__main__":
    main()