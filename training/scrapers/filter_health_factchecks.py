import os
import pandas as pd

INPUT_PATH = os.path.join(os.path.dirname(__file__), "factcheck_dataset.csv")
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "factcheck_dataset_health_myths_only.csv")

# Strong medical myth / public-health misinformation markers.
# These are intentionally narrower than generic health mentions so we keep
# only articles dealing with fake remedies, vaccines, medical scams, or health
# disinformation instead of general politics that mention health in passing.
STRONG_MYTH_MARKERS = [
    "miracle cure", "miraculous cure", "cure-all", "cure all", "guaranteed cure",
    "guaranteed result", "walang side effects", "no side effects", "instant cure",
    "natural cure", "herbal cure", "unproven medicine", "kapalit ng gamot",
    "replace medicine", "works for everything", "treats all diseases",
    "doctor don't want you to know", "hindi alam ng doktor", "secret ingredient",
    "hidden cure", "breakthrough", "medical scam", "health scam", "fake vaccine",
    "anti-vaccine", "vaccine scam", "bakuna scam", "booster scam", "covid vaccine hoax",
    "detox", "toxin cleanse", "traditional healer", "albularyo", "hilot cure",
    "medicine hoax", "fake treatment", "fake medical advice", "health hoax",
    "medication myth", "miracle drug", "covid cure", "flu cure", "pandemic hoax",
    "public health hoax", "public health misinformation", "medical misinformation"
]

HEALTH_CONTEXT_WORDS = [
    "vaccine", "bakuna", "covid", "virus", "flu", "booster", "medicine", "gamot",
    "doctor", "doktor", "hospital", "ospital", "clinic", "health", "medical",
    "patient", "pasyente", "treatment", "therapy", "disease", "sakit", "cure",
    "lunas", "remedy", "herbal", "natural remedy", "symptom", "disease hoax",
    "public health", "health official", "health department", "pharmacy", "nurse",
    "wellness", "immunization", "disinfectant", "mask", "covid-19", "antivax",
    "anti-vax", "treatment claim"
]


def safe_text(value):
    return str(value or "").lower()


def is_health_myth_post(title: str, text: str) -> bool:
    combined = safe_text(title) + " " + safe_text(text)
    if not combined.strip():
        return False

    # Require at least one strong myth marker OR one public-health misinformation clue
    # plus at least one health-context word.
    has_strong_marker = any(marker in combined for marker in STRONG_MYTH_MARKERS)
    has_health_context = any(word in combined for word in HEALTH_CONTEXT_WORDS)

    # Additional patterns that are clearly health misinformation even without a classic
    # myth marker, such as fake vaccines or bogus public health assistance claims.
    has_health_claim_pattern = any(pat in combined for pat in [
        "fake vaccine", "vaccine scam", "bakuna scam", "booster hoax",
        "covid cure", "covid hoax", "health aid scam", "medical assistance scam",
        "unverified medical", "fake treatment", "false medical claim",
        "public health scam", "health misinformation"
    ])

    # This stricter filter keeps only actual health-myth/public-health misinformation
    # articles, not general political posts that merely mention health.
    return (has_strong_marker and has_health_context) or (has_health_claim_pattern and has_health_context)


def main():
    df = pd.read_csv(INPUT_PATH)
    if df.empty:
        print("No rows found in the scraped fact-check dataset.")
        return

    filtered = df[
        df[["title", "text"]].fillna("").apply(
            lambda row: is_health_myth_post(str(row["title"]), str(row["text"])),
            axis=1,
        )
    ].copy()

    filtered = pd.DataFrame(filtered[["source", "url", "title", "text", "label"]])
    filtered.to_csv(OUTPUT_PATH, index=False)

    print(f"Original rows: {len(df)}")
    print(f"Health-myth / public-health misinformation rows: {len(filtered)}")
    print(f"Saved filtered dataset to: {OUTPUT_PATH}")

    if not filtered.empty:
        print("Sample rows:")
        print(filtered.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
