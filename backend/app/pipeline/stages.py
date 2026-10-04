"""Pipeline stages (thesis section 3). Not implemented yet.

Each stage raises NotImplementedError until its component exists. Keep the signatures stable:
the Phase 2 automatic mode reuses the same stages per claim.
"""
from ..schemas import EvidenceItem, EvidenceLabel, MLLabel


def is_health_related(text: str) -> bool:
    raise NotImplementedError("health-domain detection")


def has_verifiable_claim(text: str) -> bool:
    raise NotImplementedError("verifiable-claim detection")


def extract_claim(text: str) -> str:
    raise NotImplementedError("claim extraction")


def classify(claim: str) -> tuple[MLLabel, float, str]:
    """Return (label, confidence, model_version)."""
    raise NotImplementedError("ML classification")


def retrieve_evidence(claim: str) -> list[EvidenceItem]:
    """Search validated evidence only (view `validated_evidence`)."""
    raise NotImplementedError("evidence retrieval")


def verify(claim: str, evidence: list[EvidenceItem]) -> EvidenceLabel:
    """No relevant evidence must return INSUFFICIENT, never a fake verdict."""
    raise NotImplementedError("evidence verification")
