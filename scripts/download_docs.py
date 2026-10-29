"""
STEP: Download all official IIT Jodhpur documents listed in data/csv/sources.csv.

    python scripts/download_docs.py

- PDFs are saved as-is.
- Web pages are converted to clean text (.txt) so they can be indexed.
- Rows with type 'manual' must be downloaded by hand (instructions are printed).
"""
import csv
import re
import sys
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "data" / "docs"
SOURCES = ROOT / "data" / "csv" / "sources.csv"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AcademicHelpdeskStudentProject/1.0"}
JUNK = re.compile(r"###\d+\$\$\$_RedirectToLoginPage_%%%\d+!!!|arrow_downward")


def html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "header", "footer", "noscript", "form"]):
        tag.decompose()
    # keep table rows readable:  cell | cell | cell
    for tr in soup.find_all("tr"):
        cells = [c.get_text(" ", strip=True) for c in tr.find_all(["td", "th"])]
        tr.replace_with(soup.new_string(" | ".join(cells) + "\n"))
    main = soup.find("main") or soup.find(id=re.compile("content", re.I)) or soup.body or soup
    text = main.get_text("\n", strip=True)
    text = JUNK.sub("", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def main():
    DOCS.mkdir(parents=True, exist_ok=True)
    rows = list(csv.DictReader(open(SOURCES, newline="", encoding="utf-8")))
    ok, failed, manual = [], [], []

    for row in rows:
        out = DOCS / row["file"]
        if row["type"] == "manual":
            if out.exists():
                ok.append(row["file"])
            else:
                manual.append(row)
            continue
        if out.exists() and out.stat().st_size > 1000:
            print(f"  skip (already downloaded)  {row['file']}")
            ok.append(row["file"])
            continue
        try:
            r = requests.get(row["url"], headers=HEADERS, timeout=60)
            r.raise_for_status()
            if row["type"] == "pdf":
                if not r.content.startswith(b"%PDF"):
                    raise ValueError("response is not a PDF")
                out.write_bytes(r.content)
            else:
                text = html_to_text(r.text)
                header = f"{row['title']}\nSource: {row['url']}\nDownloaded: {time.strftime('%Y-%m-%d')}\n\n"
                out.write_text(header + text, encoding="utf-8")
            print(f"  ok   {row['file']:<50} {out.stat().st_size // 1024} KB")
            ok.append(row["file"])
        except Exception as e:
            print(f"  FAIL {row['file']:<50} {e}")
            failed.append(row)
        time.sleep(1)  # be polite to the server

    print("\n" + "=" * 70)
    print(f"Downloaded/present: {len(ok)}   Failed: {len(failed)}   Manual: {len(manual)}")
    if failed:
        print("\nOpen these links in your browser and save them into data/docs with EXACTLY this name:")
        for row in failed:
            ext = "PDF (Save as...)" if row["type"] == "pdf" else "page text (copy all text into a .txt file)"
            print(f"  - {row['file']}   <-  {row['url']}   [{ext}]")
    if manual:
        print("\nMANUAL downloads (open the page, click 'Download file' next to the item, save with this name):")
        for row in manual:
            print(f"  - {row['file']}   <-  '{row['title']}' on {row['url']}")
    if not failed and not manual:
        print("All documents ready. Next: python src/ingest.py")
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
