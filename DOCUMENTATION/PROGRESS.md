# InfoSure Progress and Roadmap

Last updated: 2026-10-05 (re-framed as model-centered, option A). Authoritative spec: `THESIS CONTEXT ARCHITECTURE.docx` (section numbers below refer to it).
Companion files: `TECH_STACK.md` (technology choices), `DATASET_CANDIDATES.md` (datasets), `CLAUDE.md` (repo rules for Claude).

## Development purpose (current phase)

**Build the whole working system first: the complete pipeline and system flow, including evidence retrieval, working as intended end to end.** A weak model, a small dataset, and a small evidence repository are acceptable for now, as long as the system visibly behaves as designed. Once the pipeline and flow are complete, the remaining work is mostly model tuning (data, training, thresholds), which only swaps artifacts and does not change the system.

| Phase | Goal | Model / data quality |
|---|---|---|
| **Phase 1 (now): build the system** | Every stage and the full flow work and can be demonstrated, in the browser | Dev model, seed data, small evidence set are fine |
| **Phase 2: tune the model** | Reach the strong classifier that is the thesis contribution (option A below) | Real dataset, training, gate, thresholds |

**Phase 1 is done when these can be shown live** (each on a few prepared examples, in the Chrome extension):
1. Highlight text on a page and receive a result.
2. Non-health text gives "out of scope"; a health opinion or question gives "No Verifiable Health Claim Detected".
3. A verifiable claim shows the model's estimate, clearly labeled.
4. All four evidence outcomes are demonstrable with a small validated evidence set: Supported, Contradicted, Insufficient Evidence, and a Conflicting assessment (ML and evidence disagree), each with its source and date.
5. The user can send feedback; it is stored as Pending and can be reviewed and validated.
6. A new model version can be dropped in and deployed (only through the acceptance gate, or an explicit dev override) without changing pipeline code, including a transformer artifact later.
7. Tagalog/Taglish input flows through the same pipeline.

**Rule for reporting:** Phase 1 results are functional demonstrations, not performance claims. Do not quote accuracy from the dev model or the seed data.

## 0. Thesis framing (decided: option A, model-centered)

**Purpose of the study: build a strong health-misinformation classifier.** The architecture around it is designed assuming a strong model (working target: about 87% on a clean held-out test set; see the target definition below).

- **Main claim:** a claim-level, multilingual (English + Tagalog/Taglish) hybrid classifier detects health misinformation more accurately than single models and simple baselines.
- **Evidence layer = supporting component.** Even at 87% accuracy, about 13 of 100 verdicts are wrong and unidentified. Retrieved, validated evidence acts as a second check and as an explanation: agreement raises confidence, disagreement is shown as "Conflicting assessment", and the passage and its source are visible.
- **Decision (user, 2026-10-05):** when evidence is insufficient, the model's prediction is **still shown** as an unverified estimate (clearly labeled, with a confidence band rather than a percentage). The decision table row "Either prediction + Insufficient" was split into two rows, "Not verified: model estimate is Reliable / use caution" and "Not verified: model estimate is Misinformation / use caution". **Applied on 2026-10-06** in `backend/app/schemas.py` (`Assessment`), `decision.py`, the tests, `CLAUDE.md`, the extension, and docx section 6 (original docx backed up in `DOCUMENTATION/archive/`).
- **Bonus experiment (small, optional):** model alone vs model + evidence on claims that have evidence, reporting how many model errors the evidence catches. Not the main claim.

**Docx section 11 was reworded on 2026-10-06** (original backed up in `DOCUMENTATION/archive/`). It was evidence-centered; it is now model-centered, as in option A. Wording used: *"Can a claim-level multilingual hybrid classifier reliably detect health misinformation in English and Tagalog, and does retrieved evidence help expose its errors?"*

**What "87%" must mean to be defensible** (decide and record this before using it as a target):
- measured on a held-out test set never used for tuning, with balanced or reported class distribution;
- macro-F1 and per-class recall reported next to accuracy;
- claims, not headlines; sources in test separate from train; no style difference between classes;
- results reported separately for English and Tagalog/Taglish.

## 1. Where we are

The backend pipeline now runs end to end on a development setup: a highlighted claim goes through scope checks, ML classification, evidence retrieval, NLI verification, and the decision layer, and returns an explainable result. It is **not usable yet**. For **Phase 1 (build the system)** the gaps are: the Chrome extension, a deploy command, showing the model estimate when evidence is insufficient, a small validated evidence set that exercises all four outcomes, and a model interface that accepts any model artifact. The classifier is a dev-only model near chance on realistic claims; improving it is **Phase 2 (tuning)** and does not block the system.

Docx priority path (section 12): `Chrome extension -> claim detection -> FastAPI -> ML prediction -> SQLite evidence retrieval -> evidence verification -> explainable result`

| Step | Status |
|---|---|
| Chrome extension | **Built (Phase 1): side panel with live highlight**; tested in headless Edge against the real backend; not yet tried by hand in Chrome |
| Claim detection / extraction | Working, rule-based (placeholder) |
| FastAPI | Working (`/health`, `/analyze`, `/feedback`) |
| ML prediction | Working with a **dev-only model**; real model is Phase 2 |
| SQLite evidence retrieval | Working; **no validated evidence yet** |
| Evidence verification | Working, **weak** (zero-shot NLI) |
| Explainable result | Working in the API; no UI |

## 2. Progress against the docx

| Docx section | What it asks for | Status |
|---|---|---|
| 2, 3 Architecture, processing flow | 8-step flow | Steps 2-8 implemented in `backend/app/pipeline/`; step 1 (extension capture) missing |
| 4, 13 ML classifier and training | SVM, NB, transformer; split; validation; test; gate; versioning | Pipeline built for SVM and NB; **transformer is a stub**; no ensemble; no calibration |
| 5 Evidence retrieval and verification | SQLite repository, semantic retrieval, claim vs evidence | Done (MiniLM embeddings, vector index, mDeBERTa NLI) |
| 6 Decision logic | 5-row decision table, show conflicts | Done and tested |
| 7, 14 Adaptive learning | Feedback table, human review, dataset and model versions, controlled retraining | Tables and review CLI done; **no retraining loop**, no deploy command |
| 8 Evidence-base adaptivity | Validate before insert, update index | Done (review CLI rebuilds index; stale index blocks retrieval) |
| 9 Technology stack | Extension, FastAPI, scikit-learn/Transformers, embeddings, SQLite | All chosen; extension and transformer not built |
| 10 Rules | No evidence = Insufficient; no auto-retraining; no certainty claims | Enforced in code (see section 5) |
| 11 Novelty / research question | Evidence-aware vs classification-only | **Reworded 2026-10-06 for option A (model-centered): claim-level multilingual hybrid classifier is the primary object, evidence layer a supporting check.** Nothing evaluated yet |
| 16 Extraction strategy | Phase 1 highlighted text; Phase 2 auto scan | Neither built in the browser; Phase 2 not started |
| 17 Language and technology (added) | English + Tagalog, multilingual-first, optional translation | Written into the docx; translation not built |

## 3. What has been done

### Repository and docs
- Fresh structure: `backend/`, `extension/`, `training/`, `data/`, `models/`, `tests/`, `DOCUMENTATION/`. The old Flask project was reviewed against the thesis, mined for reusable parts, and deleted.
- `CLAUDE.md` with thesis rules; `.gitignore`; `TECH_STACK.md`; `DATASET_CANDIDATES.md`; `PROGRESS.md`.
- Docx updated with **section 17** (original backed up in `DOCUMENTATION/archive/`).

### Backend (`backend/app/`)
- `schema.sql`: `evidence`, `feedback`, `feedback_reviews`, `dataset_versions`, `dataset_version_samples`, `model_versions`; view `validated_evidence`; audit columns; one-deployed-model constraint; migration for older databases.
- `main.py`: `GET /health`, `POST /analyze`, `POST /feedback` (stored as Pending). Errors: 503 no model or stale index.
- `pipeline/`: `lexicon.py` (health and claim rules, English + Tagalog), `stages.py`, `model_store.py` (loads the Deployed model; a Candidate is never used implicitly), `embeddings.py`, `evidence_index.py`, `nli.py`, `verification.py`, `decision.py`, `run.py`.
- `ingest.py`: loads evidence CSV as Pending passages, idempotent, requires source and URL.
- `review.py`: human validation CLI for evidence and feedback, with reviewer audit trail and index rebuild.
- `deploy.py`: deploy / list / undeploy classifier versions. Refuses a model that fails its acceptance gate (no override); a model trained with a disabled gate (dev) needs the explicit `--allow-dev-model`. One Deployed model at a time.
- `pipeline/model_store.py`: loads the deployed model (or `INFOSURE_MODEL_VERSION`) behind a `Classifier` interface chosen by `model_type`; unsupported types (e.g. a transformer, for now) are refused with a clear message.

### Extension (`extension/`)
- Manifest V3 **side panel** (stays open while browsing): `sidepanel.html/.css/.js`, `content.js` (reports highlights from pages), `background.js` (icon click opens the panel), `README.md` with run steps. Permissions: `sidePanel`, host access to `127.0.0.1:8000` / `localhost:8000`, and a content script on http(s) pages.
- The field follows the highlight of the active tab **live**; opening the panel on an existing highlight checks it right away; later highlights fill the field and the user presses Check. Calls `/analyze` and shows: scope message, decision banner, claim checked, **model estimate labeled "not verified" with a low/medium/high band (no percentage)**, evidence cards (source, date, supports/contradicts, link), and Agree / Disagree / Flag feedback to `/feedback` as Pending.
- Page text is only sent to the extension's own panel until the user presses Check. Untrusted text is rendered with `textContent` only; evidence links are limited to http(s).
- Changed from a popup to a side panel on 2026-10-05 because a popup closes when the user clicks the page.
- **v0.3 redesign (2026-10-06):** audience is end users and the thesis panel. The **model verdict (Reliable / Misinformation) is the main, largest card**; the evidence check sits below it. Added EN/TL switch, confidence meter (bands, no percentage), agree / disagree / no-evidence strip, collapsible evidence cards with source, domain and date, "How to read this", Yes/No/Flag feedback, Copy summary, New check, example claims, recent checks (local only), loading skeletons, error card with retry, light/dark and reduced-motion support. Tested with a mocked API (no real server or database): 21/21 checks in headless Edge, including no horizontal overflow, language switch without a new request, and markup shown as text. Tagalog wording is unreviewed.
- v0.2.1: the panel shows a connection line ("Connected to this page" or a clear notice for blocked pages) and injects `content.js` itself into tabs that were open before the extension was loaded (needs `scripting` and http(s) host access). Tested with and without the manifest content script (11/11 checks each), without sending feedback to the real database.
- Verified end to end in headless Edge (same Chromium version as Chrome 154; Chrome itself no longer allows command-line loading of unpacked extensions): 9/9 checks, covering open-on-highlight, live update, hint and hidden stale result, clearing keeps text, Check on live text, feedback saved, background-tab highlight ignored, tab switch shows that tab's highlight. The earlier popup version also passed the scope-routing, Tagalog, and HTML-injection checks (same panel code). Not yet tried by hand in Chrome.
- The "Insufficient" case shows the model estimate; the backend assessment text and docx section 6 say so too (2026-10-06).

### Training (`training/`)
- `prepare/clean.py` (dedupe, label checks, language tag, versioned output), `prepare/convert_pubhealth.py`.
- `split.py` (grouped, stratified 70/15/15), `classical.py` (SVM, NB), `evaluate.py` (metrics, errors, gate), `package.py`, `run.py`, `configs/default.json`, `configs/dev.json` (gate disabled, dev only).
- `eval_verifier.py` (HealthVer evaluation, threshold sweep).
- `scrapers/` and `features/`: copied from the old project, untested here.
- `transformer.py`: interface only.

### Data
| File | Content | State |
|---|---|---|
| `data/training/seed_health_claims_v1.csv` | 65 rows (57 Misinformation / 8 Reliable); 50 labels proposed by the assistant | Too small; labels need review |
| `data/training/pubhealth_v1.csv` | 4,047 rows (2,721 Reliable / 1,326 Misinformation) from PUBHEALTH | Style leakage (Reliable = headlines) |
| `data/raw/pubhealth/`, `data/raw/healthver/` | Raw downloads | PUBHEALTH MIT per dataset card; HealthVer has no license |
| `data/evidence/verafiles_factchecks_v0.csv` | 11 VERA Files articles | 194 passages ingested, **all Pending**; 3 contain HTML junk |
| `data/eval/pipeline_smoke_cases.csv` | 24 hand-written pipeline cases | Author-proposed, needs review |

### Environment
- CUDA PyTorch 2.14.1 working on the RTX 2050 (4 GB). `transformers`, `sentence-transformers`, `nltk` installed.
- 62 automated tests pass (`py -m pytest tests`).

### Measured results (all preliminary)
| Component | Result | Meaning |
|---|---|---|
| Classifier `v0.0-dev` (PUBHEALTH) | test accuracy 0.789, macro-F1 0.772 | Inflated by headline-vs-claim style; failed the placeholder gate (0.80) |
| Same model on 15 hand-written health claims | 8/15 correct | About chance; not trustworthy |
| NLI verifier, HealthVer dev, threshold 0.70 | accuracy 0.576, macro-F1 0.453; precision about 0.6 when it commits, recall about 0.2-0.3 | Cautious but weak; test split not run yet |
| Retrieval on 7 demo-validated passages | Correct passages found, including for Tagalog queries | Works; threshold 0.40 is a placeholder |
| Scope routing on 24 smoke cases | 24/24 | The rules were written alongside these cases, so this is not evidence of general accuracy |

## 4. What is still needed

Groups B, C, D are **Phase 1** (build the system). Group A is **Phase 2** (tune the model) except item 6, which is Phase 1.

### A. The model (Phase 2: main thesis contribution; item 6 is Phase 1)
1. **A real labeled claim dataset.** Thousands of short, verifiable health claims labeled Reliable / Misinformation, balanced, no style gap between classes (not headlines vs viral claims), with provenance and written labeling guidelines (docx 13.1-13.2). Include Tagalog/Taglish claims.
2. **A style-neutral, source-disjoint test set**, plus a hand-labeled Tagalog/Taglish test set. Test is touched once.
3. **Train and compare** SVM, Naive Bayes, and `xlm-roberta-base` independently (docx 13.5). Implement the transformer stage (fp16, batch 8, length 128, gradient accumulation 4).
4. **Validation-driven selection**: thresholds, and an ensemble only if it beats the best single model (13.6); calibrate confidences before mixing or displaying them.
5. **Real acceptance-gate numbers** agreed with the team (current 0.80 / 0.70 are placeholders), baselines (e.g. majority class, TF-IDF + SVM), error analysis with false-positive and false-negative examples (13.7).
6. ~~Deploy command and model-agnostic loader~~ done 2026-10-06: `py -m backend.app.deploy list|deploy VERSION|undeploy`; the loader picks a `Classifier` by `model_type` in `metadata.json`, so adding the transformer later means adding one loader, not touching the pipeline.
7. Optional: translation-vs-multilingual comparison on the Tagalog test set.

### B. Showing the model's prediction (Phase 1; decision made, to implement)
8. ~~Show the model estimate as unverified in the "Insufficient" row~~ done 2026-10-06 (code, tests, docx table).
9. Decide the behavior for very low confidence (suggested: say "no clear estimate" instead of picking a side).

### C. Evidence layer (Phase 1; supporting, keep small and scoped)
10. Limit scope to 15-20 common Philippine health topics and state this scope openly.
11. Review and validate the 194 Pending passages (`py -m backend.app.review evidence review --reviewer NAME`); add authoritative sources (DOH, WHO, PhilHealth, RITM) so Supported can occur.
12. Clean evidence ingestion (strip HTML, add publication dates, check each source's terms of use).
13. Tune the retrieval similarity threshold; optionally fine-tune the NLI verifier on HealthVer train and report its test split once.
14. Small experiment: how many model errors the evidence catches, and evidence coverage of the test claims.

### D. Product and operations (Phase 1, except 16-17 later)
15. ~~Chrome extension (highlighted-text mode)~~ built. Remaining: try it by hand in Chrome (Load unpacked), a Chrome-based automated test that does not depend on headless Edge, icons, and a settings option for the server address; the side panel calls the API directly, so a future in-page overlay would need a background service worker for API calls.
16. Feedback to dataset-version to retrain loop (docx 14), active-learning review queue (low confidence and conflicts first), authentication on review actions, privacy handling of user text.
17. Phase 2: automatic page scan reusing the same pipeline per claim.

### E. Thesis
18. ~~Reword the research question in docx section 11 for option A~~ done 2026-10-06. Objectives elsewhere in the thesis text (outside this docx) still need to match. Docx section 17 and the changed section 6 row are accepted as they are.
19. Related-literature review to support the novelty (claim-level, multilingual Tagalog/Taglish, leakage-free evaluation, evidence-assisted error exposure).

## 5. Docx rules and how they are enforced

| Rule (section 10) | Enforcement |
|---|---|
| Only health, verifiable claims proceed | `/analyze` returns out_of_scope or no_verifiable_health_claim |
| No evidence = Insufficient Evidence | Retrieval returns nothing below the threshold; verification returns Insufficient on weak, neutral, or conflicting passages |
| User feedback never retrains production directly | Feedback stored Pending; validated reviews need a label and reviewer; no retrain code exists |
| Confidence is not certainty | Responses give a score only; SVM score is documented as uncalibrated |
| Sources and dates retained | Evidence rows keep source name, URL, date; the response returns them |
| Conflicts shown transparently | Decision layer returns "Conflicting assessment" |
| Deploy only after the acceptance gate | `run.py` refuses to package on a failed gate; the model store never auto-selects a Candidate |

## 6. Known issues and risks

- The dev classifier is near chance on realistic claims; do not demo its labels as results.
- Training data style leakage (headlines vs viral claims); metrics from it are inflated.
- `lexicon.py` and the smoke cases were written together, so 24/24 is a self-consistency check, not accuracy.
- The language tag is a word-list heuristic and mislabels some English text as Tagalog.
- The NLI model says whether a passage supports a claim, not whether the passage itself is reliable.
- HealthVer has no license; PUBHEALTH content comes from fact-check sites that may hold their own rights. State this in the thesis.
- No git commits were made by the assistant; the repo has one initial commit and many uncommitted changes.
- The old scrapers in `training/scrapers/` and `training/features/` are copied, unrun, and not wired in.

## 7. Suggested order from here

### Phase 1: build the system (current)
1. ~~Apply the decision to show the model estimate when evidence is insufficient~~ done 2026-10-06.
2. ~~Deploy command and model-agnostic loader~~ done 2026-10-06.
3. Small validated evidence set (15-20 topics) that exercises Supported, Contradicted, Insufficient, and Conflicting; DOH/WHO passages for Supported.
4. ~~Chrome extension shell~~ done (see Extension section). Next for it: manual try-out in Chrome, icons, server-address setting.
5. Feedback flow end to end: send from the extension (works), review with the CLI (works for evidence and feedback), then check the review-to-dataset path.
6. Run through the Phase 1 "done" checklist live, in the browser, including a Tagalog example.
7. Optional before Phase 2: Phase 2 of the docx (automatic page scan) and the feedback retraining loop skeleton.

### Phase 2: tune the model
8. Dataset: choose sources, write labeling guidelines, build a balanced claim-level train set and a separate style-neutral, source-disjoint test set (English + Tagalog/Taglish).
9. Retrain SVM and NB with the existing pipeline; set real gate numbers; compare with baselines.
10. Implement and train the `xlm-roberta-base` stage; ensemble only if validation supports it; calibrate; deploy the first gate-passing model.
11. Tune retrieval and NLI thresholds; optionally fine-tune the verifier on HealthVer.
12. Error analysis, the "errors caught by evidence" experiment, literature review, reword the research question.

## 8. Decisions

Decided:
- **Extension scope for now: side panel with live highlighted text or typed text; automatic page scan later (Phase 2 of the docx)** (2026-10-05).
- **Development purpose: build the complete working system and pipeline first; model and data quality come after** (2026-10-05).
- **Option A: model-centered thesis** (2026-10-05).
- **Show the model's prediction even when evidence is insufficient** (2026-10-05); implemented in code, tests, extension, and docx section 6 on 2026-10-06.
- **No adviser approval step:** all decisions and docx changes made in this project are treated as approved (2026-10-06).

Still open:
1. Definition of the accuracy target (87% of what, on which test set, with which metrics).
2. Dataset source for the real classifier (public claim-level dataset vs own curation vs a mix) and labeling guidelines.
3. Acceptance-gate numbers.
4. Whether the translation stage is built or only tested as an experiment.
5. Which topics and sources the evidence repository covers, and who reviews it.
6. Whether to commit the current work to git.
