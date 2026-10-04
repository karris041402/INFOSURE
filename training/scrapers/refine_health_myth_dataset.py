import csv
import os
import re

INPUT_PATH = os.path.join(os.path.dirname(__file__), "health_myth_factchecks.csv")
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "health_myth_training_dataset.csv")

BLACKLIST_PATTERNS = [
    "global health fellows",
    "fact checkers say collaboration",
    "health misinformation around the world",
    "combat health misinformation",
    "misinfodemic",
    "public health experts",
    "debate over ivermectin",
    "time of crisis",
    "health fellowship",
    "fact-checking organizations",
    "press review for kids",
    "collaboration important",
]

MYTH_PATTERNS = [
    "miracle drug",
    "miracle cure",
    "cure for eye",
    "fake cure",
    "fake vaccine",
    "vaccine-related deaths",
    "health scam",
    "medical scam",
    "cancer-killers",
    "dengue cure",
    "cure vs high cholesterol",
    "cure for hypertension",
    "blood pressure",
    "cholesterol",
    "hypertension",
    "ivermectin",
    "remdesivir",
    "papaya leaf juice",
    "cannabis is a cancer cure",
    "cure for",
    "treats all diseases",
    "works for everything",
    "cure against",
    "fake remedy",
    "natural cure",
    "heal",
    "instant cure",
]

HEALTH_CONTEXT = [
    "vaccine",
    "covid",
    "medicine",
    "drug",
    "cure",
    "health",
    "cholesterol",
    "hypertension",
    "dengue",
    "cancer",
    "blood",
    "doctor",
    "medical",
    "treatment",
    "immunization",
    "eye",
    "public health",
    "patient",
    "symptom",
    "disease",
    "therapy",
]


def clean_text(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def text_has_blacklist(text):
    lowered = text.lower()
    return any(p in lowered for p in BLACKLIST_PATTERNS)


def is_relevant(title, body):
    combo = (title or "") + " " + (body or "")
    combo = clean_text(combo).lower()
    if not combo:
        return False
    if text_has_blacklist(combo):
        return False

    has_myth = any(p in combo for p in MYTH_PATTERNS)
    has_health = any(p in combo for p in HEALTH_CONTEXT)
    if not has_myth or not has_health:
        return False

    # Exclude generic explainer pieces about health misinformation without an actual myth claim.
    if "fact-checkers say collaboration" in combo:
        return False
    if "global health fellows" in combo:
        return False
    if "combat health misinformation" in combo:
        return False
    if "health misinformation around the world" in combo:
        return False
    if "debate over ivermectin" in combo:
        return False

    return True


def main():
    rows = []
    seen_urls = set()

    with open(INPUT_PATH, "r", encoding="utf-8", newline="") as infile:
        reader = csv.DictReader(infile)
        for row in reader:
            url = (row.get("url") or "").strip()
            title = clean_text(row.get("title"))
            text = clean_text(row.get("text"))
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)
            if is_relevant(title, text):
                rows.append({
                    "source": row.get("source", "").strip(),
                    "url": url,
                    "title": title,
                    "text": text,
                    "label": "health_myth",
                })

    with open(OUTPUT_PATH, "w", encoding="utf-8", newline="") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=["source", "url", "title", "text", "label"])
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    print(f"Original unique URLs: {len(seen_urls)}")
    print(f"Clean health-myth records kept: {len(rows)}")
    print(f"Saved filtered dataset to: {OUTPUT_PATH}")

    if rows:
        for row in rows:
            print("-", row["title"])


if __name__ == "__main__":
    main()
