import json
import sqlite3

import joblib
import pandas as pd
import pytest

from training import run
from training.evaluate import check_gate, evaluate
from training.split import split_dataset

RATIOS = {"train": 0.70, "val": 0.15, "test": 0.15}


def _synthetic(n_per_class=40):
    rows = []
    for i in range(n_per_class):
        rows.append({"text": f"Herbal remedy number {i} cures every disease instantly, miracle cure",
                     "label": "Misinformation"})
        rows.append({"text": f"Clinical guideline {i} recommends regular exercise and balanced diet",
                     "label": "Reliable"})
    return pd.DataFrame(rows)


def test_split_stratified_disjoint_deterministic():
    df = _synthetic()
    a = split_dataset(df, RATIOS, seed=1)
    b = split_dataset(df, RATIOS, seed=1)
    assert sum(len(v) for v in a.values()) == len(df)
    texts = [set(a[s]["text"]) for s in a]
    assert not (texts[0] & texts[1]) and not (texts[0] & texts[2]) and not (texts[1] & texts[2])
    for part in a.values():
        assert set(part["label"]) == {"Reliable", "Misinformation"}
    assert a["train"]["text"].tolist() == b["train"]["text"].tolist()


def test_split_keeps_groups_together():
    df = _synthetic()
    df["url"] = [f"http://src/{i // 4}" for i in range(len(df))]  # 4 rows share a source
    parts = split_dataset(df, RATIOS, seed=3, group_column="url")
    owner = {}
    for name, part in parts.items():
        for u in part["url"]:
            assert owner.setdefault(u, name) == name


def test_split_rejects_tiny_class():
    df = pd.DataFrame({"text": ["a long enough claim one", "a long enough claim two",
                                "misinfo claim number one", "misinfo claim number two", "misinfo claim number three",
                                "misinfo claim number four", "misinfo claim number five"],
                       "label": ["Reliable"] * 2 + ["Misinformation"] * 5})
    with pytest.raises(ValueError, match="at least 3"):
        split_dataset(df, RATIOS, seed=1)


def test_evaluate_and_gate():
    y_true = ["Reliable", "Reliable", "Misinformation", "Misinformation"]
    y_pred = ["Reliable", "Misinformation", "Misinformation", "Reliable"]
    m = evaluate(y_true, y_pred, ["a", "b", "c", "d"])
    assert m["accuracy"] == 0.5
    assert m["error_examples"] == {"false_positives": ["b"], "false_negatives": ["d"]}
    assert m["confusion_matrix"]["matrix"] == [[1, 1], [1, 1]]
    ok, failures = check_gate(m, {"min_macro_f1": 0.8, "min_per_class_recall": 0.7})
    assert not ok and len(failures) == 3


def _args(tmp_path, dataset, config, version="v0.1"):
    return [str(dataset), "--version", version, "--config", str(config),
            "--models-dir", str(tmp_path / "models"), "--runs-dir", str(tmp_path / "runs"),
            "--splits-dir", str(tmp_path / "splits"), "--db", str(tmp_path / "t.db")]


def _config(tmp_path, gate):
    cfg = json.loads(run.DEFAULT_CONFIG.read_text(encoding="utf-8"))
    cfg["acceptance_gate"] = gate
    p = tmp_path / "cfg.json"
    p.write_text(json.dumps(cfg), encoding="utf-8")
    return p


def test_pipeline_packages_when_gate_passes(tmp_path):
    data = tmp_path / "d.csv"
    _synthetic().to_csv(data, index=False)
    cfg = _config(tmp_path, {"min_macro_f1": 0.5, "min_per_class_recall": 0.5})
    assert run.main(_args(tmp_path, data, cfg)) == 0

    model_dir = tmp_path / "models" / "v0.1"
    meta = json.loads((model_dir / "metadata.json").read_text(encoding="utf-8"))
    assert meta["model_version"] == "v0.1" and meta["dataset_sha256"] and meta["labels"]
    pipe = joblib.load(model_dir / "model.joblib")
    assert pipe.predict(["miracle herbal cure for every disease"])[0] == "Misinformation"
    with sqlite3.connect(tmp_path / "t.db") as c:
        assert c.execute("SELECT deployment_status FROM model_versions").fetchone()[0] == "Candidate"
    # a second run with the same version must refuse, not overwrite
    assert run.main(_args(tmp_path, data, cfg)) == 1


def test_pipeline_blocks_when_gate_fails(tmp_path):
    data = tmp_path / "d.csv"
    _synthetic().to_csv(data, index=False)
    cfg = _config(tmp_path, {"min_macro_f1": 1.01, "min_per_class_recall": 0.5})
    assert run.main(_args(tmp_path, data, cfg)) == 2
    assert not (tmp_path / "models" / "v0.1").exists()
    assert json.loads((tmp_path / "runs" / "v0.1" / "report.json").read_text(encoding="utf-8"))["gate_passed"] is False


def test_pipeline_rejects_uncleaned_labels(tmp_path):
    data = tmp_path / "d.csv"
    pd.DataFrame({"text": ["some claim text here"], "label": ["FAKE"]}).to_csv(data, index=False)
    assert run.main(_args(tmp_path, data, _config(tmp_path, {"min_macro_f1": 0, "min_per_class_recall": 0}))) == 1
