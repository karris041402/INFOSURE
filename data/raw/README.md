# data/raw

Untouched output of scrapers and downloads. Never edit or clean files here.

- One subfolder or filename prefix per source, e.g. `verafiles_2026-10-04.csv`.
- Record for each batch: source, URL, date collected, license / terms of use.
- Cleaning reads from here and writes versioned results to `data/training/`
  (see `training/prepare/clean.py`).
