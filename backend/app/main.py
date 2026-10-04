import sqlite3
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException

from . import db
from .pipeline.run import analyze
from .schemas import AnalyzeRequest, AnalyzeResponse, FeedbackRequest, FeedbackResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    yield


app = FastAPI(title="InfoSure API", version="0.1.0", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze_text(req: AnalyzeRequest) -> AnalyzeResponse:
    try:
        return analyze(req.text)
    except NotImplementedError as exc:
        raise HTTPException(status_code=501, detail=f"Not implemented: {exc}")


@app.post("/feedback", response_model=FeedbackResponse, status_code=201)
def submit_feedback(
    req: FeedbackRequest, conn: sqlite3.Connection = Depends(db.get_conn)
) -> FeedbackResponse:
    """Stored as Pending. Never used for training until a human validates it (thesis section 7)."""
    try:
        with conn:
            cur = conn.execute(
                "INSERT INTO feedback (claim_text, model_prediction, model_confidence, "
                "evidence_result, user_feedback, model_version) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    req.claim_text,
                    req.model_prediction.value,
                    req.model_confidence,
                    req.evidence_result.value if req.evidence_result else None,
                    req.user_feedback.value,
                    req.model_version,
                ),
            )
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=422, detail="Unknown model_version")
    return FeedbackResponse(feedback_id=cur.lastrowid, review_status="Pending")
