"""
STEP: Check that the vector store returns the right document for typical questions.

    python tests/test_retrieval.py
Saves results/retrieval_test.csv  (take a screenshot of the terminal for the report)
"""
import csv

import _path  # noqa: F401
import config
from tools import search_documents

TESTS = [
    ("attendance requirement to appear in major exam", ["regulations_web_2019_onwards.txt", "regulations_2019_onwards.pdf", "amendment_attendance_policy_2024.pdf", "regulations_ug_2020_bioscience_copy.pdf"]),
    ("open elective credits required for B.Tech degree", ["regulations_web_2019_onwards.txt", "regulations_2019_onwards.pdf", "regulations_ug_2020_bioscience_copy.pdf", "curriculum_btech_cse_2026.pdf", "curriculum_btech_chemical_2026.pdf"]),
    ("make-up examination application within ten days", ["regulations_web_2019_onwards.txt", "regulations_2019_onwards.pdf", "regulations_ug_2020_bioscience_copy.pdf", "regulations_pg_2022_onwards.pdf", "amendment_examination_policy_2024.pdf"]),
    ("minor examination dates semester I 2026-27", ["academic_calendar_2026_27.pdf"]),
    ("major semester examination November 2026", ["academic_calendar_2026_27.pdf"]),
    ("branch change discontinued from academic year 2026-27", ["btech_registration_branch_change_faq.txt", "regulations_web_2019_onwards.txt"]),
    ("humanities bouquet courses philosophy critical thinking", ["sola_undergraduate_courses.txt"]),
    ("chemical engineering B.Tech curriculum structure credits", ["curriculum_btech_chemical_2026.pdf", "btech_chemical_semester_courses.txt"]),
    ("Autonomous Systems elective M.Tech Artificial Intelligence", ["curriculum_mtech_ai_2025.pdf", "curriculum_mtech_cse_2025.pdf", "curriculum_phd_cs_2026.pdf"]),
    ("summer term 2026 course registration dates", ["academic_calendar_summer_2026.pdf"]),
]


def main():
    rows, hits = [], 0
    for query, expected in TESTS:
        res = search_documents(query)
        if res.get("status") != "ok":
            print("ERROR:", res.get("message"))
            return
        top3 = [r["file"] for r in res["results"][:3]]
        hit = any(f in expected for f in top3)
        hits += hit
        print(f"[{'PASS' if hit else 'MISS'}] {query}")
        for r in res["results"][:3]:
            print(f"        {r['relevance']:.2f}  {r['file']}  (p. {r['page']})")
        rows.append([query, "PASS" if hit else "MISS", " | ".join(top3), " | ".join(expected)])

    config.RESULTS_DIR.mkdir(exist_ok=True)
    with open(config.RESULTS_DIR / "retrieval_test.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["query", "result", "top3_files", "expected_any_of"])
        w.writerows(rows)
    print(f"\nRetrieval hit@3: {hits}/{len(TESTS)}  ->  saved results/retrieval_test.csv")
    print("(A MISS for a document you could not download is expected.)")


if __name__ == "__main__":
    main()
