# Dataset Candidates

Status: **PUBHEALTH and HealthVer downloaded to `data/raw/` on 2026-10-05** (not cleaned or used yet). The others are candidates only. Details were read from the dataset pages; licenses must be re-checked in each repository and paper before the thesis cites them. `data/raw/*` is git-ignored.

## What the system needs

| Need | Format | Used by |
|---|---|---|
| Classifier training | `text` (claim), `label` (`Reliable` / `Misinformation`) | `training/run.py` (thesis 13) |
| Evidence verification | claim + evidence passage + `Supported` / `Contradicted` / `Insufficient Evidence` | NLI verifier (thesis 5, TECH_STACK.md) |
| Evidence repository | passages with source name, URL, date | `evidence` table (thesis 5, 8) |
| Tagalog / Taglish test | short claims with labels, hand-checked | accuracy on Tagalog (TECH_STACK.md) |

## Downloaded (verified from the files)

| Dataset | Location | Verified contents |
|---|---|---|
| PUBHEALTH | `data/raw/pubhealth/pubhealth_{train,validation,test}.parquet` (39 MB), plus HF `README.md` and `health_fact.py` | 9,832 / 1,225 / 1,235 rows = **12,292**. Columns: claim_id, claim, date_published, explanation, fact_checkers, main_text, sources, label, subjects. Label ids: 0 false (3,769), 1 mixture (1,799), 2 true (6,306), 3 unproven (377), **-1 unlabeled (41)**. 13 duplicate claims, 16 claims under 15 characters. License in dataset card: MIT. |
| HealthVer | `data/raw/healthver/healthver_{train,dev,test}.csv` (5.6 MB) | 10,590 / 1,917 / 1,823 rows = **14,330** pairs. Columns: id, evidence, claim, label, topic_ip, question. Labels: Neutral 6,117, Supports 4,986, Refutes 3,227. Only **1,855 unique claims** (each claim repeats with different evidence). **No license file in the repository** (GitHub license API returns 404). |

Provenance: the PUBHEALTH parquet files come from Hugging Face's automatic conversion (`refs/convert/parquet`) of the `ImperialCollegeLondon/health_fact` loading script, not from the original authors' files. HealthVer comes from `raw.githubusercontent.com/sarrouti/HealthVer/master/data/`.

## Candidates

| Dataset | Content | Language | License | Fits |
|---|---|---|---|---|
| [PUBHEALTH (`ImperialCollegeLondon/health_fact`)](https://huggingface.co/datasets/ImperialCollegeLondon/health_fact) **(downloaded)** | 12,292 rows (train 9,832 / validation 1,225 / test 1,235). Columns: claim, explanation, label, authors, date published, tags, main_text, evidence sources. Labels: `true`, `false`, `unproven`, `mixture` | English | MIT (dataset card) | Classifier training. Evidence candidates from `explanation` and `main_text`. |
| [HealthVer](https://github.com/sarrouti/HealthVer) **(downloaded)** | 14,330 claim-evidence pairs. Labels: Support, Refute, Neutral | English | None in repo | Evidence verification (maps to Supported / Contradicted / Insufficient Evidence). |
| [CoAID](https://github.com/cuilimeng/CoAID) | 5,216 news articles, 958 social posts, 296,752 engagements, about COVID-19, with ground-truth labels | English (likely) | Not stated; cite [Cui & Lee 2020](https://arxiv.org/pdf/2006.00885) | Extra training data; COVID only; articles and posts, not claims. |
| [Fake News Filipino (`jcblaise/fake_news_filipino`)](https://huggingface.co/datasets/jcblaise/fake_news_filipino) | 3,206 news articles, 1,603 real / 1,603 fake. Columns: label, article | Filipino (some English) | **Unknown** ("More Information Needed") | Filipino language practice only. **Not health content.** |
| [FakeHealth](https://arxiv.org/pdf/2211.05289) | Fake health news with expert-generated reviews | English | Access must be requested | Possible; access barrier. |
| [MultiClaim](https://huggingface.co/papers/2305.07991) | Multilingual previously fact-checked claim retrieval | Multilingual | Not checked | Possible for retrieval experiments. Details not read. |
| [MM-COVID](https://arxiv.org/pdf/2105.03313) | 3,981 fake and 7,192 true news items, verified by Snopes and Poynter | English, Spanish, Portuguese, Hindi, French, Italian | Not checked | No Tagalog. Low priority. |

## Gaps

- **No Tagalog or Taglish health-misinformation dataset was found.** Tagalog must be collected (VERA Files, DOH, via `training/scrapers/`) and a small test set labeled by hand.
- **Every health dataset above is English.** English-only training will not show how the system behaves on Tagalog.

## Decisions needed before use

1. **PUBHEALTH label mapping.** `true` to `Reliable` and `false` to `Misinformation` is clear. `unproven` and `mixture` have no match. Proposed: drop them in the first version.
2. **License check.** PUBHEALTH text comes from fact-checking sites, which may hold their own rights. Read the paper and repository terms. HealthVer and CoAID state no license.
3. **Text-type mismatch.** Claims (PUBHEALTH) are the right unit. Articles and posts (CoAID, Fake News Filipino) risk the model learning text style instead of truthfulness, as happened with the seed data (short claims vs long articles).
4. **Counts.** The PUBHEALTH paper reports about 11.8K claims; the downloaded files hold 12,292 rows (the HF page says 12,288). Likely unfiltered rows; decide whether to use the paper's filtering.
5. **PUBHEALTH `claim` is often a news headline, not a verifiable claim.** Examples labeled `true`: "Angioplasty through the wrist backed by new study". Examples labeled `false`: "Poor test results for heart drugs". The label describes the *story's* veracity, so it does not match the system's definition of a verifiable factual claim (thesis section 3). Needs a filter or manual review before it trains a claim-level classifier.
6. **PUBHEALTH `-1` labels** (41 rows) must be dropped.
7. **HealthVer repeats claims** (1,855 unique in 14,330 rows). Split by claim, never by row, or the same claim will land in train and test.
8. **HealthVer has no license.** Contact the authors or limit use to research with citation, and say so in the thesis.

## Proposed order

1. ~~Download PUBHEALTH and HealthVer into `data/raw/`~~ (done).
2. Clean with `training/prepare/clean.py`; train with `training/run.py` to prove the pipeline end to end on English.
3. Build the Tagalog test set from VERA Files and DOH sources.

## Disk note

After the user freed space, C: had about 65 GB free (87% used) on 2026-10-05. Hugging Face model downloads can be moved with the `HF_HOME` environment variable.

## PUBHEALTH conversion result (2026-10-05)

Script: `training/prepare/convert_pubhealth.py` (true -> Reliable, false -> Misinformation; drops mixture, unproven, -1; requires a fact checker; keeps health-tagged subjects only).

| Step | Rows |
|---|---|
| Raw | 12,292 |
| true/false only | 10,075 |
| has fact checker | 7,674 |
| health subject tag | 4,049 (2,723 Reliable / 1,326 Misinformation) |
| after `clean.py` (duplicates) | 4,047 -> `data/training/pubhealth_v1.csv` |

First training run (`v0.1-pubhealth`, SVM selected on validation): test accuracy 0.789, macro-F1 0.772, Misinformation precision 0.646. It **failed the placeholder gate** (macro-F1 0.80), so nothing was packaged.

**Do not trust these scores yet.** Even after filtering, Reliable rows are still mostly news headlines (median 10 words, trailing period) and Misinformation rows are viral claims (median 15 words), so the model partly learns text style. The `language` tag also mislabels 63 English rows as `tl` (heuristic). Next: review a sample by hand and consider a style-neutral test set.
