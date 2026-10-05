"""Traditional candidates (thesis section 13.5): Linear SVM and Naive Bayes on TF-IDF."""
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC


def _tfidf(cfg: dict) -> TfidfVectorizer:
    t = cfg["tfidf"]
    return TfidfVectorizer(
        ngram_range=tuple(t["ngram_range"]), min_df=t["min_df"], max_features=t["max_features"]
    )


def build_svm(cfg: dict) -> Pipeline:
    return Pipeline([
        ("tfidf", _tfidf(cfg)),
        ("clf", LinearSVC(C=cfg["svm"]["C"], class_weight=cfg["svm"]["class_weight"], random_state=cfg["seed"])),
    ])


def build_nb(cfg: dict) -> Pipeline:
    return Pipeline([("tfidf", _tfidf(cfg)), ("clf", MultinomialNB(alpha=cfg["nb"]["alpha"]))])


CANDIDATES = {"svm": build_svm, "nb": build_nb}


def predict_with_confidence(pipe: Pipeline, texts) -> tuple[list[str], list[float]]:
    """Return (labels, confidence in the predicted label).

    NB gives probabilities. The SVM has none: its confidence is a sigmoid of the decision margin and
    is UNCALIBRATED, so it must not be mixed with NB scores or shown as certainty (thesis 13.6).
    """
    clf = pipe.named_steps["clf"]
    labels = list(pipe.predict(texts))
    if hasattr(clf, "predict_proba"):
        conf = pipe.predict_proba(texts).max(axis=1)
    else:
        margin = np.abs(pipe.decision_function(texts))
        conf = 1.0 / (1.0 + np.exp(-margin))
    return labels, [float(c) for c in conf]
