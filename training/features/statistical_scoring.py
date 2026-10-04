import re
from typing import Any, Dict, List, Tuple


class StatisticalRiskScorer:
    """A self-contained misinformation risk scorer for health claims.

    This module is designed to work alongside a separate ML classifier later.
    It focuses on high-precision, explainable red-flag features that are often
    associated with misinformation in health-related content.
    """

    def __init__(self, weights=None, threshold=6.0):
        # Configurable weights: these can be calibrated later using a labeled dataset.
        self.threshold = threshold
        self.weights = weights or {
            'sensational_language': 3.0,
            'credible_source_absent': 2.5,
            'urgency_pressure': 3.0,
            'all_caps_or_exclamation': 2.0,
            'health_myth_keyword': 4.0,
            'high_risk_health_claim': 4.5,
        }

    def _normalize_text(self, text: str) -> str:
        return (text or '').strip()

    def _count_exclamation_caps(self, text: str) -> Tuple[float, float]:
        total_chars = len(text)
        if total_chars == 0:
            return 0.0, 0.0

        exclamation_count = text.count('!')
        uppercase_count = sum(1 for ch in text if ch.isupper())
        uppercase_ratio = uppercase_count / total_chars
        exclamation_ratio = exclamation_count / total_chars
        return uppercase_ratio, exclamation_ratio

    def _contains_any(self, text: str, keywords: List[str]) -> bool:
        lower_text = text.lower()
        return any(keyword.lower() in lower_text for keyword in keywords)

    def _detect_sensational_language(self, text: str) -> bool:
        sensational_terms = [
            'shock', 'shocking', 'miracle', 'proven', 'guaranteed', 'breakthrough',
            'secret', 'hidden', 'exposed', 'hindi alam ng doktor', 'hindi alam ng mga doktor',
            'walang side effects', 'cure all', 'instant cure', 'miraculous', 'bingi ang doktor',
            'lahat ng sakit', 'diagnosis from facebook', 'may gamot na', 'supernatural healing',
            'magpapagaling ka agad', 'instant healing', 'secret formula', 'viral post'
        ]
        return self._contains_any(text, sensational_terms)

    def _detect_credible_source_absent(self, text: str) -> bool:
        # A credible source may include a health authority, doctor, hospital, WHO, DOH, etc.
        positive_sources = [
            'who', 'doh', 'department of health', 'philhealth', 'fda', 'cdc',
            'doctor', 'physician', 'hospital', 'clinic', 'research', 'study',
            'medical expert', 'health expert', 'nurse', 'specialist', 'world health organization',
            'department of health philippines', 'health authorities', 'doctor says', 'hospital says',
            'expert advice', 'medical board', 'health officials'
        ]
        return not self._contains_any(text, positive_sources)

    def _detect_urgency_pressure(self, text: str) -> bool:
        urgency_terms = [
            'share bago mabura', 'share now', 'share before it is removed', 'ipaalam sa lahat',
            'ibahagi sa lahat', 'act now', 'huwag magpahuli', 'limited time', 'urgent',
            'bago mahuli', 'kumilos na', 'huwag mag-atubiling', 'spread this', 'bili na',
            'limited slots', 'while supplies last', 'do not wait', 'make sure you share this'
        ]
        return self._contains_any(text, urgency_terms)

    def _detect_high_risk_health_claim(self, text: str) -> bool:
        myth_terms = [
            'cure sa cancer', 'cures cancer', 'gabay para sa cancer', 'walang side effects',
            'replace medicine', 'kapalit ng gamot', 'treats all diseases', 'works for everything',
            'cure all', 'guaranteed cure', 'miracle cure', 'natural cure', 'safe for everyone',
            'nakapagpapagaling ng lahat ng sakit', 'nagpapagaling ng lahat', 'pampatanggal ng cancer',
            'mahika na gamot', 'nakakapagligtas sa lahat', 'treats every disease', 'all diseases'
        ]
        return self._contains_any(text, myth_terms)

    def _detect_health_myth_keyword(self, text: str) -> bool:
        myth_keywords = [
            'cure', 'lunas', 'miracle', 'gamot na', 'natural remedy', 'walang side effects',
            'proven', 'guaranteed', 'pangontra sa lahat', 'siguradong', 'pain-free', 'pawis',
            'toxin', 'bawal maligo', 'kulang ka lang sa sugar', 'laway ng aso', 'albularyo', 'hilot',
            'herbal healer', 'detox', 'remove toxins', 'pampabawas ng toxins'
        ]
        return self._contains_any(text, myth_keywords)

    def _detect_all_caps_or_exclamation(self, text: str) -> bool:
        uppercase_ratio, exclamation_ratio = self._count_exclamation_caps(text)
        return uppercase_ratio > 0.20 or exclamation_ratio > 0.05

    def feature_scan(self, text: str) -> Dict[str, bool]:
        """Extract a dictionary of red-flag features from text."""
        cleaned = self._normalize_text(text)
        return {
            'sensational_language': self._detect_sensational_language(cleaned),
            'credible_source_absent': self._detect_credible_source_absent(cleaned),
            'urgency_pressure': self._detect_urgency_pressure(cleaned),
            'all_caps_or_exclamation': self._detect_all_caps_or_exclamation(cleaned),
            'health_myth_keyword': self._detect_health_myth_keyword(cleaned),
            'high_risk_health_claim': self._detect_high_risk_health_claim(cleaned),
        }

    def score_post(self, text: str) -> Dict[str, Any]:
        """Compute a weighted misinformation risk score and explain each trigger.

        Returns:
            {
              'risk_score': float,
              'risk_label': 'High Risk' | 'Low Risk',
              'threshold': float,
              'detected_features': [...],
              'explanation': [...],
            }
        """
        cleaned = self._normalize_text(text)
        if not cleaned:
            return {
                'risk_score': 0.0,
                'risk_label': 'Low Risk',
                'threshold': self.threshold,
                'detected_features': [],
                'explanation': ['No text provided for scoring.'],
            }

        feature_flags = self.feature_scan(cleaned)
        detected = []
        explanations = []

        # The score is the sum of weights for all identified risky features.
        # Each feature has a weight that can be tuned using training data later.
        total_score = 0.0

        for feature_name, detected_flag in feature_flags.items():
            if not detected_flag:
                continue

            detected.append(feature_name)
            weight = self.weights.get(feature_name, 1.0)
            total_score += weight

            label = feature_name.replace('_', ' ').title()
            explanations.append(f"{label}: detected (weight={weight})")

        is_high_risk = total_score > self.threshold
        risk_label = 'High Risk' if is_high_risk else 'Low Risk'

        return {
            'risk_score': round(total_score, 2),
            'risk_label': risk_label,
            'threshold': self.threshold,
            'detected_features': detected,
            'explanation': explanations,
            'details': {
                'raw_features': feature_flags,
                'text_length': len(cleaned)
            },
        }


# Example usage: show the module working end-to-end with a Taglish sample.
if __name__ == '__main__':
    sample_text = (
        "MIRACLE CURE! GUARANTEED! SHARE bago mabura! "
        "HINDI ALAM NG DOKTOR! CURE SA CANCER, walang side effects!"
    )

    scorer = StatisticalRiskScorer(threshold=10.0)
    result = scorer.score_post(sample_text)

    print("Sample text:", sample_text)
    print("Risk score:", result['risk_score'])
    print("Classification:", result['risk_label'])
    print("Detected features:", result['detected_features'])
    print("Explainability:")
    for item in result['explanation']:
        print(" -", item)
