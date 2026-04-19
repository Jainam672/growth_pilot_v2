from pydantic import BaseModel, EmailStr
from typing import Optional, List, Any
from datetime import datetime


# ─────────────────────────────────────────────────────────────
#  AUTH
# ─────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    language: Optional[str] = "en"
    age: Optional[int] = None
    city: Optional[str] = None
    profession: Optional[str] = None
    experience_level: Optional[str] = "beginner"
    business_interest: Optional[str] = None
    income: Optional[str] = None
    birthdate: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    mobile_number: Optional[str] = None
    gender: Optional[str] = None
    usage_purpose: Optional[str] = None
    
    def validate_password(self):
        """Validate password strength."""
        if len(self.password) < 6:
            raise ValueError("Password must be at least 6 characters long")
        return self.password


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    name: str
    email: str


# ─────────────────────────────────────────────────────────────
#  USER
# ─────────────────────────────────────────────────────────────

class UserOut(BaseModel):
    id: int
    name: str
    email: str
    language: str
    age: Optional[int]
    city: Optional[str]
    profession: Optional[str]
    experience_level: Optional[str]
    business_interest: Optional[str]
    income: Optional[str]
    birthdate: Optional[str]
    state: Optional[str]
    country: Optional[str]
    mobile_number: Optional[str]
    gender: Optional[str]
    usage_purpose: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────────────────────
#  IDEAS
# ─────────────────────────────────────────────────────────────

class IdeaCreate(BaseModel):
    title: str
    description: str
    budget: Optional[Any] = None          # accepts int or string from form
    location: Optional[str] = None
    category: Optional[str] = None
    experience_level: Optional[str] = "beginner"


class IdeaOut(BaseModel):
    id: int
    title: str
    description: str
    budget: Optional[str]
    location: Optional[str]
    category: Optional[str]
    experience_level: Optional[str]
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────────────────────
#  AI RESPONSE
# ─────────────────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    idea_id: int


class AIResponseOut(BaseModel):
    id: int
    idea_id: int
    feasibility: Optional[str]
    cost_breakdown: Optional[str]
    roadmap: Optional[Any]       # parsed JSON list
    marketing: Optional[Any]
    risks: Optional[Any]
    competitors: Optional[Any]
    funding: Optional[Any]
    idea_score: Optional[int]
    stage: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class FullIdeaWithResponse(BaseModel):
    idea: IdeaOut
    response: Optional[AIResponseOut]


# ─────────────────────────────────────────────────────────────
#  DASHBOARD
# ─────────────────────────────────────────────────────────────

class DashboardStats(BaseModel):
    total_ideas: int
    analyzed_ideas: int
    pending_ideas: int
    recent_ideas: List[IdeaOut]
    category_distribution: dict


# ─────────────────────────────────────────────────────────────
#  SETTINGS
# ─────────────────────────────────────────────────────────────

class SettingsUpdate(BaseModel):
    current_password: str
    language: Optional[str] = "en"
    voice_input: Optional[bool] = False
    voice_output: Optional[bool] = False
    ai_detail_level: Optional[str] = "detailed"
    notifications: Optional[bool] = True
    # Profile update fields
    name: Optional[str] = None
    age: Optional[int] = None
    city: Optional[str] = None
    profession: Optional[str] = None
    experience_level: Optional[str] = None
    business_interest: Optional[str] = None
    income: Optional[str] = None
    birthdate: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    mobile_number: Optional[str] = None
    gender: Optional[str] = None
    usage_purpose: Optional[str] = None


class SettingsOut(BaseModel):
    language: str
    voice_input: bool
    voice_output: bool
    ai_detail_level: str
    notifications: bool

    model_config = {"from_attributes": True}
