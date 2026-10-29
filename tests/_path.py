"""Lets the test scripts import modules from src/."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

# Windows terminals: avoid crashes on special characters
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
