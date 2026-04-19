from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from collections import Counter

from database import get_db
from auth import get_current_user
from schemas import DashboardStats, IdeaOut
import models

router = APIRouter()


@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Return dashboard statistics for the current user."""
    ideas = (
        db.query(models.Idea)
        .filter(models.Idea.user_id == current_user.id)
        .order_by(models.Idea.created_at.desc())
        .all()
    )

    total    = len(ideas)
    analyzed = sum(1 for i in ideas if i.status == "analyzed")
    pending  = total - analyzed
    recent   = ideas[:5]  # last 5 ideas

    # Category distribution
    categories = [i.category or "Uncategorized" for i in ideas]
    distribution = dict(Counter(categories))

    return DashboardStats(
        total_ideas=total,
        analyzed_ideas=analyzed,
        pending_ideas=pending,
        recent_ideas=recent,
        category_distribution=distribution,
    )
