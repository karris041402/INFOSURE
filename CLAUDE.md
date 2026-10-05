# CLAUDE.md — INFOSURE

Authoritative spec: `DOCUMENTATION/THESIS CONTEXT ARCHITECTURE.docx`. If this file and the docx disagree, the docx wins. Ask the user before deviating from it.

## Thesis

**Hybrid NLP and Ensemble Machine Learning Browser Extension for Claim-Level Misinformation Detection and Evidence-Based Verification in Online Health Information.**

Research question: can an evidence-aware verification layer improve the reliability and usefulness of ML-based health misinformation detection compared with classification alone?

The system does not label a whole post real or fake. It finds health-related verifiable claims, classifies each with ML, retrieves trusted evidence, compares claim to evidence, and shows an explainable result.

## Repo layout

Fresh structure, built from the thesis docx. Old Flask project is gone.

- `backend/app/deploy.py` — `py -m backend.app.deploy list|deploy VERSION [--allow-dev-model]|undeploy`. Only a model that passed its acceptance gate can be deployed; `pipeline/model_store.py` loads it behind a `Classifier` interface chosen by `model_type` (svm, nb now; add a loader for the transformer later).
- `backend/app/review.py` — human validation CLI (`py -m backend.app.review evidence review --reviewer NAME`, `evidence set`, `feedback set`, `index build`). Only Validated evidence is retrievable; the vector index (`data/index/`, git-ignored) must be rebuilt after changes or `/analyze` returns 503. `pipeline/evidence_index.py` + `embeddings.py` do retrieval (multilingual MiniLM, `SIMILARITY_MIN` is a placeholder). Verification: `pipeline/nli.py` (mDeBERTa XNLI, premise=passage, hypothesis=claim) + `pipeline/verification.py` (aggregate: Supported/Contradicted need a confident passage with no strong opposite; conflict or weak = Insufficient). Threshold `NLI_MIN_CONFIDENCE` is a placeholder; evaluate with `py -m training.eval_verifier --split dev` (tune on dev, report test once).
- `backend/app/` — FastAPI app and pipeline stages (health filter, claim detect/extract, ML predict, retrieve, verify, decide, explain).
- `extension/` — Chrome extension, Manifest V3.
- `training/` — offline training pipeline (split, train, tune, evaluate, package).
- `data/evidence/` — validated evidence sources, separate from training data.
- `data/raw/` — untouched scraper/download output. Never edit; never clean in place.
- `training/prepare/` — dataset cleaning (`convert_pubhealth.py` builds `data/training/pubhealth_v0.csv` from raw PUBHEALTH; `clean.py`: drop bad rows, dedupe, tag language, write a NEW versioned CSV + report). Not model text preprocessing.
- `data/training/` — labeled training datasets with provenance, versioned.
- `models/` — versioned model artifacts (e.g. `models/v1.0/`).
- `tests/` — tests for the new code.
- `DOCUMENTATION/` — thesis spec (authoritative).
- `training/` pipeline: `run.py` (entry: split → train → select on val → test once → gate → package), `split.py`, `classical.py` (SVM, NB), `transformer.py` (stub), `evaluate.py` (metrics + gate), `package.py` (writes `models/<version>/`, registers Candidate), `configs/default.json` (acceptance-gate numbers are placeholders). Run: `py -m training.run <clean csv> --version vX.Y`.
- `training/scrapers/` — fact-check scrapers copied from the old project (VERA Files etc.). Untested here; they write output to the current directory.
- `training/features/` — copied `health_lexicon.py`, `statistical_scoring.py`, `preprocessing.py` (needs `nltk`). Not wired into the pipeline.

The old Flask project (`legacy/`) was deleted on the user's approval after datasets and reusable code were copied out. Current data: `data/training/seed_health_claims_v0.csv` (65 rows; 50 labels are proposed and need review) and `data/evidence/verafiles_factchecks_v0.csv` (11 articles, all Pending). Both are too small to train or verify on.

## Target architecture

Three layers; build in this order of priority:

1. **Chrome extension** (Manifest V3, HTML/CSS/JS or TS). User-facing. Primary input mode: user-highlighted text. Extended mode (Phase 2): automatic page scan with segmentation.
2. **Backend API**: Python + **FastAPI**. Loads a versioned model artifact.
3. **Storage**: SQLite for prototype.

Prototype path: extension → claim detection/extraction → FastAPI → ML prediction → SQLite evidence retrieval → evidence verification → decision layer → explainable result.

### Live verification flow

1. Capture content (highlighted text first).
2. Health-domain detection. Not health → return out-of-scope.
3. Verifiable-claim detection. No claim → return "No Verifiable Health Claim Detected". Never force true/false on opinions or questions.
4. Claim extraction (isolate the factual assertion).
5. ML classification → `Reliable` or `Misinformation` plus confidence.
6. Evidence retrieval (semantic search over the SQLite evidence repository).
7. Evidence verification → `Supported`, `Contradicted`, or `Insufficient Evidence`.
8. Decision layer combines ML result and evidence result; show both, agreement or conflict, and references.

Decision table:

| ML | Evidence | Presentation |
|---|---|---|
| Reliable | Supported | Supported / strong agreement |
| Misinformation | Contradicted | Likely misinformation / strong agreement |
| Reliable | Contradicted | Conflicting assessment |
| Misinformation | Supported | Conflicting assessment |
| Reliable | Insufficient | Not verified: model estimate is Reliable / use caution |
| Misinformation | Insufficient | Not verified: model estimate is Misinformation / use caution |

### Components

- **ML classifier**: ensemble candidates Linear SVM (TF-IDF), Naive Bayes, RoBERTa/transformer. Pattern-based; it does NOT look up the evidence DB. Keep classifier labels (`Reliable`/`Misinformation`) distinct from evidence labels (`Supported`/`Contradicted`/`Insufficient`).
- **Evidence repository** (SQLite): `evidence_id`, `topic/normalized_claim`, `evidence_text`, `source_name`, `source_url`, `publication_date`, `review_status` (Pending/Validated/Rejected), `embedding_reference`, `created_at/updated_at`. Only `Validated` rows are retrievable. Embeddings from a sentence-transformer or equivalent.
- **Feedback repository** (SQLite): `feedback_id`, `claim_text`, `model_prediction`, `model_confidence`, `evidence_result`, `user_feedback` (Agree/Disagree/Flag), `review_status`, `validated_label`, `model_version`, `created_at`.
- **Tables**: `evidence`, `feedback`, `feedback_reviews`, `dataset_versions`, `model_versions`. Model files/checkpoints are versioned artifacts on disk, not DB rows.

## Decisions and approval

The user has decided that every decision and docx change made in this project is treated as approved. Do not add or ask for an adviser-approval step. The docx stays the spec, but record changes to it in `DOCUMENTATION/PROGRESS.md` and keep a backup in `DOCUMENTATION/archive/` before editing it.

## Hard rules (from thesis section 10)

- Only health-related, verifiable claims go to verification.
- "Verifiable" does not mean "true".
- No relevant evidence → `Insufficient Evidence`, never automatically fake.
- Source credibility is a signal, not proof. A trusted source does not make every statement true.
- User feedback must NOT retrain the production model without human validation.
- Never present model confidence as factual certainty.
- Always keep evidence source and date so results stay traceable and auditable.
- Show conflicts transparently; do not collapse them into a real/fake label.
- Novelty claim must be backed by the literature review. Do not invent citations or claim novelty in code/docs.

## Training pipeline (offline, separate from live inference)

Curate labeled dataset → clean/dedupe/validate → stratified split (70/15/15 or 80/10/10) → train SVM, NB, transformer independently → validate/tune/build ensemble → test once → version → deploy to FastAPI.

- Training data and the evidence repository are separate; document each.
- Split before model development. Prevent leakage: near-duplicates, reposts, same-source items must not span train and test.
- Preprocessing is model-specific. TF-IDF models: normalized text. Transformers: natural sentences with the model's tokenizer; keep negation.
- Choose hyperparameters, thresholds, ensemble weights from validation results, not by hand. If the ensemble does not beat the best single model, say so.
- Metrics: accuracy, precision, recall, F1, macro-F1, class recall, confusion matrix. Report false-positive and false-negative examples.
- Deploy only after the predefined acceptance gate passes.
- Package: model/checkpoint, tokenizer/vectorizer, label mapping, threshold/ensemble config, training date, dataset version, metrics, model version (e.g. `v1.0`).
- Retraining is a later step, only after validation and model-versioning are stable. Active learning (prioritize low-confidence and ML-vs-evidence conflicts for review) is optional.

## Extraction modes

- **Phase 1 (primary)**: user-highlighted text only; send only the selection to the backend.
- **Phase 2 (extended)**: whole page → extract → segment → health filter → claim detection → each claim goes through the SAME ML + evidence pipeline, result per claim. Never classify a whole article as one item. Only the acquisition stage differs; do not build a second verification system.

Finish and evaluate Phase 1 before Phase 2.

## Working conventions

- Environment: Windows, XAMPP path `C:\xampp\htdocs\INFOSURE`, Python via `py`. A `.git` directory now exists; check `git status` before relying on it.
- Dependencies: create `backend/requirements.txt` and `training/requirements.txt` when the first code lands; pin versions. Tests: `py -m pytest tests`.
- New code goes only in `backend/`, `extension/`, `training/`, `tests/`.
- Never commit or overwrite `*.pkl`, `*.db`, or datasets without saying so. Treat them as versioned artifacts; bump the model/dataset version instead of silently replacing.
- Match existing code style in each area. Keep changes minimal and tied to the thesis architecture.
- Cite the docx section number when a change is driven by it. If a request conflicts with the thesis rules above, flag it before implementing.
- Scope text for defense: user-selected text is the primary claim source; automatic scanning is a planned extended mode feeding the same pipeline.
