import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

DB_PATH = Path(os.environ.get("INFOSURE_DB", ROOT / "data" / "infosure.db"))
MODELS_DIR = Path(os.environ.get("INFOSURE_MODELS_DIR", ROOT / "models"))
INDEX_DIR = Path(os.environ.get("INFOSURE_INDEX_DIR", ROOT / "data" / "index"))

EMBEDDING_MODEL = os.environ.get(
    "INFOSURE_EMBEDDING_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)
RETRIEVAL_TOP_K = int(os.environ.get("INFOSURE_TOP_K", "3"))
# Placeholder: cosine similarity below this means "no relevant evidence" (-> Insufficient Evidence).
# Tune on validated claim/evidence pairs (HealthVer) before trusting it.
SIMILARITY_MIN = float(os.environ.get("INFOSURE_SIMILARITY_MIN", "0.40"))

# Multilingual NLI cross-encoder used for evidence verification (MIT license per its model card).
NLI_MODEL = os.environ.get("INFOSURE_NLI_MODEL", "MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7")
# Placeholder: a passage must entail/contradict the claim with at least this probability to count.
# Tune on HealthVer dev with `py -m training.eval_verifier` before trusting it.
NLI_MIN_CONFIDENCE = float(os.environ.get("INFOSURE_NLI_MIN_CONFIDENCE", "0.70"))
