"""Rule-based text checks for the first pipeline stages (thesis section 3, steps 2-4).

Deliberately simple and transparent: whole-word health terms (English + Tagalog) and surface patterns
for questions and subjective statements. These are placeholders for a trained detector (OPEN in
TECH_STACK.md); they will misjudge unusual phrasing, so treat the results as a first filter only.
"""
import re

_HEALTH_PATTERNS = [
    # general
    r"health\w*", r"medic\w*", r"disease\w*", r"illness\w*", r"sick\w*", r"symptom\w*", r"infect\w*",
    r"virus\w*", r"bacteri\w*", r"cure\w*", r"cured", r"treat\w*", r"therap\w*", r"remed\w*", r"heal\w*",
    r"doctor\w*", r"hospital\w*", r"patient\w*", r"nurse\w*", r"surgery", r"drug\w*", r"antibiotic\w*",
    r"vaccin\w*", r"immun\w*", r"covid\w*", r"coronavirus", r"flu", r"fever", r"cough\w*", r"cold",
    r"pneumonia", r"cancer\w*", r"tumou?r\w*", r"diabet\w*", r"insulin", r"hypertension", r"blood",
    r"heart\w*", r"cardio\w*", r"stroke", r"kidney\w*", r"liver", r"lung\w*", r"brain", r"mental",
    r"depress\w*", r"anxiety", r"diet\w*", r"nutrition\w*", r"vitamin\w*", r"supplement\w*", r"herbal",
    r"obes\w*", r"exercis\w*", r"smok\w*", r"tobacco", r"alcohol", r"pregnan\w*", r"autis\w*",
    r"measles", r"dengue", r"tuberculosis", r"tb", r"malaria", r"hiv", r"aids", r"asthma", r"allerg\w*",
    r"pain\w*", r"headache\w*", r"tired", r"fatigue", r"toxin\w*", r"antibod\w*", r"infection\w*",
    r"hygiene", r"wash\w* (?:your |their |the )?hands?", r"mask\w*", r"quarantin\w*", r"outbreak\w*",
    r"epidemic", r"pandemic", r"calories?", r"cholesterol", r"bleach",
    # Tagalog
    r"gamot", r"sakit", r"lunas", r"gumaling", r"magaling", r"galing", r"bakuna", r"pagbabakuna",
    r"lagnat", r"ubo", r"sipon", r"kanser", r"tigdas", r"dengue", r"doktor", r"ospital", r"pasyente",
    r"kalusugan", r"malusog", r"masakit", r"hilot", r"albularyo", r"herbal", r"bitamina", r"bawang",
    r"kamay", r"impeksyon", r"impeksiyon", r"sugat", r"dugo", r"puso", r"baga", r"bato", r"diabetes",
]
_HEALTH_RE = re.compile(r"\b(?:" + "|".join(_HEALTH_PATTERNS) + r")\b", re.IGNORECASE)

_QUESTION_START = re.compile(
    r"^\s*(?:what|why|how|when|where|who|which|should|is|are|am|was|were|can|could|do|does|did|will|would|"
    r"may|might|shall|ano|bakit|paano|saan|kailan|sino|alin|dapat ba|pwede ba|puwede ba|maaari ba)\b",
    re.IGNORECASE,
)
_SUBJECTIVE_START = re.compile(
    r"^\s*(?:i|we)\s+(?:really\s+)?(?:think|feel|felt|believe|hope|wish|guess|love|hate|am|was|'m)\b"
    r"|^\s*(?:i'm|i've been)\b|^\s*(?:sana|parang|feeling|gusto ko|sa tingin ko|palagay ko|pakiramdam ko)\b",
    re.IGNORECASE,
)
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")
MIN_CLAIM_WORDS = 3


def is_health_text(text: str) -> bool:
    return bool(_HEALTH_RE.search(text))


def is_question(sentence: str) -> bool:
    s = sentence.strip()
    return s.endswith("?") or bool(_QUESTION_START.match(s)) or bool(re.search(r"\bba\s*[?.!]*$", s, re.I))


def is_subjective(sentence: str) -> bool:
    return bool(_SUBJECTIVE_START.match(sentence))


def sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENTENCE_SPLIT.split(" ".join(text.split())) if s.strip()]


def is_claim_like(sentence: str) -> bool:
    """A health sentence that asserts something checkable: not a question, not a personal feeling/wish."""
    return (
        len(sentence.split()) >= MIN_CLAIM_WORDS
        and is_health_text(sentence)
        and not is_question(sentence)
        and not is_subjective(sentence)
    )
