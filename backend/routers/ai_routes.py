import json
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from database import get_db
from auth import get_current_user
from schemas import AnalyzeRequest, AIResponseOut, FullIdeaWithResponse
import models

router = APIRouter()


def _run_analysis(idea_id: int, db: Session):
    """Core analysis logic — called directly or via background task."""
    idea = db.query(models.Idea).filter(models.Idea.id == idea_id).first()
    if not idea:
        return None

    from ai_engine.rag_pipeline import analyze_idea

    result = analyze_idea(
        idea_title=idea.title,
        idea_description=idea.description,
        budget=idea.budget,
        location=idea.location,
        category=idea.category,
        experience_level=idea.experience_level,
    )

    # Save or update AI response in DB
    existing = db.query(models.AIResponse).filter(
        models.AIResponse.idea_id == idea_id
    ).first()

    def to_json(val):
        return json.dumps(val) if isinstance(val, list) else val

    if existing:
        existing.feasibility    = result.get("feasibility")
        existing.cost_breakdown = result.get("cost_breakdown")
        existing.roadmap        = to_json(result.get("roadmap"))
        existing.marketing      = to_json(result.get("marketing"))
        existing.risks          = to_json(result.get("risks"))
        existing.competitors    = to_json(result.get("competitors"))
        existing.funding        = to_json(result.get("funding"))
        existing.idea_score     = result.get("idea_score")
        existing.stage          = result.get("stage")
    else:
        ai_resp = models.AIResponse(
            idea_id=idea_id,
            feasibility=result.get("feasibility"),
            cost_breakdown=result.get("cost_breakdown"),
            roadmap=to_json(result.get("roadmap")),
            marketing=to_json(result.get("marketing")),
            risks=to_json(result.get("risks")),
            competitors=to_json(result.get("competitors")),
            funding=to_json(result.get("funding")),
            idea_score=result.get("idea_score"),
            stage=result.get("stage"),
        )
        db.add(ai_resp)

    idea.status = "analyzed"
    db.commit()
    return result


@router.post("/analyze", response_model=FullIdeaWithResponse)
def analyze(
    payload: AnalyzeRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Analyze a business idea using RAG + Ollama and return structured results."""

    # Verify ownership
    idea = db.query(models.Idea).filter(
        models.Idea.id == payload.idea_id,
        models.Idea.user_id == current_user.id
    ).first()
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")

    _run_analysis(idea.id, db)
    db.refresh(idea)

    # Parse JSON lists for response
    response = idea.response
    if response:
        for field in ["roadmap", "marketing", "risks", "competitors", "funding"]:
            val = getattr(response, field)
            if val and isinstance(val, str):
                try:
                    setattr(response, field, json.loads(val))
                except json.JSONDecodeError:
                    pass

    return FullIdeaWithResponse(idea=idea, response=response)


@router.get("/result/{idea_id}", response_model=FullIdeaWithResponse)
def get_result(
    idea_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Fetch existing AI analysis result for an idea."""
    idea = db.query(models.Idea).filter(
        models.Idea.id == idea_id,
        models.Idea.user_id == current_user.id
    ).first()
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")

    response = idea.response
    if response:
        for field in ["roadmap", "marketing", "risks", "competitors", "funding"]:
            val = getattr(response, field)
            if val and isinstance(val, str):
                try:
                    setattr(response, field, json.loads(val))
                except json.JSONDecodeError:
                    pass

    return FullIdeaWithResponse(idea=idea, response=response)
