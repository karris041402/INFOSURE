"""Evidence ingestion (thesis sections 5 and 8).

Loads a source CSV into the `evidence` table. Articles are split into short passages so retrieval
can match a claim to a specific passage. Every row is inserted as `Pending`; nothing becomes
retrievable until a human sets it to `Validated`. Re-running is safe (duplicates are skipped).

CSV columns: source, url, title, text. Optional: publication_date.

Usage:
    py -m backend.app.ingest data/evidence/verafiles_factchecks_v0.csv
"""
import argparse
import csv
import re
import sqlite3
import sys
from pathlib import Path

from . import db

MAX_PASSAGE_CHARS = 600
MIN_PASSAGE_CHARS = 40

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z“\"‘'])")
_ABBREVIATIONS = ("Fr.", "Dr.", "Mr.", "Mrs.", "Ms.", "Sr.", "Jr.", "St.", "No.", "Sec.", "vs.", "Atty.")


def _sentences(text: str) -> list[str]:
    merged: list[str] = []
    for part in _SENTENCE_SPLIT.split(text.strip()):
        if merged and merged[-1].endswith(_ABBREVIATIONS):
            merged[-1] = f"{merged[-1]} {part}"
        else:
            merged.append(part)
    return merged


def split_passages(text: str, max_chars: int = MAX_PASSAGE_CHARS) -> list[str]:
    """Group consecutive sentences into passages of at most max_chars (a long sentence stays whole)."""
    passages: list[str] = []
    current = ""
    for sentence in _sentences(" ".join(text.split())):
        if current and len(current) + 1 + len(sentence) > max_chars:
            passages.append(current)
            current = sentence
        else:
            current = f"{current} {sentence}".strip()
    if current:
        passages.append(current)
    # fold a tiny trailing fragment into the previous passage
    if len(passages) > 1 and len(passages[-1]) < MIN_PASSAGE_CHARS:
        passages[-2] = f"{passages[-2]} {passages.pop()}"
    return passages


def ingest_csv(conn: sqlite3.Connection, path: Path | str) -> dict[str, int]:
    stats = {"articles": 0, "passages_added": 0, "passages_skipped": 0, "rows_rejected": 0}
    with open(path, encoding="utf-8", newline="") as f, conn:
        for row in csv.DictReader(f):
            source, url = (row.get("source") or "").strip(), (row.get("url") or "").strip()
            title, text = (row.get("title") or "").strip(), (row.get("text") or "").strip()
            if not (source and url and text):
                stats["rows_rejected"] += 1  # evidence must stay traceable: source and URL are required
                continue
            stats["articles"] += 1
            for passage in split_passages(text):
                cur = conn.execute(
                    "INSERT OR IGNORE INTO evidence "
                    "(topic, evidence_text, source_name, source_url, publication_date) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (title or source, passage, source, url, (row.get("publication_date") or "").strip() or None),
                )
                stats["passages_added" if cur.rowcount else "passages_skipped"] += 1
    return stats


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ingest evidence passages as Pending.")
    parser.add_argument("csv_path", type=Path)
    args = parser.parse_args(argv)
    if not args.csv_path.is_file():
        print(f"File not found: {args.csv_path}", file=sys.stderr)
        return 1
    db.init_db()
    with db.connect() as conn:
        stats = ingest_csv(conn, args.csv_path)
    print(stats)
    print("All new passages are Pending and not retrievable until validated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
