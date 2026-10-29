"""
STEP: Build the vector store (RAG index).

Reads every PDF / TXT in data/docs, splits it into overlapping chunks,
embeds each chunk with Ollama (nomic-embed-text) and stores it in ChromaDB
together with metadata used for citations (title, file, page, year, url).

Run:  python src/ingest.py
"""
import csv
import re
import sys
import time
from pathlib import Path

import chromadb
from pypdf import PdfReader

import config
from embeddings import embed_texts

JUNK_PATTERNS = [
    r"###\d+\$\$\$_RedirectToLoginPage_%%%\d+!!!",
    r"arrow_downward",
    r"\[Back to index\]",
]


def clean_text(text: str) -> str:
    for pat in JUNK_PATTERNS:
        text = re.sub(pat, " ", text)
    text = text.replace(" ", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()


def load_sources() -> dict:
    """file name -> metadata row from data/csv/sources.csv"""
    meta = {}
    if config.SOURCES_CSV.exists():
        with open(config.SOURCES_CSV, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                meta[row["file"].strip()] = row
    return meta


def read_pages(path: Path) -> list[tuple[int, str]]:
    """Return [(page_number, text)]. Text files are split into ~3000-char 'sections'."""
    if path.suffix.lower() == ".pdf":
        reader = PdfReader(str(path))
        return [(i + 1, clean_text(p.extract_text() or "")) for i, p in enumerate(reader.pages)]
    text = clean_text(path.read_text(encoding="utf-8", errors="ignore"))
    sections, current = [], ""
    for para in text.split("\n\n"):
        if len(current) + len(para) > 3000 and current:
            sections.append(current)
            current = ""
        current += para + "\n\n"
    if current.strip():
        sections.append(current)
    return [(i + 1, s.strip()) for i, s in enumerate(sections)]


def chunk_text(text: str, size: int = config.CHUNK_SIZE, overlap: int = config.CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping chunks, cutting at word boundaries."""
    words = text.split()
    chunks, current = [], []
    length = 0
    for word in words:
        current.append(word)
        length += len(word) + 1
        if length >= size:
            chunks.append(" ".join(current))
            # keep the last `overlap` characters worth of words
            keep, kept_len = [], 0
            for w in reversed(current):
                if kept_len + len(w) + 1 > overlap:
                    break
                keep.insert(0, w)
                kept_len += len(w) + 1
            current, length = keep, kept_len
    if current and (not chunks or len(" ".join(current)) > overlap):
        chunks.append(" ".join(current))
    return chunks


def main():
    files = sorted(p for p in config.DOCS_DIR.iterdir()
                   if p.suffix.lower() in {".pdf", ".txt", ".md"})
    if not files:
        sys.exit("No documents in data/docs. Run: python scripts/download_docs.py")

    sources = load_sources()
    client = chromadb.PersistentClient(path=str(config.CHROMA_DIR))
    try:
        client.delete_collection(config.COLLECTION_NAME)   # rebuild from scratch
    except Exception:
        pass
    collection = client.create_collection(config.COLLECTION_NAME, metadata={"hnsw:space": "cosine"})

    summary = []
    total_chunks = 0
    start = time.time()
    for path in files:
        meta = sources.get(path.name, {})
        title = meta.get("title") or path.stem.replace("_", " ")
        try:
            pages = read_pages(path)
        except Exception as e:
            print(f"  !! Could not read {path.name}: {e}")
            continue

        ids, docs, metas = [], [], []
        for page_no, page_text in pages:
            for c_idx, chunk in enumerate(chunk_text(page_text)):
                if len(chunk) < 40:
                    continue
                ids.append(f"{path.name}::p{page_no}::c{c_idx}")
                docs.append(chunk)
                metas.append({
                    "file": path.name,
                    "title": title,
                    "page": page_no,
                    "category": meta.get("category", ""),
                    "year": meta.get("year", ""),
                    "url": meta.get("url", ""),
                })
        if not docs:
            print(f"  !! {path.name}: no text found (scanned PDF?) - skipped")
            summary.append((path.name, len(pages), 0))
            continue

        vectors = embed_texts(docs, kind="document")
        for i in range(0, len(docs), 200):
            collection.add(ids=ids[i:i + 200], documents=docs[i:i + 200],
                           metadatas=metas[i:i + 200], embeddings=vectors[i:i + 200])
        total_chunks += len(docs)
        summary.append((path.name, len(pages), len(docs)))
        print(f"  ok  {path.name:<55} pages/sections={len(pages):<4} chunks={len(docs)}")

    config.RESULTS_DIR.mkdir(exist_ok=True)
    with open(config.RESULTS_DIR / "ingest_summary.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["file", "pages_or_sections", "chunks"])
        w.writerows(summary)

    print("\n" + "=" * 70)
    print(f"Documents indexed : {sum(1 for s in summary if s[2] > 0)}")
    print(f"Total chunks      : {total_chunks}")
    print(f"Time taken        : {time.time() - start:.0f} s")
    print(f"Vector store      : {config.CHROMA_DIR}")
    print("Summary saved to  : results/ingest_summary.csv")


if __name__ == "__main__":
    main()
