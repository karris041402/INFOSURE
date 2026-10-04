import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

DB_PATH = Path(os.environ.get("INFOSURE_DB", ROOT / "data" / "infosure.db"))
MODELS_DIR = Path(os.environ.get("INFOSURE_MODELS_DIR", ROOT / "models"))
