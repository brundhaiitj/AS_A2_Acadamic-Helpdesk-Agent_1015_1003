"""
Final evaluation tables and charts for the report (all 4 configurations).

    python eval/final_tables.py

Reads results/scored_all.csv (from eval/score.py, with manual_accuracy reviewed) and writes
  results/final_metrics.csv       run 1, all 30 questions, one row per configuration
  results/final_by_category.csv   accuracy % per category and configuration
  results/final_per_question.csv  1/0 per question and configuration (run 1)
  results/final_consistency.csv   questions answered in two runs: did the answer / correctness change?
  results/final_chart_metrics.png, results/final_chart_category.png
"""
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "results"
ORDER = ["single_qwen3-8b", "multi_qwen3-8b", "single_llama3.1-8b", "multi_llama3.1-8b"]
LABEL = {"single_qwen3-8b": "Single · Qwen3 8B", "multi_qwen3-8b": "Multi · Qwen3 8B",
         "single_llama3.1-8b": "Single · Llama 3.1 8B", "multi_llama3.1-8b": "Multi · Llama 3.1 8B"}
COLORS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]


def pct(s):
    s = pd.to_numeric(s, errors="coerce").dropna()
    return round(100 * s.mean(), 1) if len(s) else None


def norm(t):
    t = re.sub(r"\[source.*", "", str(t).lower(), flags=re.S)
    return re.sub(r"\W+", " ", t).strip()


def main():
    df = pd.read_csv(RES / "scored_all.csv", dtype=str).fillna("")
    df["acc"] = df.apply(lambda r: r["manual_accuracy"] if r["manual_accuracy"] in ("0", "1") else r["accuracy_auto"], axis=1)
    r1 = df[df["run"] == "1"]

    rows = []
    for cfg in ORDER:
        g = r1[r1.config == cfg]
        gi, go = g[g.category != "out_of_scope"], g[g.category == "out_of_scope"]
        rows.append({
            "configuration": LABEL[cfg], "answers": len(g),
            "accuracy_%": pct(g.acc), "in_scope_accuracy_%": pct(gi.acc),
            "groundedness_%": pct(gi.grounded), "citation_present_%": pct(gi.cited),
            "correct_refusal_%": pct(go.refused), "false_refusal_%": pct(gi.refused),
            "refusals_logged_%": pct(go.logged), "correct_tool_%": pct(g.tool_correct),
            "correct_routing_%": pct(g.routing_correct) if "multi" in cfg else "",
            "median_seconds": round(pd.to_numeric(g.seconds).median(), 0),
        })
    met = pd.DataFrame(rows)
    met.to_csv(RES / "final_metrics.csv", index=False)

    cat = (r1.assign(a=pd.to_numeric(r1.acc)).pivot_table(index="category", columns="config", values="a", aggfunc="mean")[ORDER] * 100).round(0)
    cat.columns = [LABEL[c] for c in cat.columns]
    cat = cat.reindex(["policy", "schedule", "email", "out_of_scope"])
    cat.to_csv(RES / "final_by_category.csv")

    pq = r1.pivot_table(index="id", columns="config", values="acc", aggfunc="first")[ORDER]
    pq.columns = [LABEL[c] for c in pq.columns]
    pq.to_csv(RES / "final_per_question.csv")

    cons = []
    for (cfg, qid), g in df.groupby(["config", "id"]):
        if g.run.nunique() < 2:
            continue
        g = g.sort_values("run")
        cons.append({"configuration": LABEL[cfg], "id": qid, "question": g.question.iloc[0],
                     "answer_text_changed": "yes" if len({norm(a) for a in g.answer}) > 1 else "no",
                     "correctness_run1_run2": " / ".join(g.acc),
                     "correctness_changed": "YES" if g.acc.nunique() > 1 else "no",
                     "run1": g.answer.iloc[0][:160].replace("\n", " "), "run2": g.answer.iloc[-1][:160].replace("\n", " ")})
    pd.DataFrame(cons).to_csv(RES / "final_consistency.csv", index=False)

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                         "axes.edgecolor": "#8a8984", "axes.labelcolor": "#52514e", "xtick.color": "#52514e",
                         "ytick.color": "#52514e", "figure.facecolor": "#ffffff", "axes.facecolor": "#ffffff"})

    def grouped(frame, groups, title, fname, ylabel):
        n = len(frame.columns)
        w = 0.8 / n
        fig, ax = plt.subplots(figsize=(10, 4.6))
        for i, (col, colr) in enumerate(zip(frame.columns, COLORS)):
            xs = [k + (i - (n - 1) / 2) * w for k in range(len(groups))]
            vals = frame[col].astype(float).values
            bars = ax.bar(xs, vals, width=w - 0.02, color=colr, label=col, zorder=3)
            for b, v in zip(bars, vals):
                ax.text(b.get_x() + b.get_width() / 2, v + 1.2, f"{v:.0f}", ha="center", va="bottom", fontsize=7.5, color="#52514e")
        ax.set_xticks(range(len(groups)))
        ax.set_xticklabels(groups)
        ax.set_ylim(0, 112)
        ax.set_ylabel(ylabel)
        ax.grid(axis="y", color="#e6e5e0", zorder=0)
        ax.set_title(title, loc="left", fontsize=12, color="#0b0b0b")
        ax.legend(ncol=4, frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.1), fontsize=9)
        plt.tight_layout()
        plt.savefig(RES / fname, dpi=170)
        plt.close()

    mcols = ["accuracy_%", "groundedness_%", "correct_refusal_%", "correct_tool_%"]
    mframe = met.set_index("configuration")[mcols].T
    grouped(mframe, ["Accuracy", "Groundedness\n(in-scope)", "Correct refusal\n(out-of-scope)", "Correct tool"],
            "Evaluation metrics by configuration (30 questions, run 1)", "final_chart_metrics.png", "%")
    grouped(cat, ["Policy (12)", "Schedule (8)", "Email (4)", "Out of scope (6)"],
            "Accuracy by question category", "final_chart_category.png", "Accuracy %")

    print(met.to_string(index=False))
    print(cat.to_string())
    print(f"\n{len(cons)} question/config pairs with 2 runs; correctness changed in "
          f"{sum(c['correctness_changed'] == 'YES' for c in cons)}, wording changed in {sum(c['answer_text_changed'] == 'yes' for c in cons)}")


if __name__ == "__main__":
    main()
