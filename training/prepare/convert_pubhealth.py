"""Convert raw PUBHEALTH parquet files into the pipeline's `text,label` format.

Mapping: label 2 (true) -> Reliable, label 0 (false) -> Misinformation.
Dropped: mixture (1), unproven (3), unlabeled (-1), and the filters below.

Why the filters exist (checked on the raw data):
- Rows with no `fact_checkers` are mostly news headlines (e.g. Reuters Health), not verifiable claims,
  and are almost all `true`. Keeping them teaches the model "headline style = Reliable".
- `--health-only` keeps rows whose `subjects` tag looks health-related. Without it, many `false`
  rows are political claims, so the model would learn "politics = Misinformation".
Both filters are ON by default; turn them off only to measure how much they matter.

Usage:
    py -m training.prepare.convert_pubhealth data/training/pubhealth_v0.csv
Then clean:  py -m training.prepare.clean data/training/pubhealth_v0.csv data/training/pubhealth_v1.csv
"""
import argparse
import json
import sys
from pathlib import Path

import pandas as pd

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw" / "pubhealth"
SPLIT_FILES = ["pubhealth_train.parquet", "pubhealth_validation.parquet", "pubhealth_test.parquet"]
LABELS = {0: "Misinformation", 2: "Reliable"}
HEALTH_TAG_WORDS = (
    "health", "medic", "covid", "coronavirus", "vaccin", "cancer", "disease", "drug", "pharma",
    "nutrition", "diet", "fitness", "mental", "virus", "flu", "hospital", "doctor", "surgery",
    "pregnan", "diabetes", "obesity", "autism", "opioid", "fda", "cdc", "who",
)


def _is_health_tag(subjects: str) -> bool:
    tags = [t.strip().lower() for t in str(subjects or "").split(",")]
    # exact word match for short tags like "who" / "fda" / "cdc"; substring for the rest
    return any(
        (w in tag.split()) if len(w) <= 3 else (w in tag) for tag in tags for w in HEALTH_TAG_WORDS
    )


def convert(df: pd.DataFrame, require_fact_checker: bool = True, health_only: bool = True) -> tuple[pd.DataFrame, dict]:
    report: dict = {"rows_in": len(df)}
    df = df.copy()
    df["claim"] = df["claim"].fillna("").astype(str)

    df = df[df["label"].isin(LABELS)]
    report["after_label_filter (true/false only)"] = len(df)
    if require_fact_checker:
        df = df[df["fact_checkers"].fillna("").str.strip() != ""]
        report["after_fact_checker_filter"] = len(df)
    if health_only:
        df = df[df["subjects"].map(_is_health_tag)]
        report["after_health_filter"] = len(df)

    out = pd.DataFrame({
        "text": df["claim"],
        "label": df["label"].map(LABELS),
        "source": "PUBHEALTH",
        "health_topic": df["subjects"].fillna(""),
        "unit": "claim",
        "label_status": "dataset_label",
        "origin": "data/raw/pubhealth",
        "group": df["claim_id"].astype(str),
        "fact_checker": df["fact_checkers"].fillna(""),
    }).reset_index(drop=True)
    report["class_counts"] = out["label"].value_counts().to_dict()
    return out, report


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Convert PUBHEALTH parquet files to text,label CSV.")
    p.add_argument("output", type=Path)
    p.add_argument("--raw-dir", type=Path, default=RAW_DIR)
    p.add_argument("--keep-headlines", action="store_true", help="do not require a fact checker")
    p.add_argument("--keep-non-health", action="store_true", help="do not filter by health subject tags")
    args = p.parse_args(argv)
    if args.output.exists():
        print(f"Refusing to overwrite {args.output}", file=sys.stderr)
        return 1
    missing = [f for f in SPLIT_FILES if not (args.raw_dir / f).is_file()]
    if missing:
        print(f"Missing in {args.raw_dir}: {missing}", file=sys.stderr)
        return 1

    raw = pd.concat([pd.read_parquet(args.raw_dir / f) for f in SPLIT_FILES], ignore_index=True)
    out, report = convert(raw, not args.keep_headlines, not args.keep_non_health)
    out.to_csv(args.output, index=False, encoding="utf-8")
    args.output.with_suffix(".convert-report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
