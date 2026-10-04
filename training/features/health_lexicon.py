# Filipino Health Misinformation Lexicon & Detection Features

# Filipino/Tagalog Health-Related Terms
HEALTH_KEYWORDS_TAGALOG = {
    'lunas': 'cure',
    'gamot': 'medicine',
    'sakit': 'disease/pain',
    'bakuna': 'vaccine',
    'virus': 'virus',
    'bawas': 'reduce',
    'palusog': 'health',
    'pasyente': 'patient',
    'doktor': 'doctor',
    'ospital': 'hospital',
    'herbal': 'herbal',
    'natural': 'natural',
    'pangasiwa': 'care',
    'uminom': 'drink/take',
    'hilot': 'massage therapy',
    'albularyo': 'faith healer',
    'amulet': 'amulet',
    'manghihilot': 'traditional healer',
    'lamig': 'cold/chill',
    'init': 'heat',
    'lagnat': 'fever',
    'ubo': 'cough',
    'sipon': 'cold',
}

# WARNING SIGNALS FOR MISINFORMATION
SENSATIONALISM_WORDS = [
    'miracle', 'miraculous', 'miraculo',
    'cure-all', 'wonder drug', 'breakthrough',
    'hidden', 'suppressed', 'secret', 'sikreto',
    'exposed', 'shocking', 'shocking revelation',
    'government conspiracy', 'coverup', 'cover-up',
    'doctors don\'t want you to know', 'hindi gusto ng doctors',
    'only one ingredient', 'isang sangkap lang',
    'instant', 'overnight', 'overnight cure',
    'guaranteed', 'garantisado', 'walang katangian',
]

URGENCY_WORDS = [
    'urgent', 'urgenpe', 'mabilis', 'quickly',
    'before it\'s too late', 'bago mahuling huli',
    'limited time', 'limited time offer',
    'act now', 'kumilos na ngayon',
    'don\'t delay', 'huwag pabagalin',
    'rush', 'bilisan',
]

CREDIBILITY_KEYWORDS_POSITIVE = [
    'study', 'research', 'clinical trial', 'peer-reviewed',
    'doctor', 'physician', 'medical professional',
    'hospital', 'clinic', 'health department',
    'FDA', 'WHO', 'DOH', 'department of health',
    'published', 'verified', 'confirmed',
    'evidence-based', 'scientific', 'scientifically proven',
]

CREDIBILITY_KEYWORDS_NEGATIVE = [
    'rumor', 'rumour', 'allegedly', 'supposedly',
    'unverified', 'unconfirmed', 'claim',
    'anonymous sources', 'insider says',
    'believe', 'think', 'seem to',
    'conspiracy', 'conspiracy theory',
    'natural remedy', 'folk remedy', 'traditional',
    'testimonial', 'personal experience', 'karanasan ko lang',
]

# Common Filipino Folk Health Beliefs (potential misinformation)
FOLK_HEALTH_CLAIMS = {
    'hilot': 'bone setting massage - often unregulated',
    'albularyo': 'faith healer - not evidence-based',
    'lamig': 'traditional concept of body heat imbalance',
    'init': 'body heat/fire - traditional belief',
    'pasma': 'sudden cold exposure illness - culturally believed but not medically recognized',
    'taba ng puso': 'fat from heart - traditional belief unproven',
    'usog': 'evil eye/bad luck illness',
}

# Credible Filipino Health Sources
CREDIBLE_SOURCES = [
    'Department of Health',
    'DOH',
    'Philippine Health Insurance Corporation',
    'PhilHealth',
    'UP College of Medicine',
    'Philippine General Hospital',
    'National Institutes of Health',
    'RITM',  # Research Institute for Tropical Medicine
    'FDA',
    'WHO',
    'CDC',
]

# Medical Claims to Verify
HIGH_RISK_CLAIMS = [
    'cure', 'curato', 'lunas',
    'prevent all', 'prevent lahat',
    'guaranteed', 'garantisado',
    'replace', 'replace medicine', 'kapalit ng gamot',
    'works for everything', 'effective sa lahat',
    'no side effects', 'walang side effects',
]

def calculate_sensationalism_score(text):
    """Calculate sensationalism score (0-1)"""
    text_lower = text.lower()
    score = 0
    total_words = len(text.split())
    
    for word in SENSATIONALISM_WORDS:
        score += text_lower.count(word)
    
    for word in URGENCY_WORDS:
        score += text_lower.count(word) * 1.5  # Urgency words weighted higher
    
    return min(score / max(total_words, 1) * 10, 1.0)

def calculate_credibility_score(text):
    """Calculate credibility score based on sources mentioned (0-1)"""
    text_lower = text.lower()
    credible_count = 0
    non_credible_count = 0
    
    for keyword in CREDIBILITY_KEYWORDS_POSITIVE:
        credible_count += text_lower.count(keyword.lower())
    
    for keyword in CREDIBILITY_KEYWORDS_NEGATIVE:
        non_credible_count += text_lower.count(keyword.lower())
    
    # Net credibility
    net = credible_count - non_credible_count
    return max(min((net + 5) / 10, 1.0), 0.0)

def detect_health_keywords(text):
    """Detect if text contains health-related content"""
    text_lower = text.lower()
    health_count = 0
    
    for _, keyword in HEALTH_KEYWORDS_TAGALOG.items():
        health_count += text_lower.count(keyword.lower())
    
    for keyword in CREDIBILITY_KEYWORDS_POSITIVE + CREDIBILITY_KEYWORDS_NEGATIVE + HIGH_RISK_CLAIMS:
        if keyword.lower() in text_lower:
            health_count += 1
    
    return health_count > 0

def extract_health_features(text):
    """Extract interpretable features for health misinformation detection"""
    features = {
        'sensationalism_score': calculate_sensationalism_score(text),
        'credibility_score': calculate_credibility_score(text),
        'contains_urgent_language': any(word in text.lower() for word in URGENCY_WORDS),
        'contains_folk_remedies': any(remedy in text.lower() for remedy in FOLK_HEALTH_CLAIMS.keys()),
        'lacks_credible_sources': sum(1 for src in CREDIBLE_SOURCES if src.lower() in text.lower()) == 0,
        'high_risk_claim_detected': any(claim in text.lower() for claim in HIGH_RISK_CLAIMS),
    }
    return features
