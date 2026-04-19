from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from auth import get_current_user, verify_password
from schemas import SettingsUpdate, SettingsOut
import models

router = APIRouter()


@router.get("/", response_model=SettingsOut)
def get_settings(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Get current user's settings."""
    settings = db.query(models.UserSettings).filter(
        models.UserSettings.user_id == current_user.id
    ).first()

    if not settings:
        # Create default settings if missing
        settings = models.UserSettings(user_id=current_user.id)
        db.add(settings)
        db.commit()
        db.refresh(settings)

    return settings


@router.put("/", response_model=SettingsOut)
def update_settings(
    payload: SettingsUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Update user preferences and profile."""
    # Verify current password before making any changes
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect current password")

    settings = db.query(models.UserSettings).filter(
        models.UserSettings.user_id == current_user.id
    ).first()

    if not settings:
        settings = models.UserSettings(user_id=current_user.id)
        db.add(settings)

    settings.language        = payload.language
    settings.voice_input     = payload.voice_input
    settings.voice_output    = payload.voice_output
    settings.ai_detail_level = payload.ai_detail_level
    settings.notifications   = payload.notifications

    # Update user profile
    current_user.language         = payload.language
    if payload.name is not None: current_user.name = payload.name
    if payload.age is not None: current_user.age = payload.age
    if payload.city is not None: current_user.city = payload.city
    if payload.profession is not None: current_user.profession = payload.profession
    if payload.experience_level is not None: current_user.experience_level = payload.experience_level
    if payload.business_interest is not None: current_user.business_interest = payload.business_interest
    if payload.income is not None: current_user.income = payload.income
    if payload.birthdate is not None: current_user.birthdate = payload.birthdate
    if payload.state is not None: current_user.state = payload.state
    if payload.country is not None: current_user.country = payload.country
    if payload.mobile_number is not None: current_user.mobile_number = payload.mobile_number
    if payload.gender is not None: current_user.gender = payload.gender
    if payload.usage_purpose is not None: current_user.usage_purpose = payload.usage_purpose

    db.commit()
    db.refresh(settings)
    return settings
