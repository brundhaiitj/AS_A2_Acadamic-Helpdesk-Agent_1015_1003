# IIT Jodhpur Academic Helpdesk Agent (RAG + Google ADK + Ollama)

A local, laptop-friendly helpdesk that answers questions about IIT Jodhpur academic programs, course contents,
rules and regulations, the time table and academic calendar, and drafts emails to course instructors
(sick leave / make-up exam). Out-of-scope questions are refused and logged for a human.

- **LLM:** `qwen3:8b` or `llama3.1:8b` served by **Ollama**, used by **Google ADK** through **LiteLLM**
- **RAG:** local embeddings (`nomic-embed-text`) + **ChromaDB**
- **Citations:** every answer cites the document and page it came from
- Runs on a 16 GB RAM laptop, fully offline after setup

## Setup
```bash
# 1. Install Python 3.12, Git and Ollama, then:
ollama pull qwen3:8b
ollama pull nomic-embed-text
ollama pull llama3.1:8b          # for the model comparison

# 2. Python environment
python -m venv .venv
.venv\Scripts\activate           # Windows   (Mac/Linux: source .venv/bin/activate)
pip install -r requirements.txt
python check_setup.py            # every line should say OK

# 3. Data + vector store
python scripts/download_docs.py  # downloads the official documents into data/docs
python src/ingest.py             # builds chroma_db/
```

## Run
```bash
adk web src                      # browser UI at http://localhost:8000 -> choose an agent
python src/chat.py               # terminal chat with the single agent
python src/chat.py --agent multi # terminal chat with the multi-agent system
```

## Multi-agent system
`helpdesk_orchestrator` routes each question with `transfer_to_agent` to `policy_agent` (rules, credits,
curriculum), `schedule_agent` (slots, electives, calendar) or `email_agent` (instructor emails, drafts), and
refuses + logs out-of-scope questions itself. Code: `src/multi_agent/`.

## Evaluation
```bash
python eval/run_eval.py --agent multi  --runs 3 --model qwen3:8b      # or llama3.1:8b, --ids Q01,Q13 for a subset
python eval/run_eval.py --agent single --runs 1 --model qwen3:8b
python eval/score.py       # results/scored_all.csv (accuracy, groundedness, refusals, tool/routing)
python eval/analyze.py     # results/summary.md, consistency.csv, chart_*.png
```
Report: [read online](report/README.md) · [PDF](report/Academic_Helpdesk_Agent_Report.pdf) · [Word (.docx) download](https://github.com/brundhaiitj/AS_A2_Acadamic-Helpdesk-Agent_1015_1003/raw/main/report/Academic_Helpdesk_Agent_Report.docx)
Switch the LLM: set `HELPDESK_MODEL=llama3.1:8b` (or edit `src/config.py`).

## Tests
```bash
python tests/test_retrieval.py   # does search return the right document? (hit@3)
python tests/test_tools.py       # runs every tool once
python tests/test_agent.py       # 10 sample questions through the single agent
```

## Folder structure
```
data/docs/            official documents (PDF + text versions of web pages)
data/csv/             sources.csv (document list + URLs), courses.csv, faculty.csv
src/config.py         models, paths and RAG settings
src/ingest.py         chunk + embed + store in ChromaDB
src/tools.py          the 6 tools used by the agents
src/prompts.py        agent instructions
src/single_agent/     base version (one agent, all tools)
src/multi_agent/      orchestrator + policy / schedule / email agents
src/guardrails.py     removes thinking text, guarantees refusals are logged
src/runner.py         run any agent on a question (used by tests / evaluation)
eval/questions.csv    30 evaluation questions with expected answers and sources
eval/answer_keys.csv  key facts + expected agent per question
eval/run_eval.py      runs questions through an agent; score.py / analyze.py score and summarise
logs/                 unanswered_log.csv (questions referred to a human)
outputs/email_drafts/ generated email drafts (never sent)
results/              test and evaluation outputs
report/               report and screenshots
```

## Tools
| Tool | Purpose |
|---|---|
| `search_documents(query)` | Semantic search over the official documents (returns passages + source + page) |
| `lookup_course(course)` | Slot, instructor, credits, classroom for a course code or name |
| `count_electives(department, level)` | Number of electives floated this semester by a department at a level |
| `get_instructor_email(course_code)` | Instructor name + email and the department office email |
| `draft_email(course_code, purpose, details, ...)` | Leave / make-up exam email draft for the student to review (not sent) |
| `log_unanswered(question, reason)` | Logs questions the agent cannot answer to `logs/unanswered_log.csv` |

## Data sources
All documents come from official IIT Jodhpur websites; see `data/csv/sources.csv` for titles, years and URLs.
Instructor email IDs for the current semester are dummy values (personal data).
