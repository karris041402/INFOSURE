from ..schemas import AnalyzeResponse, EvidenceLabel, Scope
from . import stages
from .decision import decide


def analyze(text: str) -> AnalyzeResponse:
    if not stages.is_health_related(text):
        return AnalyzeResponse(
            scope=Scope.OUT_OF_SCOPE,
            message="The selected text is outside the health domain.",
        )
    if not stages.has_verifiable_claim(text):
        return AnalyzeResponse(
            scope=Scope.NO_VERIFIABLE_CLAIM,
            message="No Verifiable Health Claim Detected",
        )

    claim = stages.extract_claim(text)
    ml_label, ml_confidence, model_version = stages.classify(claim)
    evidence = stages.retrieve_evidence(claim)
    evidence_result = stages.verify(claim, evidence) if evidence else EvidenceLabel.INSUFFICIENT

    return AnalyzeResponse(
        scope=Scope.VERIFIED,
        claim=claim,
        ml_label=ml_label,
        ml_confidence=ml_confidence,
        evidence_result=evidence_result,
        assessment=decide(ml_label, evidence_result),
        evidence=evidence,
        model_version=model_version,
    )
