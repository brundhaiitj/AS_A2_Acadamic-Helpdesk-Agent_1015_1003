"""
Run this first:   python check_setup.py
It checks Python, the libraries, Ollama and the models. Every line should say OK.
"""
import importlib
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

ok_all = True


def report(ok, msg, fix=""):
    global ok_all
    ok_all &= ok
    print(f"[{'OK ' if ok else 'XX '}] {msg}" + ("" if ok else f"\n       -> FIX: {fix}"))


# 1. Python version
v = sys.version_info
report(v >= (3, 10), f"Python {v.major}.{v.minor}", "Install Python 3.11 or 3.12")

# 2. Libraries
for lib, pip_name in [("google.adk", "google-adk"), ("litellm", "litellm"), ("chromadb", "chromadb"),
                      ("pypdf", "pypdf"), ("bs4", "beautifulsoup4"), ("pandas", "pandas"), ("requests", "requests")]:
    try:
        importlib.import_module(lib)
        report(True, f"library {pip_name}")
    except Exception as e:
        report(False, f"library {pip_name} ({e})", "pip install -r requirements.txt")

# 3. Ollama + models
try:
    import requests
    import config
    tags = requests.get(f"{config.OLLAMA_BASE_URL}/api/tags", timeout=5).json()
    names = [m["name"] for m in tags.get("models", [])]
    report(True, f"Ollama running at {config.OLLAMA_BASE_URL}")
    for model in [config.CHAT_MODEL, config.EMBED_MODEL]:
        present = any(n == model or n.startswith(model + ":") or n.split(":")[0] == model for n in names)
        report(present, f"model {model}", f"ollama pull {model}")
    if not any(n.startswith("llama3.1") for n in names):
        print("[-- ] model llama3.1:8b not pulled yet (only needed later by Person 2: ollama pull llama3.1:8b)")
except Exception as e:
    report(False, f"Ollama not reachable ({e})", "Open the Ollama app (or run: ollama serve)")

# 4. Embedding + chat smoke tests
if ok_all:
    try:
        from embeddings import embed_texts
        vec = embed_texts(["attendance rules"], kind="query")[0]
        report(len(vec) > 100, f"embedding works (vector size {len(vec)})")
    except Exception as e:
        report(False, f"embedding failed ({e})", f"ollama pull {config.EMBED_MODEL}")
    try:
        import litellm
        litellm.drop_params = True
        r = litellm.completion(model=config.litellm_model_name(),
                               messages=[{"role": "user", "content": "Reply with just the word READY. /no_think"}],
                               **config.litellm_model_kwargs())
        text = r.choices[0].message.content or ""
        report("READY" in text.upper(), f"chat model answers: {text.strip()[:40]!r}")
    except Exception as e:
        report(False, f"chat model failed ({e})", f"ollama pull {config.CHAT_MODEL}")

print("\nALL GOOD - continue to the next step." if ok_all else "\nFix the XX lines above, then run this again.")
