# InfoSure Technology Stack

Status: **proposed**. Items marked OPEN need a decision or an experiment before they are final.
The thesis docx (`THESIS CONTEXT ARCHITECTURE.docx`) is authoritative. Section 17 of it mirrors this file.

## Fit with the thesis docx

| Component | In docx? | Choice here | Fit |
|---|---|---|---|
| Browser interface | Yes (sec. 9) | Chrome Extension, Manifest V3, JS/TS | Matches |
| Backend API | Yes (sec. 9) | Python + FastAPI | Matches |
| Storage | Yes (sec. 5, 9, 14.2) | SQLite | Matches |
| Traditional classifiers | Yes (sec. 4, 13.5) | Linear SVM + Naive Bayes on TF-IDF (scikit-learn) | Matches |
| Transformer classifier | Yes, "for example RoBERTa" | `xlm-roberta-base` (multilingual RoBERTa) | Matches; the multilingual variant is a refinement |
| Semantic embeddings | Yes, "sentence-transformer or equivalent" | `paraphrase-multilingual-MiniLM-L12-v2` | Matches |
| Evidence verification method | Required (sec. 5) but method not named | NLI cross-encoder, multilingual (OPEN) | Gap in docx; filled here |
| Health-domain / verifiable-claim detection | Required (sec. 3) but method not named | Lexicon + classifier (OPEN) | Gap in docx; filled here |
| Language scope and translation | **Not mentioned** | English + Tagalog/Taglish; multilingual-first; translation optional | **Addition**; docx updated in section 17 |
| Model versioning | Yes (sec. 13.8) | Folder per version under `models/` + `model_versions` table | Matches |

## Language handling (addition to the docx)

Scope: English and Tagalog, including mixed Taglish.

Primary approach: **multilingual models**, so Tagalog is processed directly with no translation step.

Optional approach: a translation stage (Tagalog/Taglish to English) placed before health-domain detection. It is **not the default**, because translation can flip negation and distort cultural terms ("pasma", "usog"), and it adds a second source of error. Treat it as an experiment: compare accuracy on a hand-labeled Tagalog test set with and without translation. Always keep the original text and show it to the user.

```
selected text -> language tag -> [optional: translate to English] -> health filter -> claim detection
              -> claim extraction -> ML classify + evidence retrieve -> evidence verify -> decision
```

## Components

| Stage | Technology | Notes |
|---|---|---|
| Extension | Chrome MV3, JS/TS | Phase 1: highlighted text. Phase 2: page scan. |
| API | FastAPI, uvicorn, pydantic | Already scaffolded in `backend/`. |
| Database | SQLite | Tables in `backend/app/schema.sql`. |
| Language tag | Function-word heuristic now (`training/prepare/clean.py`) | OPEN: replace with fastText `lid` or `langdetect` if the heuristic is too weak. |
| Health filter, claim detection | Lexicon (`training/features/health_lexicon.py`) plus a small classifier | OPEN: needs labeled data and evaluation. |
| ML classifier | scikit-learn: `LinearSVC`/`SGDClassifier(hinge)`, `MultinomialNB` with TF-IDF; `xlm-roberta-base` fine-tuned with Hugging Face Transformers + PyTorch | Labels: `Reliable` / `Misinformation`. Ensemble weights chosen on validation data only. |
| Embeddings | `sentence-transformers`: `paraphrase-multilingual-MiniLM-L12-v2` | Alternative: `LaBSE` (larger, slower). |
| Vector search | Brute-force cosine similarity over a NumPy matrix | Enough at prototype scale. FAISS only if evidence grows large. Vectors referenced by `embedding_reference`. |
| Evidence verification | Multilingual NLI cross-encoder, labels map to Supported / Contradicted / Insufficient | IMPLEMENTED with `MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7` (MIT per model card, 1.1 GB). Zero-shot on HealthVer dev: accuracy 0.57-0.58, macro-F1 0.41-0.47 (threshold-dependent); see `training/runs/verifier_dev.json`. Test split not yet run. Low confidence, conflict, or no relevant passage returns `Insufficient Evidence`. |
| Translation (optional) | NLLB-200 distilled (about 600M parameters) | License CC-BY-NC: fine for the thesis, not for commercial use. Experiment only. |
| Evaluation | scikit-learn metrics | Accuracy, precision, recall, F1, macro-F1, confusion matrix, per-class recall. |
| Artifacts | `models/<version>/` with model, tokenizer/vectorizer, label map, thresholds, dataset version, metrics | Registered in `model_versions`. |

## Hardware and training configuration

Machine: NVIDIA GeForce RTX 2050, **4 GB VRAM**. Installed PyTorch is CPU-only (`torch 2.13.0+cpu`); the CUDA build must be installed before GPU use.

| Task | Fits in 4 GB? | Settings |
|---|---|---|
| SVM / Naive Bayes training | Yes, CPU | n/a |
| MiniLM embeddings | Yes | batch 32, CPU or GPU |
| `xlm-roberta-base` inference | Yes | fp16 |
| `xlm-roberta-base` fine-tuning | Tight | fp16, batch 8, max length 128, gradient accumulation 4; lower the batch size on out-of-memory |
| NLI verifier inference | Yes | fp16 |
| `xlm-roberta-large`, large translation models, LLMs | No | not planned |

Training must be reproducible: fixed random seeds, pinned library versions, config saved with each model version.

## Licenses

All model licenses below are from memory and **must be checked on each Hugging Face model card before the thesis cites them.**

| Model | License (verify) |
|---|---|
| `xlm-roberta-base` | MIT |
| `paraphrase-multilingual-MiniLM-L12-v2` | Apache 2.0 |
| `LaBSE` | Apache 2.0 |
| NLLB-200 | CC-BY-NC 4.0 (non-commercial) |
| mDeBERTa XNLI candidate | verify |

## Open decisions

1. Whether the translation stage is built at all, or only used as an ablation.
2. NLI verifier model and its acceptance threshold.
3. Health-domain and verifiable-claim detection method.
4. Language-identification method beyond the heuristic.
5. A real labeled dataset: the current seed has 57 Misinformation vs 8 Reliable rows and cannot train or evaluate these models.
