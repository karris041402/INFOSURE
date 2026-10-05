"""Dataset cleaning (thesis section 13.1). Not text preprocessing for models (section 13.4).

Reads a labeled CSV, drops unusable rows, removes duplicates, tags language, and writes a new
versioned CSV plus a JSON report. The input file is never modified.

Required columns: text, label (Reliable | Misinformation).
All other columns (source, url, label_status, ...) are kept so provenance survives.

Usage:
    py -m training.prepare.clean data/training/seed_health_claims_v0.csv \
        data/training/seed_health_claims_v1.csv
"""
import argparse
import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

import pandas as pd

VALID_LABELS = {"Reliable", "Misinformation"}
MIN_CHARS = 15

# Common Tagalog function words. Used only to tag language; not a translation or filter.
_TAGALOG = {
    "ang", "ng", "sa", "na", "ay", "mga", "ko", "mo", "ka", "kapag", "kung", "pag", "ito", "iyon",
    "hindi", "walang", "may", "at", "para", "bawal", "lahat", "ibig", "sabihin", "lang", "si", "ni",
    "kay", "niya", "namin", "natin", "naman", "dahil", "ba", "po", "yung", "nang", "pa", "din", "rin",
}
_ENGLISH = {
    "the", "is", "are", "can", "of", "to", "and", "in", "that", "it", "for", "with", "you", "your",
    "will", "cure", "causes", "all", "not", "from", "be", "by", "or", "any", "every", "does", "do",
}
_WORD = re.compile(r"[a-zA-Z']+")


def normalize_text(text: str) -> str:
    return " ".join(unicodedata.normalize("NFC", str(text)).split())


def dedupe_key(text: str) -> str:
    return re.sub(r"[\W_]+", " ", text.casefold()).strip()


def detect_language(text: str) -> str:
    """Return 'en', 'tl', or 'mixed' (Taglish) from function-word counts."""
    words = [w.lower() for w in _WORD.findall(text)]
    tl = sum(w in _TAGALOG for w in words)
    en = sum(w in _ENGLISH for w in words)
    if tl and en:
        return "mixed"
    if tl:
        return "tl"
    return "en"


def clean(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    dropped: Counter = Counter()
    df = df.copy()
    df["text"] = df["text"].fillna("").map(normalize_text)
    df["label"] = df["label"].fillna("").astype(str).str.strip()

    keep = df["text"].str.len() >= MIN_CHARS
    dropped["empty_or_too_short"] = int((~keep).sum())
    df = df[keep]

    keep = df["label"].isin(VALID_LABELS)
    dropped["invalid_label"] = int((~keep).sum())
    df = df[keep]

    key = df["text"].map(dedupe_key)
    conflict = df.groupby(key)["label"].transform("nunique") > 1
    dropped["conflicting_duplicate_labels"] = int(conflict.sum())
    df, key = df[~conflict], key[~conflict]

    dup = key.duplicated()
    dropped["duplicate"] = int(dup.sum())
    df = df[~dup]

    df["language"] = df["text"].map(detect_language)
    report = {
        "rows_out": len(df),
        "dropped": {k: v for k, v in dropped.items() if v},
        "class_counts": df["label"].value_counts().to_dict(),
        "language_counts": df["language"].value_counts().to_dict(),
    }
    if "unit" in df.columns:
        report["unit_counts"] = df["unit"].value_counts().to_dict()
    return df.reset_index(drop=True), report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Clean a labeled dataset into a new version.")
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args(argv)
    if not args.input.is_file():
        print(f"File not found: {args.input}", file=sys.stderr)
        return 1
    if args.output.resolve() == args.input.resolve() or args.output.exists():
        print(f"Refusing to overwrite {args.output}. Pick a new version name.", file=sys.stderr)
        return 1

    df = pd.read_csv(args.input, encoding="utf-8")
    missing = {"text", "label"} - set(df.columns)
    if missing:
        print(f"Missing columns: {sorted(missing)}", file=sys.stderr)
        return 1

    cleaned, report = clean(df)
    report["input"], report["rows_in"] = str(args.input), len(df)
    cleaned.to_csv(args.output, index=False, encoding="utf-8")
    args.output.with_suffix(".report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
