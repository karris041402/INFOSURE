import json

import joblib
import pytest

from backend.app import config, db, deploy
from backend.app.pipeline import model_store
from backend.app.pipeline.model_store import ModelNotAvailable
from training.classical import build_svm

CFG = {"seed": 1, "tfidf": {"ngram_range": [1, 1], "min_df": 1, "max_features": 100},
       "svm": {"C": 1.0, "class_weight": "balanced"}}
GOOD = {"macro_f1": 0.9, "per_class": {"Reliable": {"recall": 0.9}, "Misinformation": {"recall": 0.9}}}
BAD = {"macro_f1": 0.5, "per_class": {"Reliable": {"recall": 0.9}, "Misinformation": {"recall": 0.2}}}
REAL_GATE = {"min_macro_f1": 0.8, "min_per_class_recall": 0.7}
DEV_GATE = {"min_macro_f1": 0.0, "min_per_class_recall": 0.0}


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "t.db")
    monkeypatch.setattr(config, "MODELS_DIR", tmp_path / "models")
    monkeypatch.delenv("INFOSURE_MODEL_VERSION", raising=False)
    model_store._load.cache_clear()
    db.init_db()
    return tmp_path


def register(env, version, metrics=GOOD, gate=REAL_GATE, model_type="svm"):
    d = env / "models" / version
    d.mkdir(parents=True)
    joblib.dump(build_svm(CFG).fit(["cure everything", "vaccination helps"], ["Misinformation", "Reliable"]), d / "model.joblib")
    (d / "metadata.json").write_text(json.dumps(
        {"model_version": version, "model_type": model_type, "acceptance_gate": gate, "metrics": metrics}), encoding="utf-8")
    with db.connect() as c:
        c.execute("INSERT INTO model_versions (model_version, artifact_path) VALUES (?, ?)", (version, str(d)))


def status(version):
    with db.connect() as c:
        return c.execute("SELECT deployment_status FROM model_versions WHERE model_version=?", (version,)).fetchone()[0]


def test_deploy_gated_model_and_pipeline_uses_it(env):
    register(env, "v1")
    with db.connect() as c:
        assert "deployed v1" in deploy.deploy(c, "v1")
    assert status("v1") == "Deployed"
    classifier = model_store.load_model()  # resolved from the database, no env override
    label, confidence = classifier.predict("miracle cure everything")
    assert classifier.version == "v1" and label in ("Reliable", "Misinformation") and 0 <= confidence <= 1


def test_deploy_retires_the_previous_model(env):
    register(env, "v1")
    register(env, "v2")
    with db.connect() as c:
        deploy.deploy(c, "v1")
        deploy.deploy(c, "v2")
    assert (status("v1"), status("v2")) == ("Retired", "Deployed")


def test_failed_gate_is_never_deployed_even_with_override(env):
    register(env, "v1", metrics=BAD)
    with db.connect() as c:
        with pytest.raises(ValueError, match="fails its acceptance gate"):
            deploy.deploy(c, "v1", allow_dev_model=True)
    assert status("v1") == "Candidate"


def test_dev_model_needs_the_explicit_override(env):
    register(env, "v0-dev", metrics=BAD, gate=DEV_GATE)  # a disabled gate passes any metrics
    with db.connect() as c:
        with pytest.raises(ValueError, match="allow-dev-model"):
            deploy.deploy(c, "v0-dev")
        assert status("v0-dev") == "Candidate"
        assert "WARNING" in deploy.deploy(c, "v0-dev", allow_dev_model=True)
    assert status("v0-dev") == "Deployed"


def test_unknown_or_unsupported_models_are_refused(env):
    register(env, "tf1", model_type="transformer")
    with db.connect() as c:
        with pytest.raises(ValueError, match="not registered"):
            deploy.deploy(c, "nope")
        with pytest.raises(ValueError, match="Unsupported model type"):
            deploy.deploy(c, "tf1")


def test_undeploy_and_no_model_error(env):
    register(env, "v1")
    with db.connect() as c:
        deploy.deploy(c, "v1")
        assert deploy.undeploy(c) == 1
    with pytest.raises(ModelNotAvailable, match="No deployed model"):
        model_store.load_model()


def test_loader_rejects_unsupported_type(env):
    register(env, "tf1", model_type="transformer")
    with pytest.raises(ModelNotAvailable, match="transformer"):
        model_store._load(str(config.MODELS_DIR), "tf1")


def test_cli_list(env, capsys):
    register(env, "v1")
    assert deploy.main(["list"]) == 0
    assert "v1" in capsys.readouterr().out
    assert deploy.main(["deploy", "missing"]) == 1
