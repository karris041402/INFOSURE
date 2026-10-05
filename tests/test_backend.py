import sqlite3

import pytest
from fastapi.testclient import TestClient

from backend.app import config, db
from backend.app.main import app
from backend.app.pipeline.decision import decide
from backend.app.schemas import Assessment, EvidenceLabel, MLLabel


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "t.db")
    with TestClient(app) as c:
        yield c


@pytest.mark.parametrize(
    "ml,ev,expected",
    [
        (MLLabel.RELIABLE, EvidenceLabel.SUPPORTED, Assessment.STRONG_SUPPORT),
        (MLLabel.MISINFORMATION, EvidenceLabel.CONTRADICTED, Assessment.LIKELY_MISINFORMATION),
        (MLLabel.RELIABLE, EvidenceLabel.CONTRADICTED, Assessment.CONFLICTING),
        (MLLabel.MISINFORMATION, EvidenceLabel.SUPPORTED, Assessment.CONFLICTING),
        (MLLabel.RELIABLE, EvidenceLabel.INSUFFICIENT, Assessment.UNVERIFIED_RELIABLE),
        (MLLabel.MISINFORMATION, EvidenceLabel.INSUFFICIENT, Assessment.UNVERIFIED_MISINFORMATION),
    ],
)
def test_decision_table(ml, ev, expected):
    assert decide(ml, ev) is expected


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_analyze_without_model_is_503(client, monkeypatch):
    monkeypatch.delenv("INFOSURE_MODEL_VERSION", raising=False)
    r = client.post("/analyze", json={"text": "Garlic cures cancer."})
    assert r.status_code == 503


def test_analyze_rejects_empty(client):
    assert client.post("/analyze", json={"text": ""}).status_code == 422


def test_feedback_stored_pending(client):
    r = client.post(
        "/feedback",
        json={"claim_text": "x", "model_prediction": "Reliable", "user_feedback": "Flag"},
    )
    assert r.status_code == 201 and r.json()["review_status"] == "Pending"


def test_feedback_unknown_model_version(client):
    r = client.post(
        "/feedback",
        json={"claim_text": "x", "model_prediction": "Reliable", "user_feedback": "Agree",
              "model_version": "v9"},
    )
    assert r.status_code == 422


def test_only_validated_evidence_visible(tmp_path):
    p = tmp_path / "s.db"
    db.init_db(p)
    with db.connect(p) as c:
        for status in ("Pending", "Validated", "Rejected"):
            c.execute(
                "INSERT INTO evidence (topic, evidence_text, source_name, source_url, review_status)"
                " VALUES ('t',?,'WHO','http://x',?)", (f"e-{status}", status))
        rows = c.execute("SELECT review_status FROM validated_evidence").fetchall()
    assert [r[0] for r in rows] == ["Validated"]


def test_validated_review_requires_label(tmp_path):
    p = tmp_path / "s.db"
    db.init_db(p)
    with db.connect(p) as c:
        c.execute("INSERT INTO feedback (claim_text, model_prediction, user_feedback)"
                  " VALUES ('c','Reliable','Flag')")
        with pytest.raises(sqlite3.IntegrityError):
            c.execute("INSERT INTO feedback_reviews (feedback_id, review_status, reviewer)"
                      " VALUES (1,'Validated','me')")


def test_single_deployed_model(tmp_path):
    p = tmp_path / "s.db"
    db.init_db(p)
    with db.connect(p) as c:
        c.execute("INSERT INTO model_versions (model_version, artifact_path, deployment_status)"
                  " VALUES ('v1','m/v1','Deployed')")
        with pytest.raises(sqlite3.IntegrityError):
            c.execute("INSERT INTO model_versions (model_version, artifact_path, deployment_status)"
                      " VALUES ('v2','m/v2','Deployed')")


# --- evidence ingestion ---
from backend.app.ingest import ingest_csv, split_passages  # noqa: E402


def _csv(tmp_path, rows):
    import csv
    p = tmp_path / "e.csv"
    with open(p, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["source", "url", "title", "text"])
        w.writeheader()
        w.writerows(rows)
    return p


def test_split_passages_respects_limit_and_abbreviations():
    text = "Fr. Gatus did not reveal a cure. " + " ".join(f"Sentence number {i} is here." for i in range(60))
    passages = split_passages(text, max_chars=200)
    assert passages[0].startswith("Fr. Gatus did not reveal a cure.")
    assert all(len(p) <= 260 for p in passages)
    assert " ".join(passages) == " ".join(text.split())


def test_ingest_pending_idempotent_and_requires_source(tmp_path):
    p = tmp_path / "s.db"
    db.init_db(p)
    csv_path = _csv(tmp_path, [
        {"source": "verafiles", "url": "http://a", "title": "T", "text": "Garlic does not cure cancer. " * 5},
        {"source": "", "url": "http://b", "title": "T", "text": "No source given here at all."},
    ])
    with db.connect(p) as c:
        first = ingest_csv(c, csv_path)
        second = ingest_csv(c, csv_path)
        statuses = {r[0] for r in c.execute("SELECT review_status FROM evidence")}
        visible = c.execute("SELECT COUNT(*) FROM validated_evidence").fetchone()[0]
    assert first["passages_added"] >= 1 and first["rows_rejected"] == 1
    assert second["passages_added"] == 0 and second["passages_skipped"] == first["passages_added"]
    assert statuses == {"Pending"} and visible == 0
