# data/eval

Hand-written cases for testing the **pipeline behavior**, not for training or measuring model quality.

`pipeline_smoke_cases.csv`
- `expected_scope`: what the pipeline should do with the text: `verified` (health + verifiable claim, goes through ML and evidence), `no_verifiable_health_claim` (health-related but opinion/question/wish), `out_of_scope` (not health).
- `truth`: common-knowledge truth of `verified` claims (`true`/`false`), for sanity checks only.
- `label_status = author_proposed`: written by the assistant, needs human review before any result is cited. 24 cases, too few for statistics.
- Do not train on these. Keep them out of `data/training/`.
