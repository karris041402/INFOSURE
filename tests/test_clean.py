import pandas as pd

from training.prepare.clean import clean, detect_language, normalize_text


def test_language_tags():
    assert detect_language("Lemon water can cure cancer.") == "en"
    assert detect_language("Kapag may lagnat, bawal maligo.") == "tl"
    assert detect_language("Bawang can cure the flu kapag hindi ka na may sipon.") == "mixed"


def test_clean_drops_and_dedupes():
    df = pd.DataFrame({
        "text": ["Lemon water can cure cancer.", "lemon  water can cure cancer!", "short",
                 "Garlic cures all diseases.", "Garlic cures all diseases.", "Vitamin C helps recovery.",
                 "Drinking water is healthy daily."],
        "label": ["Misinformation", "Misinformation", "Misinformation",
                  "Misinformation", "Reliable", "FAKE", "Reliable"],
    })
    out, report = clean(df)
    assert out["text"].tolist() == ["Lemon water can cure cancer.", "Drinking water is healthy daily."]
    assert report["dropped"] == {
        "empty_or_too_short": 1, "invalid_label": 1,
        "conflicting_duplicate_labels": 2, "duplicate": 1,
    }


def test_normalize_text():
    assert normalize_text("  a\n b\t c ") == "a b c"
