import hashlib
import sqlite3

import numpy as np
import pytest
from fastapi.testclient import TestClient

from backend.app import config, db, review
from backend.app.main import app
from backend.app.pipeline import embeddings, evidence_index, nli, stages
from backend.app.pipeline.evidence_index import EvidenceIndexStale


def fake_embed(texts):
    """Deterministic bag-of-words vectors (no model download)."""
    out = np.zeros((len(texts), 128), np.float32)
    for i, t in enumerate(texts):
        for w in t.lower().replace(".", " ").split():
            out[i, int(hashlib.md5(w.encode()).hexdigest(), 16) % 128] += 1
    norms = np.linalg.norm(out, axis=1, keepdims=True)
    return out / np.where(norms == 0, 1, norms)


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "t.db")
    monkeypatch.setattr(config, "INDEX_DIR", tmp_path / "index")
    monkeypatch.setattr(config, "SIMILARITY_MIN", 0.3)
    monkeypatch.setattr(embeddings, "embed", fake_embed)
    db.init_db()
    with db.connect() as c:
        for text in ["Garlic does not cure cancer according to oncology studies.",
                     "Handwashing with soap reduces the spread of infections.",
                     "Measles vaccination prevents measles outbreaks."]:
            c.execute("INSERT INTO evidence (topic, evidence_text, source_name, source_url) "
                      "VALUES ('t', ?, 'WHO', 'http://who')", (text,))
    return tmp_path


def conn():
    return db.connect()


def test_migration_adds_audit_columns(tmp_path):
    p = tmp_path / "old.db"
    with sqlite3.connect(p) as c:
        c.execute("CREATE TABLE evidence (evidence_id INTEGER PRIMARY KEY, topic TEXT, evidence_text TEXT, "
                  "source_name TEXT, source_url TEXT, publication_date TEXT, review_status TEXT, "
                  "embedding_reference TEXT, created_at TEXT, updated_at TEXT)")
    db.init_db(p)
    with db.connect(p) as c:
        cols = {r[1] for r in c.execute("PRAGMA table_info(evidence)")}
    assert {"reviewed_by", "reviewed_at"} <= cols


def test_set_status_records_reviewer_and_validates_input(env):
    with conn() as c:
        review.set_evidence_status(c, [1, 2], "Validated", "ana")
        row = c.execute("SELECT review_status, reviewed_by, reviewed_at FROM evidence WHERE evidence_id=1").fetchone()
        assert tuple(row)[:2] == ("Validated", "ana") and row["reviewed_at"]
        with pytest.raises(ValueError, match="reviewer"):
            review.set_evidence_status(c, [3], "Validated", " ")
        with pytest.raises(ValueError, match="not found"):
            review.set_evidence_status(c, [999], "Validated", "ana")
        with pytest.raises(ValueError, match="status"):
            review.set_evidence_status(c, [3], "Maybe", "ana")


def test_interactive_review(env):
    answers = iter(["v", "x", "r", "q"])  # 'x' is invalid and re-prompts
    with conn() as c:
        done = review.review_interactive(c, "ana", input_fn=lambda _: next(answers), out=lambda s: None)
        stats = review.evidence_stats(c)
    assert done == {"Validated": 1, "Rejected": 1, "skipped": 0}
    assert stats == {"Pending": 1, "Validated": 1, "Rejected": 1}


def test_feedback_review_needs_label_and_logs(env):
    with conn() as c:
        c.execute("INSERT INTO feedback (claim_text, model_prediction, user_feedback) VALUES ('c','Reliable','Flag')")
        with pytest.raises(ValueError, match="label"):
            review.set_feedback_status(c, 1, "Validated", "ana")
        review.set_feedback_status(c, 1, "Validated", "ana", label="Misinformation", notes="checked")
        assert c.execute("SELECT review_status FROM feedback").fetchone()[0] == "Validated"
        r = c.execute("SELECT validated_label, reviewer FROM feedback_reviews").fetchone()
        assert tuple(r) == ("Misinformation", "ana")


def test_pending_evidence_is_never_retrieved(env):
    with conn() as c:
        assert evidence_index.search(c, "Garlic cures cancer") == []  # nothing validated


def test_build_and_search(env):
    with conn() as c:
        review.set_evidence_status(c, [1, 2, 3], "Validated", "ana")
        assert evidence_index.status(c)["stale"] is True
        meta = evidence_index.build_index(c)
        assert meta["ids"] == [1, 2, 3] and evidence_index.status(c)["stale"] is False
        refs = [r[0] for r in c.execute("SELECT embedding_reference FROM evidence ORDER BY evidence_id")]
        assert all(r and "#" in r for r in refs)
        hits = evidence_index.search(c, "Garlic cures cancer")
        assert hits and hits[0].evidence_id == 1 and 0 < hits[0].similarity <= 1
        assert hits[0].source_name == "WHO" and hits[0].source_url
        assert evidence_index.search(c, "stock market closed higher on Friday") == []


def test_index_goes_stale_and_rejected_evidence_disappears(env):
    with conn() as c:
        review.set_evidence_status(c, [1, 2], "Validated", "ana")
        evidence_index.build_index(c)
        review.set_evidence_status(c, [3], "Validated", "ana")        # new approval
        with pytest.raises(EvidenceIndexStale):
            evidence_index.search(c, "measles vaccination")
        evidence_index.build_index(c)
        assert evidence_index.search(c, "measles vaccination")[0].evidence_id == 3
        review.set_evidence_status(c, [3], "Rejected", "ana")         # rejection after approval
        with pytest.raises(EvidenceIndexStale):
            evidence_index.search(c, "measles vaccination")
        evidence_index.build_index(c)
        assert evidence_index.search(c, "measles vaccination") == []
        assert c.execute("SELECT embedding_reference FROM evidence WHERE evidence_id=3").fetchone()[0] is None


def test_analyze_uses_retrieval(env, monkeypatch):
    import joblib
    from backend.app.pipeline.model_store import _load
    from training.classical import build_svm
    cfg = {"seed": 1, "tfidf": {"ngram_range": [1, 1], "min_df": 1, "max_features": 100},
           "svm": {"C": 1.0, "class_weight": "balanced"}}
    mdir = env / "models" / "vtest"
    mdir.mkdir(parents=True)
    joblib.dump(build_svm(cfg).fit(["cure everything", "vaccination helps"], ["Misinformation", "Reliable"]),
                mdir / "model.joblib")
    (mdir / "metadata.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(config, "MODELS_DIR", env / "models")
    monkeypatch.setenv("INFOSURE_MODEL_VERSION", "vtest")
    _load.cache_clear()
    with conn() as c:
        review.set_evidence_status(c, [1, 2, 3], "Validated", "ana")
    with TestClient(app) as client:
        # validated but not indexed -> refuse (503), never silently ignore
        assert client.post("/analyze", json={"text": "Garlic cures cancer."}).status_code == 503
        with conn() as c:
            evidence_index.build_index(c)
        # evidence found and NLI says the passage entails the claim -> Supported, shown with its relation
        monkeypatch.setattr(nli, "predict", lambda prem, hyp: np.array([[0.9, 0.05, 0.05]] * len(prem)))
        r = client.post("/analyze", json={"text": "Garlic cures cancer."}).json()
        assert r["evidence_result"] == "Supported" and r["evidence"][0]["relation"] == "entailment"
        assert r["evidence"][0]["relation_score"] == pytest.approx(0.9) and r["assessment"]
        # NLI says contradiction -> Contradicted
        monkeypatch.setattr(nli, "predict", lambda prem, hyp: np.array([[0.05, 0.05, 0.9]] * len(prem)))
        assert client.post("/analyze", json={"text": "Garlic cures cancer."}).json()["evidence_result"] == "Contradicted"
        # weak/neutral NLI -> Insufficient, never a guess
        monkeypatch.setattr(nli, "predict", lambda prem, hyp: np.array([[0.3, 0.5, 0.2]] * len(prem)))
        r = client.post("/analyze", json={"text": "Garlic cures cancer."}).json()
        assert r["evidence_result"] == "Insufficient Evidence" and r["assessment"].startswith("Not verified")
        # nothing similar -> Insufficient Evidence
        r = client.post("/analyze", json={"text": "Ginger tea kills bacteria."})
        assert r.status_code == 200 and r.json()["evidence_result"] == "Insufficient Evidence"


def test_aggregate_rules():
    from backend.app.pipeline.verification import aggregate
    from backend.app.schemas import EvidenceLabel as L
    t = 0.7
    assert aggregate(np.zeros((0, 3)), t) is L.INSUFFICIENT
    assert aggregate(np.array([[0.8, 0.1, 0.1]]), t) is L.SUPPORTED
    assert aggregate(np.array([[0.1, 0.1, 0.8]]), t) is L.CONTRADICTED
    assert aggregate(np.array([[0.6, 0.3, 0.1]]), t) is L.INSUFFICIENT           # below threshold
    assert aggregate(np.array([[0.2, 0.7, 0.1]]), t) is L.INSUFFICIENT           # neutral
    assert aggregate(np.array([[0.8, 0.1, 0.1], [0.1, 0.1, 0.85]]), t) is L.INSUFFICIENT  # passages conflict
    assert aggregate(np.array([[0.8, 0.1, 0.1], [0.3, 0.5, 0.2]]), t) is L.SUPPORTED     # one strong, one weak
    assert aggregate(np.array([[0.7, 0.0, 0.7]]), t) is L.INSUFFICIENT                   # same passage both


def test_verify_without_evidence_is_insufficient():
    from backend.app.schemas import EvidenceLabel as L
    assert stages.verify("anything", []) == (L.INSUFFICIENT, [])
