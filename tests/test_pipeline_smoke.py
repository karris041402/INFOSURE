"""Runs data/eval/pipeline_smoke_cases.csv through /analyze with a tiny throwaway model.

Checks pipeline BEHAVIOR (scope routing, evidence rule, decision), not model accuracy.
"""
import csv
from pathlib import Path

import joblib
import pytest
from fastapi.testclient import TestClient

from backend.app import config
from backend.app.main import app
from backend.app.pipeline import stages
from backend.app.pipeline.model_store import _load
from training.classical import build_svm

CASES = list(csv.DictReader(open(
    Path(__file__).resolve().parents[1] / "data" / "eval" / "pipeline_smoke_cases.csv", encoding="utf-8")))
CFG = {"seed": 1, "tfidf": {"ngram_range": [1, 2], "min_df": 1, "max_features": 1000},
       "svm": {"C": 1.0, "class_weight": "balanced"}, "nb": {"alpha": 1.0}}


@pytest.fixture
def client(tmp_path, monkeypatch):
    models = tmp_path / "models" / "vtest"
    models.mkdir(parents=True)
    pipe = build_svm(CFG).fit(
        ["miracle cure heals everything", "doctors recommend vaccination", "garlic cures cancer",
         "exercise improves heart health"],
        ["Misinformation", "Reliable", "Misinformation", "Reliable"])
    joblib.dump(pipe, models / "model.joblib")
    (models / "metadata.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "t.db")
    monkeypatch.setattr(config, "MODELS_DIR", tmp_path / "models")
    monkeypatch.setenv("INFOSURE_MODEL_VERSION", "vtest")
    _load.cache_clear()
    with TestClient(app) as c:
        yield c


@pytest.mark.parametrize("case", CASES, ids=[c["text"][:40] for c in CASES])
def test_scope_routing(client, case):
    r = client.post("/analyze", json={"text": case["text"]})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["scope"] == case["expected_scope"]
    if case["expected_scope"] == "verified":
        assert body["ml_label"] in ("Reliable", "Misinformation")
        assert 0 <= body["ml_confidence"] <= 1
        assert body["model_version"] == "vtest"
        # no validated evidence exists -> must be Insufficient, never a fake/true verdict
        assert body["evidence_result"] == "Insufficient Evidence"
        # the model estimate is still shown, marked as not verified
        assert body["assessment"] == f"Not verified: model estimate is {body['ml_label']} / use caution"
        assert body["evidence"] == []
    else:
        assert body["ml_label"] is None and body["message"]


def test_extract_claim_picks_the_assertion():
    text = "I think this is scary. Drinking bleach cures COVID-19. What should I do?"
    assert stages.extract_claim(text) == "Drinking bleach cures COVID-19."


def test_candidate_model_not_used_implicitly(client, monkeypatch):
    monkeypatch.delenv("INFOSURE_MODEL_VERSION")
    assert client.post("/analyze", json={"text": "Garlic cures cancer."}).status_code == 503
