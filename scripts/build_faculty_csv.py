"""
Builds data/csv/faculty.csv from courses.csv + official department office emails.
Run again whenever you edit courses.csv:

    python scripts/build_faculty_csv.py
"""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COURSES = ROOT / "data" / "csv" / "courses.csv"
FACULTY = ROOT / "data" / "csv" / "faculty.csv"

# Department office emails published on iitj.ac.in department pages
DEPARTMENT_OFFICES = [
    ("CS", "Department of Computer Science & Engineering", "office_cse@iitj.ac.in"),
    ("CH", "Department of Chemical Engineering", "office_che@iitj.ac.in"),
    ("CY", "Department of Chemistry", "office_chemistry@iitj.ac.in"),
    ("EE", "Department of Electrical Engineering", "office_ee@iitj.ac.in"),
    ("CI", "Department of Civil and Infrastructure Engineering", "office_civil@iitj.ac.in"),
    ("DS", "School of Design", "office_design@iitj.ac.in"),
    ("EX", "Office of Executive Education Program", "office_eep@iitj.ac.in"),
]


def main():
    people = {}
    for row in csv.DictReader(open(COURSES, newline="", encoding="utf-8")):
        names = [n.strip() for n in row["instructor"].split(",")]
        emails = [e.strip() for e in row["instructor_email"].split(",")]
        for i, name in enumerate(names):
            email = emails[i] if i < len(emails) else emails[0]
            key = (name, email)
            entry = people.setdefault(key, {"name": name, "department": row["department"], "role": "Course instructor",
                                            "email": email, "courses": [], "data_status": row["data_status"]})
            entry["courses"].append(row["course_code"])

    with open(FACULTY, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["name", "department", "role", "email", "courses", "data_status"])
        for p in people.values():
            w.writerow([p["name"], p["department"], p["role"], p["email"], " ".join(p["courses"]), p["data_status"]])
        for code, name, email in DEPARTMENT_OFFICES:
            w.writerow([name, code, "Department office", email, "", "official - department web page"])
    print(f"faculty.csv written with {len(people)} instructors + {len(DEPARTMENT_OFFICES)} department offices")


if __name__ == "__main__":
    main()
