from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from schemas import RegisterRequest, LoginRequest, TokenResponse, UserOut
import models
from auth import hash_password, verify_password, create_access_token

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user and return an access token immediately."""
    try:
        # Validate password strength
        payload.validate_password()

        # Check duplicate email
        existing = db.query(models.User).filter(models.User.email == payload.email).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")

        # Create user
        user = models.User(
            name=payload.name,
            email=payload.email,
            hashed_password=hash_password(payload.password),
            language=payload.language or "en",
            age=payload.age,
            city=payload.city,
            profession=payload.profession,
            experience_level=payload.experience_level,
            business_interest=payload.business_interest,
            income=payload.income,
            birthdate=payload.birthdate,
            state=payload.state,
            country=payload.country,
            mobile_number=payload.mobile_number,
            gender=payload.gender,
            usage_purpose=payload.usage_purpose,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Create default settings
        settings = models.UserSettings(user_id=user.id)
        db.add(settings)
        db.commit()

        # Issue token
        token = create_access_token({"sub": str(user.id)})
        return TokenResponse(
            access_token=token,
            user_id=user.id,
            name=user.name,
            email=user.email
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """Login and return a JWT access token."""
    try:
        user = db.query(models.User).filter(models.User.email == payload.email).first()
        if not user or not verify_password(payload.password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid email or password")

        if not user.is_active:
            raise HTTPException(status_code=403, detail="Account is deactivated")

        token = create_access_token({"sub": str(user.id)})
        return TokenResponse(
            access_token=token,
            user_id=user.id,
            name=user.name,
            email=user.email
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")


# Note: GET /me endpoint is defined in main.py with proper auth protection
