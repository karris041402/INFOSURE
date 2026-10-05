"""Evaluate the NLI verifier on HealthVer (thesis 13.7 applied to evidence verification).

HealthVer: Supports -> Supported, Refutes -> Contradicted, Neutral -> Insufficient Evidence.
Rule: choose the confidence threshold on `dev`, then report `test` ONCE with that threshold.

Usage:
    py -m training.eval_verifier --split dev                    # sweep thresholds
    py -m training.eval_verifier --split test --threshold 0.80  # final report at the chosen threshold
    add --limit N for a quick smoke run
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix, precision_recall_fscore_support

from backend.app import config
from backend.app.pipeline import nli, verification
from backend.app.schemas import EvidenceLabel

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "raw" / "healthver"
MAP = {"Supports": EvidenceLabel.SUPPORTED, "Refutes": EvidenceLabel.CONTRADICTED,
       "Neutral": EvidenceLabel.INSUFFICIENT}
ORDER = [EvidenceLabel.SUPPORTED, EvidenceLabel.CONTRADICTED, EvidenceLabel.INSUFFICIENT]


def score(df: pd.DataFrame) -> np.ndarray:
    return nli.predict(df["evidence"].astype(str).tolist(), df["claim"].astype(str).tolist())


def report(y_true: list[str], probs: np.ndarray, threshold: float) -> dict:
    # one passage per pair here, so aggregate() sees a single row
    y_pred = [verification.aggregate(p[None, :], threshold).value for p in probs]
    labels = [l.value for l in ORDER]
    prec, rec, f1, sup = precision_recall_fscore_support(y_true, y_pred, labels=labels, zero_division=0)
    return {
        "threshold": threshold,
        "accuracy": float(np.mean(np.array(y_true) == np.array(y_pred))),
        "macro_f1": float(f1.mean()),
        "per_class": {l: {"precision": float(p), "recall": float(r), "f1": float(f), "support": int(s)}
                      for l, p, r, f, s in zip(labels, prec, rec, f1, sup)},
        "confusion_matrix": {"labels": labels, "matrix": confusion_matrix(y_true, y_pred, labels=labels).tolist()},
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--split", choices=["dev", "test"], required=True)
    p.add_argument("--threshold", type=float, help="single threshold (use on test after tuning on dev)")
    p.add_argument("--limit", type=int)
    p.add_argument("--out", type=Path, default=ROOT / "training" / "runs")
    args = p.parse_args(argv)
    if args.split == "test" and args.threshold is None:
        print("error: report test with a threshold chosen on dev (--threshold)", file=sys.stderr)
        return 1

    df = pd.read_csv(DATA / f"healthver_{args.split}.csv", encoding="utf-8")
    if args.limit:
        df = df.sample(args.limit, random_state=0)
    probs = score(df)
    y_true = [MAP[l].value for l in df["label"]]
    thresholds = [args.threshold] if args.threshold is not None else [0.5, 0.6, 0.7, 0.8, 0.9]
    reports = [report(y_true, probs, t) for t in thresholds]
    for r in reports:
        pc = r["per_class"]
        print(f"t={r['threshold']:.2f} acc={r['accuracy']:.3f} macroF1={r['macro_f1']:.3f} | "
              + " ".join(f"{k.split()[0][:5]} P={v['precision']:.2f} R={v['recall']:.2f}" for k, v in pc.items()))
    if args.threshold is not None:
        print(json.dumps(reports[0]["confusion_matrix"]))
    args.out.mkdir(parents=True, exist_ok=True)
    out = args.out / f"verifier_{args.split}.json"
    out.write_text(json.dumps({"nli_model": config.NLI_MODEL, "split": args.split, "n": len(df),
                               "reports": reports}, indent=2), encoding="utf-8")
    print("saved", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
