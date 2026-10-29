"""
Tools used by the helpdesk agent(s).

HANDOVER CONTRACT (Person 2's multi-agent code relies on these exact names):
    search_documents(query)                      -> rules, regulations, curriculum, calendar
    lookup_course(course)                        -> slot / instructor / credits of a course
    count_electives(department, level)           -> electives floated this semester
    get_instructor_email(course_code)            -> instructor name + email
    draft_email(course_code, purpose, details,
                student_name, roll_number)       -> email draft (NOT sent)
    log_unanswered(question, reason)             -> logs question for a human

Every tool returns a dict that includes the source to cite.
"""
import csv
import re
from datetime import datetime
from functools import lru_cache

import config

COURSE_SOURCE = "Course & Timetable list (data/csv/courses.csv)"
FACULTY_SOURCE = "Faculty & Department contacts (data/csv/faculty.csv)"
REGULATIONS_SOURCE = "IIT Jodhpur Academic Regulations (UG/PG, July 2019 onwards)"

DEPT_ALIASES = {
    "HS": ["humanities", "hss", "liberal arts", "sola", "social science", "school of liberal arts"],
    "CS": ["computer", "cse", "computer science"],
    "CH": ["chemical", "che", "chemical engineering"],
    "EE": ["electrical", "ee", "electrical engineering"],
    "ME": ["mechanical", "me", "mechanical engineering"],
    "MA": ["mathematics", "maths", "math"],
    "PH": ["physics"],
    "CY": ["chemistry"],
    "BB": ["bioscience", "bioengineering", "biology", "bio"],
    "CI": ["civil", "infrastructure"],
    "MT": ["materials", "metallurgical"],
    "OA": ["office of academics"],
    "OS": ["office of students"],
}


# ---------------------------------------------------------------- helpers
def _read_csv(path) -> list[dict]:
    if not path.exists():
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return [{k.strip(): (v or "").strip() for k, v in row.items()} for row in csv.DictReader(f)]


def _norm_code(code: str) -> str:
    return re.sub(r"[\s\-_]", "", code or "").upper()


def _dept_code(department: str) -> str:
    d = (department or "").strip().lower()
    if d.upper() in DEPT_ALIASES:
        return d.upper()
    for code, names in DEPT_ALIASES.items():
        if any(n in d for n in names):
            return code
    return d.upper()[:2]


def _course_level(code: str):
    """HSL4010 -> 400, CSL7570 -> 700"""
    m = re.match(r"^[A-Z]{2}[A-Z](\d)", _norm_code(code))
    return int(m.group(1)) * 100 if m else None


def _public_course(row: dict) -> dict:
    keys = ["course_code", "course_name", "department", "category", "credits", "ltp",
            "slot", "instructor", "classroom", "semester", "data_status"]
    return {k: row.get(k, "") for k in keys}


@lru_cache(maxsize=1)
def _collection():
    import chromadb
    client = chromadb.PersistentClient(path=str(config.CHROMA_DIR))
    return client.get_collection(config.COLLECTION_NAME)


# ---------------------------------------------------------------- tools
def search_documents(query: str) -> dict:
    """Search the official IIT Jodhpur documents (academic regulations, attendance and
    examination rules, grading, leave and make-up exam rules, B.Tech/M.Tech curricula,
    credit requirements, academic calendar dates, notices).

    Args:
        query: A short search query, e.g. "attendance requirement major exam".

    Returns:
        dict with the top matching passages. Each result has 'text', 'source', 'page'.
        Cite answers as [Source: <source>, p. <page>].
    """
    from embeddings import embed_texts
    try:
        vector = embed_texts([query], kind="query")[0]
        res = _collection().query(query_embeddings=[vector], n_results=config.TOP_K)
    except Exception as e:
        return {"status": "error", "message": f"Search failed: {e}. Has ingest.py been run?"}

    results = []
    for text, meta, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0]):
        results.append({
            "text": text,
            "source": meta.get("title", meta.get("file")),
            "file": meta.get("file"),
            "page": meta.get("page"),
            "year": meta.get("year"),
            "relevance": round(1 - float(dist), 3),
        })
    return {"status": "ok", "query": query, "results": results,
            "how_to_cite": "[Source: <source>, p. <page>]"}


def lookup_course(course: str) -> dict:
    """Look up a course by code (e.g. "CSL7570") or by name (e.g. "Autonomous Systems")
    to get its slot, instructor, credits, L-T-P, classroom and semester.

    Args:
        course: Course code or (part of the) course name.

    Returns:
        dict with matching courses and the source to cite.
    """
    rows = _read_csv(config.COURSES_CSV)
    q_code = _norm_code(course)
    exact = [r for r in rows if _norm_code(r["course_code"]) == q_code]
    if not exact:
        words = [w for w in re.findall(r"[a-z0-9]+", course.lower()) if len(w) > 2]
        exact = [r for r in rows if words and all(w in r["course_name"].lower() for w in words)]
    if not exact:
        return {"status": "not_found", "query": course,
                "message": "No course matched in the course list.", "source": COURSE_SOURCE}
    return {"status": "ok", "matches": [_public_course(r) for r in exact], "source": COURSE_SOURCE}


def count_electives(department: str, level: int) -> dict:
    """Count the elective courses floated in the CURRENT semester by a department at a
    given course level (100, 200, 300, 400, 500, 600, 700, 800).

    Args:
        department: Department name or code, e.g. "Humanities", "HS", "Chemical", "CS".
        level: Course level such as 400 (taken from the first digit of the course number).

    Returns:
        dict with the count and the list of matching elective courses.
    """
    dept = _dept_code(department)
    level = int(str(level)[0]) * 100 if level else None
    rows = _read_csv(config.COURSES_CSV)
    matches = [
        r for r in rows
        if r.get("department", "").upper() == dept
        and _course_level(r["course_code"]) == level
        and "elective" in r.get("category", "").lower()
        and r.get("semester", "") == config.CURRENT_SEMESTER
    ]
    return {
        "status": "ok",
        "department": dept,
        "level": level,
        "semester": config.CURRENT_SEMESTER,
        "count": len(matches),
        "courses": [{"course_code": r["course_code"], "course_name": r["course_name"],
                     "slot": r["slot"]} for r in matches],
        "source": COURSE_SOURCE,
    }


def get_instructor_email(course_code: str) -> dict:
    """Find the instructor(s) and email ID(s) for a course, plus the department office email.

    Args:
        course_code: Course code such as "CSL7570" or "MAL1010".

    Returns:
        dict with instructor name(s), email(s) and the source to cite.
    """
    found = lookup_course(course_code)
    if found["status"] != "ok":
        return {"status": "not_found", "course_code": course_code,
                "message": "Course not found, so the instructor email is unknown.",
                "source": COURSE_SOURCE}
    row = next(r for r in _read_csv(config.COURSES_CSV)
               if _norm_code(r["course_code"]) == _norm_code(found["matches"][0]["course_code"]))
    office = next((f for f in _read_csv(config.FACULTY_CSV)
                   if f.get("role") == "Department office" and f.get("department") == row.get("department")), None)
    return {
        "status": "ok",
        "course_code": row["course_code"],
        "course_name": row["course_name"],
        "instructor": row.get("instructor", ""),
        "email": row.get("instructor_email", ""),
        "department_office_email": office["email"] if office else "",
        "data_status": row.get("data_status", ""),
        "source": f"{COURSE_SOURCE}; {FACULTY_SOURCE}",
    }


def draft_email(course_code: str, purpose: str, details: str,
                student_name: str = "[Your Name]", roll_number: str = "[Your Roll No.]") -> dict:
    """Draft (but never send) an email from a student to the instructor of a course.

    Args:
        course_code: Course code, e.g. "CSL7570".
        purpose: One of "leave" (sick leave / leave of absence), "makeup" (permission for a
                 make-up exam) or "other".
        details: Key facts from the student, e.g. "2 days, 30-31 Oct 2026, fever".
        student_name: Student's name if given, else a placeholder.
        roll_number: Student's roll number if given, else a placeholder.

    Returns:
        dict with to, subject, body and the file path where the draft was saved.
    """
    info = get_instructor_email(course_code)
    if info["status"] != "ok":
        return {"status": "error", "message": f"Course {course_code} not found; cannot draft email."}

    p = purpose.lower()
    kind = "makeup" if ("make" in p or "exam" in p) else "leave" if ("leave" in p or "sick" in p or "absen" in p) else "other"
    instructor = info["instructor"] or ""
    first = instructor.split(",")[0].strip()
    greeting = "Dear Sir/Madam," if (not first or "dummy" in first.lower()) else f"Dear Prof. {first},"
    course = f"{info['course_code']} - {info['course_name']}"

    if kind == "leave":
        subject = f"Request for leave of absence - {info['course_code']}"
        middle = (f"I am writing to inform you that I will be unable to attend the classes of {course} "
                  f"and to request leave for the following: {details}.\n\n"
                  "I will submit the supporting document (e.g. medical certificate) as required, and I will "
                  "make sure to cover the missed lectures and any assignments.")
        rule = ("Rule note (Academic Regulations, Sec. 15): leave applications go to the Convener DUGC with a "
                "medical certificate if applicable; short leave is up to 10 days on medical grounds and 5 days "
                "for other valid reasons.")
    elif kind == "makeup":
        subject = f"Request for permission to take make-up examination - {info['course_code']}"
        middle = (f"I could not appear for the examination of {course} due to the following reason: {details}.\n\n"
                  "I kindly request your permission and recommendation to take the make-up examination. "
                  "I will attach the required medical certificate / supporting documents.")
        rule = ("Rule note (Academic Regulations, Sec. 8): the make-up application is made to the Dean (Academics) "
                "through the course instructor within ten days of the missed examination, with the required "
                "medical documents.")
    else:
        subject = f"Regarding {info['course_code']}"
        middle = details
        rule = ""

    body = (f"{greeting}\n\n{middle}\n\nThank you for your consideration.\n\n"
            f"Yours sincerely,\n{student_name}\nRoll No.: {roll_number}\nIIT Jodhpur")

    config.EMAIL_DRAFT_DIR.mkdir(parents=True, exist_ok=True)
    fname = config.EMAIL_DRAFT_DIR / f"{datetime.now():%Y%m%d_%H%M%S}_{info['course_code']}_{kind}.txt"
    fname.write_text(f"To: {info['email']}\nSubject: {subject}\n\n{body}\n\n{rule}\n", encoding="utf-8")

    return {
        "status": "ok",
        "to": info["email"],
        "cc_department_office": info["department_office_email"],
        "subject": subject,
        "body": body,
        "rule_note": rule,
        "saved_to": str(fname.relative_to(config.ROOT)),
        "note": "This is a DRAFT for the student to review. It has NOT been sent.",
        "source": f"{info['source']}; {REGULATIONS_SOURCE}",
    }


def log_unanswered(question: str, reason: str) -> dict:
    """Record a question the helpdesk cannot answer so that a human can answer it later.
    Use this for out-of-scope questions (e.g. food, travel, hostels) or when the documents
    do not contain the answer.

    Args:
        question: The user's question, exactly as asked.
        reason: Short reason, e.g. "out of scope" or "not found in documents".

    Returns:
        dict confirming the question was logged.
    """
    config.LOG_DIR.mkdir(exist_ok=True)
    new_file = not config.UNANSWERED_LOG.exists()
    with open(config.UNANSWERED_LOG, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new_file:
            w.writerow(["timestamp", "question", "reason", "model", "status"])
        w.writerow([datetime.now().isoformat(timespec="seconds"), question, reason,
                    config.CHAT_MODEL, "pending human answer"])
    return {"status": "logged", "log_file": "logs/unanswered_log.csv",
            "message": "Question recorded for the helpdesk staff."}


ALL_TOOLS = [search_documents, lookup_course, count_electives,
             get_instructor_email, draft_email, log_unanswered]
