# Handover: Person 1 → Person 2

Fill every `____` before handing over.

## 1. Status checklist
- [ ] `python check_setup.py` → all OK
- [ ] Documents downloaded: ____ files in `data/docs/` (target 20–30)
- [ ] Both 2024-25 amendment PDFs added manually
- [ ] `courses.csv` verified against ERP: ____ rows verified, ____ rows still dummy
- [ ] `faculty.csv` rebuilt
- [ ] RAG index built: ____ chunks from ____ documents (`results/ingest_summary.csv`)
- [ ] Retrieval test: ____ / 10 PASS (`results/retrieval_test.csv`)
- [ ] Tool test passed (`results/tools_test.md`)
- [ ] Single agent smoke test: ____ / 8 in-scope correct, ____ / 2 refusals correct (`results/single_agent_smoke_test.md`)
- [ ] 30 evaluation questions verified (`eval/questions.csv`)
- [ ] Screenshots in `report/screenshots/` (01–05)

## 2. Notes for Person 2
- Model used for testing: qwen3:8b (Ollama) | embedding: nomic-embed-text
- Average answer time of the single agent: ____ seconds
- Documents that could NOT be downloaded / were replaced: ____
- Data that is dummy (privacy): instructor emails (all current-semester courses), ____
- Problems faced and how they were fixed: ____
- Questions where the single agent was wrong in the smoke test: ____

## 3. How to run Part 1 (for Person 2)
```
pip install -r requirements.txt
python check_setup.py
python src/ingest.py          # rebuild the vector store (chroma_db is not in git)
python tests/test_agent.py    # confirms the single agent works on your laptop
```
Tools contract (do not rename): `search_documents`, `lookup_course`, `count_electives`,
`get_instructor_email`, `draft_email`, `log_unanswered` — all in `src/tools.py`.
Run any agent programmatically with `runner.ask(agent, question)` → returns answer, tools used, agents used, time.

## 4. Draft text for the report (Part 1 – system built by Person 1)

**Document collection.** ____ official documents were collected from IIT Jodhpur websites (iitj.ac.in and department sub-sites): academic regulations (UG/PG), two 2024-25 policy amendments, an office-order notification, the AY 2026-27 academic calendars, B.Tech/M.Tech/PhD curricula (Chemical, CSE, EE, ME, AI, DCS), the School of Liberal Arts course list, the list of programmes, the first-year time table and announcement pages. Web pages were converted to clean text. Structured data (courses, slots, instructors) was kept in CSV files; instructor emails were replaced with dummy values to protect personal data.

**RAG pipeline.** Each document is split page-wise into overlapping chunks (≈900 characters, 150-character overlap) and embedded locally with `nomic-embed-text` through Ollama. Chunks are stored in a persistent ChromaDB collection (cosine similarity) with metadata — title, file, page, year, category and URL — which the agent uses to cite its answers. The top 5 chunks are returned per query. Retrieval hit@3 on 10 test queries: ____/10.

**Tools.** (1) `search_documents` – semantic search over the vector store; (2) `lookup_course` – course slot/instructor/credits from the course CSV; (3) `count_electives` – counts electives by department and level for the current semester; (4) `get_instructor_email` – instructor and department-office email; (5) `draft_email` – builds a leave / make-up-exam email draft with the relevant rule and saves it (never sends); (6) `log_unanswered` – appends unanswerable questions to `logs/unanswered_log.csv` for a human.

**Single agent (base version).** A Google ADK `LlmAgent` running `qwen3:8b` via LiteLLM/Ollama (temperature 0, 8k context, thinking off) with all six tools. Its instruction restricts it to academic topics, forbids answering from memory, requires a `[Source: …, p. …]` citation, and makes it call `log_unanswered` and give a fixed refusal for out-of-scope questions. Smoke test: ____.
