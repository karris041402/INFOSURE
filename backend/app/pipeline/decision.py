"""Decision layer (thesis section 6). Pure logic: no I/O."""
from ..schemas import Assessment, EvidenceLabel, MLLabel


def decide(ml: MLLabel, evidence: EvidenceLabel) -> Assessment:
    if evidence is EvidenceLabel.INSUFFICIENT:
        return Assessment.INSUFFICIENT
    if ml is MLLabel.RELIABLE and evidence is EvidenceLabel.SUPPORTED:
        return Assessment.STRONG_SUPPORT
    if ml is MLLabel.MISINFORMATION and evidence is EvidenceLabel.CONTRADICTED:
        return Assessment.LIKELY_MISINFORMATION
    return Assessment.CONFLICTING
