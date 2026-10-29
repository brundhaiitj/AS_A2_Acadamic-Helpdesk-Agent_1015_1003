# Person 1 – Step-by-step guide (≈ 3.5 hours)

You build the **first half**: setup → documents → CSV data → RAG → tools → single agent → verified question set → handover.
Every file is already written. You only **run, check, fix data, take screenshots and commit**.

> If any command shows an error, copy the **whole** error and paste it in the chat with Claude.

**Commands:** Windows users type `python`, Mac users type `python3`. Run every command in the **VS Code terminal** (`Ctrl + ~`), inside the project folder, with the virtual environment active (you will see `(.venv)` at the start of the line).

---

## Step 1 – Install tools and start the model download (15 min) ⏱ do this FIRST

1. Install **Python 3.12** (python.org; on Windows tick **"Add Python to PATH"**), **Git** (git-scm.com) and **VS Code** (+ the *Python* extension).
2. Install **Ollama** from ollama.com and open it once.
3. In any terminal, start the downloads (≈ 5.5 GB; let them run while you do Steps 2–4):
   ```
   ollama pull qwen3:8b
   ollama pull nomic-embed-text
   ```
   (`llama3.1:8b` is needed later by Person 2 only.)

## Step 2 – GitHub repo in VS Code (10 min)

1. On github.com → **New repository** → name `academic-helpdesk-agent` → Private → **Create** (do not add a README).
2. Settings → Collaborators → **add Person 2**.
3. In VS Code: `Ctrl+Shift+P` → **Git: Clone** → paste the repo URL → choose a folder → **Open**.
4. Unzip the package Claude gave you and copy **everything inside it** into this folder.
5. Source Control panel (left) → message `Project structure and starter code` → **Commit** → **Sync/Push**.

## Step 3 – Python environment + setup check (10 min)

```
python -m venv .venv
.venv\Scripts\activate            (Windows)      |   source .venv/bin/activate   (Mac)
pip install -r requirements.txt
python check_setup.py
```
✅ All lines must show `[OK ]` (wait until the model downloads have finished).
📸 Screenshot → save as `report/screenshots/01_setup_check.png`.

## Step 4 – Download the documents (25 min)

```
python scripts/download_docs.py
```
Then do by hand:
1. Open https://iitj.ac.in/office-of-academics/en/Academic-Regulations → section **7. Amendments … 2024-25** → download both files and save them in `data/docs/` as
   `amendment_attendance_policy_2024.pdf` and `amendment_examination_policy_2024.pdf`.
2. For any line marked `FAIL`, open the link in the browser and save it in `data/docs/` with **exactly** the printed name.
3. Open each file for a few seconds to confirm it is the right document, and type `yes` in the `checked` column of `data/csv/sources.csv`.
4. Run the script again → it should say *All documents ready*.

Commit: `Add official IIT Jodhpur documents`.

## Step 5 – Verify the course list (35 min)

Open `data/csv/courses.csv` (VS Code or Excel; save as CSV).
- Rows with `data_status = dummy - verify on ERP` are this semester's courses (**AY 2026-27 Sem I**). Open the **ERP course list / time table** and correct: course code, name, slot, classroom, category. Add or delete rows so the list matches what is really floated (especially **Humanities (HS) 300/400-level electives**, **CSL7570**, and a few Chemical Engg. courses).
- Keep instructor emails **dummy** (privacy is allowed by the assignment). You may put the real instructor name.
- After checking a row, change `data_status` to `verified - ERP (email dummy)`.
- Do not change the column names.

Then rebuild the faculty list:
```
python scripts/build_faculty_csv.py
```
Commit: `Verified course list and faculty contacts`.

## Step 6 – Build the RAG index + test retrieval (20 min)

```
python src/ingest.py
python tests/test_retrieval.py
```
✅ Ingest prints every document with its chunk count. Retrieval should show **8/10 or more PASS**.
📸 Screenshots → `02_ingest.png`, `03_retrieval_test.png`.

## Step 7 – Test the tools (10 min)

```
python tests/test_tools.py
```
✅ Check by eye: Autonomous Systems slot matches your CSV, Humanities 400-level count matches, the email draft is created in `outputs/email_drafts/`, and `logs/unanswered_log.csv` has a TEST row.
📸 `04_tools_test.png`

## Step 8 – Run the single agent (30 min)

```
python tests/test_agent.py
```
(5–10 min; the first answer is slow because the model loads.) Read `results/single_agent_smoke_test.md`:
- In-scope answers should be correct and end with `[Source: …]`.
- The **dining** and **reach campus** questions must be refused, and both must appear in `logs/unanswered_log.csv`.

Now the web UI:
```
adk web src
```
Open **http://localhost:8000** → choose **single_agent** → ask 3 questions (one rule question, one slot question, one email) → 📸 `05_adk_web_ui.png` (the UI shows the tool calls). Stop with `Ctrl + C`.

Commit: `Single agent working + test results`.

## Step 9 – Verify the 30 evaluation questions (40 min)

Open `eval/questions.csv`. For **each** row:
1. Open the document in `expected_source` and use `Ctrl+F` to find the answer.
2. Correct `expected_answer` if needed. Update Q13, Q18, Q21, Q23 to match your **verified** `courses.csv`. Check Q01 against the 2024-25 attendance amendment.
3. Type `yes` in `verified_by_person1`.

Commit: `Verified evaluation question set (30 questions)`.

## Step 10 – Handover (15 min)

1. Fill in every `____` in `HANDOVER.md` (numbers from Steps 4–8).
2. Make sure the screenshots are in `report/screenshots/`.
3. Commit `Person 1 handover` → **Push**.
4. Send Person 2 the repo link and say: *"Part 1 done – see HANDOVER.md"*.

🎉 Your half is complete.

---

## Quick fixes

| Problem | Fix |
|---|---|
| `Ollama not reachable` | Open the Ollama app, wait 10 s, try again |
| `adk` / `python` not recognised | Activate the venv again (Step 3, line 2) |
| `pip install` fails on chromadb | Use Python 3.12 (not 3.13/3.14), recreate `.venv` |
| Agent is very slow | Close Chrome tabs / other apps; 16 GB RAM is enough but tight |
| Agent answers without a source, or calls the wrong tool | Paste the question + answer in the chat with Claude |
| A download keeps failing | Save the page/PDF manually from the browser with the exact file name |
