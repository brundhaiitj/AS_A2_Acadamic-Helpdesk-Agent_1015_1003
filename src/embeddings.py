"""
Turns text into vectors using a local embedding model served by Ollama.
nomic-embed-text works best with the prefixes 'search_document:' and 'search_query:'.
"""
import requests

import config


def _prefix(text: str, kind: str) -> str:
    if "nomic" in config.EMBED_MODEL:
        return ("search_query: " if kind == "query" else "search_document: ") + text
    return text


def embed_texts(texts: list[str], kind: str = "document", batch_size: int = 16) -> list[list[float]]:
    """Return one embedding vector per text. kind = 'document' or 'query'."""
    vectors: list[list[float]] = []
    for i in range(0, len(texts), batch_size):
        batch = [_prefix(t, kind) for t in texts[i:i + batch_size]]
        resp = requests.post(
            f"{config.OLLAMA_BASE_URL}/api/embed",
            json={"model": config.EMBED_MODEL, "input": batch},
            timeout=300,
        )
        if resp.status_code == 404:          # very old Ollama: one text at a time
            for text in batch:
                r = requests.post(
                    f"{config.OLLAMA_BASE_URL}/api/embeddings",
                    json={"model": config.EMBED_MODEL, "prompt": text},
                    timeout=300,
                )
                r.raise_for_status()
                vectors.append(r.json()["embedding"])
            continue
        resp.raise_for_status()
        vectors.extend(resp.json()["embeddings"])
    return vectors
