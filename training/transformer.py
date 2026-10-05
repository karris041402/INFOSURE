"""Transformer candidate (thesis section 13.5): xlm-roberta-base fine-tuning. NOT IMPLEMENTED.

Settings live in configs/default.json under "transformer", sized for a 4 GB GPU (RTX 2050):
fp16, batch size 8, max length 128, gradient accumulation 4. Lower the batch size on out-of-memory.

Required before implementing: install the CUDA build of torch plus `transformers`, and confirm
`torch.cuda.is_available()` is True. The tokenizer must be saved with the model (section 13.8), and
text must keep natural sentence structure (no stopword removal; negation matters, section 13.4).
"""
import pandas as pd


def train_transformer(train_df: pd.DataFrame, val_df: pd.DataFrame, cfg: dict):
    try:
        import torch  # noqa: F401
        import transformers  # noqa: F401
    except ImportError as exc:
        raise RuntimeError(
            "Transformer stage needs torch and transformers (CUDA build of torch for the GPU)."
        ) from exc
    raise NotImplementedError("xlm-roberta-base fine-tuning")
