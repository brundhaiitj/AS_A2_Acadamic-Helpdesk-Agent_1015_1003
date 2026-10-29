# Tool test results

## lookup_course({'course': 'Autonomous Systems'})
```json
{
  "status": "ok",
  "matches": [
    {
      "course_code": "CSL7570",
      "course_name": "Autonomous Systems",
      "department": "CS",
      "category": "elective",
      "credits": "3",
      "ltp": "3-0-0",
      "slot": "J",
      "instructor": "Instructor CSL7570 (dummy)",
      "classroom": "LHC 105",
      "semester": "AY 2026-27 Sem I",
      "data_status": "dummy - verify on ERP"
    }
  ],
  "source": "Course & Timetable list (data/csv/courses.csv)"
}
```

## lookup_course({'course': 'MAL1010'})
```json
{
  "status": "ok",
  "matches": [
    {
      "course_code": "MAL1010",
      "course_name": "Mathematics I",
      "department": "MA",
      "category": "institute core",
      "credits": "4",
      "ltp": "3-1-0",
      "slot": "N",
      "instructor": "Kirankumar Hiremath",
      "classroom": "LHB 308 / LHB 110",
      "semester": "AY 2023-24 Sem I (first year)",
      "data_status": "official - Office of Academics first-year time table"
    }
  ],
  "source": "Course & Timetable list (data/csv/courses.csv)"
}
```

## count_electives({'department': 'Humanities', 'level': 400})
```json
{
  "status": "ok",
  "department": "HS",
  "level": 400,
  "semester": "AY 2026-27 Sem I",
  "count": 6,
  "courses": [
    {
      "course_code": "HSL4010",
      "course_name": "Introduction to Philosophy",
      "slot": "W"
    },
    {
      "course_code": "HSL4020",
      "course_name": "Fundamentals of Logic",
      "slot": "W"
    },
    {
      "course_code": "HSL4030",
      "course_name": "Critical Thinking",
      "slot": "W"
    },
    {
      "course_code": "HSL4040",
      "course_name": "Theories of Justice",
      "slot": "W"
    },
    {
      "course_code": "HSL4050",
      "course_name": "Gandhian Thought",
      "slot": "W"
    },
    {
      "course_code": "HSL4060",
      "course_name": "Role of Technology in Development",
      "slot": "W"
    }
  ],
  "source": "Course & Timetable list (data/csv/courses.csv)"
}
```

## get_instructor_email({'course_code': 'CSL7570'})
```json
{
  "status": "ok",
  "course_code": "CSL7570",
  "course_name": "Autonomous Systems",
  "instructor": "Instructor CSL7570 (dummy)",
  "email": "csl7570.instructor@iitj.ac.in",
  "department_office_email": "office_cse@iitj.ac.in",
  "data_status": "dummy - verify on ERP",
  "source": "Course & Timetable list (data/csv/courses.csv); Faculty & Department contacts (data/csv/faculty.csv)"
}
```

## draft_email({'course_code': 'CSL7570', 'purpose': 'leave', 'details': '2 days (30-31 October 2026) due to fever'})
```json
{
  "status": "ok",
  "to": "csl7570.instructor@iitj.ac.in",
  "cc_department_office": "office_cse@iitj.ac.in",
  "subject": "Request for leave of absence - CSL7570",
  "body": "Dear Sir/Madam,\n\nI am writing to inform you that I will be unable to attend the classes of CSL7570 - Autonomous Systems and to request leave for the following: 2 days (30-31 October 2026) due to fever.\n\nI will submit the supporting document (e.g. medical certificate) as required, and I will make sure to cover the missed lectures and any assignments.\n\nThank you for your consideration.\n\nYours sincerely,\n[Your Name]\nRoll No.: [Your Roll No.]\nIIT Jodhpur",
  "rule_note": "Rule note (Academic Regulations, Sec. 15): leave applications go to the Convener DUGC with a medical certificate if applicable; short leave is up to 10 days on medical grounds and 5 days for other valid reasons.",
  "saved_to": "outputs/email_drafts/20261029_193120_CSL7570_leave.txt",
  "note": "This is a DRAFT for the student to review. It has NOT been sent.",
  "source": "Course & Timetable list (data/csv/courses.csv); Faculty & Department contacts (data/csv/faculty.csv); IIT Jodhpur Academic Regulations (UG/PG, July 2019 onwards)"
}
```

## log_unanswered({'question': 'TEST: what are the dining options on campus?', 'reason': 'out of scope (tool test)'})
```json
{
  "status": "logged",
  "log_file": "logs/unanswered_log.csv",
  "message": "Question recorded for the helpdesk staff."
}
```

## search_documents({'query': 'attendance requirement major exam'})
```json
{
  "status": "ok",
  "query": "attendance requirement major exam",
  "results": [
    {
      "text": "or lab session. The attendance records must be made available to the student after every lecture. Even if the student's attendance falls below 75%, the student will be allowed to appear for the exams....",
      "source": "Circular: Amendment in the Attendance Policy (08 July 2024; from Sem I AY 2024-25)",
      "file": "amendment_attendance_policy_2024.txt",
      "page": 1,
      "year": "2024",
      "relevance": 0.769
    },
    {
      "text": "this arrangement, the course will be listed in the Grade Card of the student. 4.1.9 Attendance Requirements A student should have full attendance in each course. Unless the student takes leave of abse...",
      "source": "Academic Regulations (students enrolled from July 2020 onwards)",
      "file": "regulations_ug_2020_bioscience_copy.pdf",
      "page": 7,
      "year": "2020",
      "relevance": 0.749
    }
  ],
  "how_to_cite": "[Source: <source>, p. <page>]"
}
```
