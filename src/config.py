"""
Central settings for the Academic Helpdesk Agent.

Change the model here (or set the HELPDESK_MODEL environment variable)
to compare LLMs, e.g.  qwen3:8b  or  llama3.1:8b
"""
import os
from pathlib import Path

# ---------- Folders ----------
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DOCS_DIR = DATA_DIR / "docs"            # downloaded PDFs / text pages
CSV_DIR = DATA_DIR / "csv"
SOURCES_CSV = CSV_DIR / "sources.csv"   # list of documents + metadata
COURSES_CSV = CSV_DIR / "courses.csv"   # courses, slots, instructors
FACULTY_CSV = CSV_DIR / "faculty.csv"   # instructors + department office emails

CHROMA_DIR = ROOT / "chroma_db"         # local vector store (auto-created)
COLLECTION_NAME = "iitj_academic_docs"

LOG_DIR = ROOT / "logs"
UNANSWERED_LOG = LOG_DIR / "unanswered_log.csv"
EMAIL_DRAFT_DIR = ROOT / "outputs" / "email_drafts"
RESULTS_DIR = ROOT / "results"

# ---------- Models (served by Ollama) ----------
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
os.environ.setdefault("OLLAMA_API_BASE", OLLAMA_BASE_URL)  # used by LiteLLM

CHAT_MODEL = os.getenv("HELPDESK_MODEL", "qwen3:8b")   # use qwen3:4b on 8 GB RAM laptops
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")

# ---------- RAG settings ----------
CHUNK_SIZE = 900        # characters per chunk
CHUNK_OVERLAP = 150     # characters shared between neighbouring chunks
TOP_K = 5               # chunks returned per search

# Semester used by the "current semester" course tools
CURRENT_SEMESTER = "AY 2026-27 Sem I"


def litellm_model_name() -> str:
    """Model string that Google ADK passes to LiteLLM."""
    return f"ollama_chat/{CHAT_MODEL}"


def litellm_model_kwargs() -> dict:
    """Extra settings for deterministic, laptop-friendly runs."""
    kwargs = {
        "temperature": 0,
        "num_ctx": int(os.getenv("HELPDESK_NUM_CTX", "8192")),   # context window (tokens)
        "timeout": int(os.getenv("HELPDESK_TIMEOUT", "300")),    # give up on one model call after 5 min
    }
    if "qwen3" in CHAT_MODEL:
        kwargs["reasoning_effort"] = "none"   # turns off Qwen3 'thinking' mode
    return kwargs
