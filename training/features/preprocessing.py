import re
from typing import Dict, List, Set

import nltk
from nltk.tokenize import wordpunct_tokenize

# -----------------------------------------------------------------------------
# Preprocessing module for Taglish health misinformation detection.
# This stage normalizes noisy social-media text before feature extraction or ML.
# -----------------------------------------------------------------------------

# Ensure the tokenizers are available in the environment.
# This is important because newer NLTK versions sometimes do not ship every
# tokenizer resource by default, especially in lightweight or offline setups.
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    try:
        nltk.download('punkt', quiet=True)
    except Exception:
        pass

try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    try:
        nltk.download('punkt_tab', quiet=True)
    except Exception:
        pass

# Ensure English stopwords are loaded once at module level.
try:
    from nltk.corpus import stopwords
    ENGLISH_STOPWORDS: Set[str] = set(stopwords.words('english'))
except Exception:
    try:
        nltk.download('stopwords', quiet=True)
        from nltk.corpus import stopwords
        ENGLISH_STOPWORDS = set(stopwords.words('english'))
    except Exception:
        ENGLISH_STOPWORDS = set()

# A small Filipino stopword set to supplement NLTK's English list.
# These words are common in Taglish posts but do not add useful signal for
# misinformation detection and are removed to reduce noise.
FILIPINO_STOPWORDS: Set[str] = {
    'ang', 'ng', 'sa', 'mga', 'ay', 'at', 'na', 'si', 'siya', 'ko', 'mo', 'ni', 'namin',
    'nila', 'ito', 'iyan', 'iyon', 'dahil', 'kasi', 'hindi', 'ba', 'lang', 'lamang',
    'o', 'ka', 'natin', 'kayo', 'sila', 'kami', 'para', 'kung', 'kapag', 'din', 'rin', 'pa',
    'yung', 'yan', 'nang', 'bago', 'ano', 'talaga'
}

TOKEN_NORMALIZATION_MAP: Dict[str, str] = {
    'doktor': 'doctor',
    'doktors': 'doctor',
    'doctors': 'doctor',
    'bakuna': 'vaccine',
    'bakunahan': 'vaccine',
    'gamot': 'medicine',
    'gamotin': 'medicine',
    'lunas': 'cure',
    'luya': 'ginger',
    'tsekw': 'tsek',
}


def preprocess_text(text: str) -> List[str]:
    """Lowercase, tokenize, remove punctuation, and strip English/Filipino stopwords.

    This is the first core step in the pipeline. The goal is to convert noisy
    social media text into a cleaner token list that can be used for feature
    extraction and model training.
    """
    if not isinstance(text, str):
        text = str(text)

    # Step 1: lowercase all input to keep consistent token forms.
    text = text.lower()

    # Step 2: remove punctuation and non-alphanumeric characters.
    # This keeps words like 'cancer', 'doctor', and 'vaccine' while stripping
    # emojis, symbols, and other noise that often appear in social posts.
    text = re.sub(r'[^a-z0-9\s]', ' ', text)

    # Step 3: tokenize the cleaned text.
    # We use a lightweight tokenizer because it is more robust than relying on
    # missing NLTK punkt resources in some environments.
    try:
        tokens = wordpunct_tokenize(text)
    except Exception:
        tokens = re.findall(r"[a-z0-9]+", text)

    # Step 4: remove English stopwords using cached NLTK list.
    english_stopwords = ENGLISH_STOPWORDS

    # Step 5: remove Filipino stopwords and short tokens.
    filtered_tokens: List[str] = []
    for raw_token in tokens:
        token = TOKEN_NORMALIZATION_MAP.get(raw_token) or raw_token
        if token in english_stopwords:
            continue
        if token in FILIPINO_STOPWORDS:
            continue
        if len(token) <= 1:
            continue
        filtered_tokens.append(token)

    return filtered_tokens


def __demo__():
    sample = "SHOCKING! Kalamansi at luya, PROVEN cure sa cancer! Hindi alam ng mga doktor ito. SHARE bago pa ito matanggal!"
    print("Raw:", sample)
    print("Cleaned tokens:", preprocess_text(sample))


if __name__ == "__main__":
    __demo__()
