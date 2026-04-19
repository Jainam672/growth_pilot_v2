from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from auth import get_current_user
from schemas import IdeaCreate, IdeaOut
import models

router = APIRouter()


@router.post("/", response_model=IdeaOut, status_code=201)
def create_idea(
    payload: IdeaCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Submit a new business idea."""
    idea = models.Idea(
        user_id=current_user.id,
        title=payload.title,
        description=payload.description,
        budget=str(payload.budget) if payload.budget is not None else None,
        location=payload.location,
        category=payload.category,
        experience_level=payload.experience_level,
    )
    db.add(idea)
    db.commit()
    db.refresh(idea)
    return idea


@router.get("/", response_model=List[IdeaOut])
def list_ideas(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List all ideas belonging to the current user."""
    return (
        db.query(models.Idea)
        .filter(models.Idea.user_id == current_user.id)
        .order_by(models.Idea.created_at.desc())
        .all()
    )


@router.get("/{idea_id}", response_model=IdeaOut)
def get_idea(
    idea_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get a single idea by ID (must belong to current user)."""
    idea = db.query(models.Idea).filter(
        models.Idea.id == idea_id,
        models.Idea.user_id == current_user.id
    ).first()
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")
    return idea


@router.delete("/{idea_id}", status_code=204)
def delete_idea(
    idea_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Delete an idea and its AI response."""
    idea = db.query(models.Idea).filter(
        models.Idea.id == idea_id,
        models.Idea.user_id == current_user.id
    ).first()
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")
    db.delete(idea)
    db.commit()
