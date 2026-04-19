from sqlalchemy import (
    Column, Integer, String, Text, DateTime,
    ForeignKey, Boolean, Float
)
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class User(Base):
    __tablename__ = "users"

    id              = Column(Integer, primary_key=True, index=True)
    name            = Column(String(100), nullable=False)
    email           = Column(String(150), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    language        = Column(String(10), default="en")
    age             = Column(Integer, nullable=True)
    city            = Column(String(100), nullable=True)
    profession      = Column(String(100), nullable=True)
    experience_level= Column(String(50), nullable=True)
    business_interest= Column(String(200), nullable=True)
    income          = Column(String(50), nullable=True)
    birthdate       = Column(String(20), nullable=True)
    state           = Column(String(100), nullable=True)
    country         = Column(String(100), nullable=True)
    mobile_number   = Column(String(20), nullable=True)
    gender          = Column(String(20), nullable=True)
    usage_purpose   = Column(String(100), nullable=True)
    is_active       = Column(Boolean, default=True)
    created_at      = Column(DateTime, default=datetime.utcnow)

    # Relationships
    ideas    = relationship("Idea", back_populates="owner", cascade="all, delete-orphan")
    settings = relationship("UserSettings", back_populates="user",
                            uselist=False, cascade="all, delete-orphan")


class Idea(Base):
    __tablename__ = "ideas"

    id               = Column(Integer, primary_key=True, index=True)
    user_id          = Column(Integer, ForeignKey("users.id"), nullable=False)
    title            = Column(String(200), nullable=False)
    description      = Column(Text, nullable=False)
    budget           = Column(String(50))          # e.g. "10000-50000"
    location         = Column(String(150))
    category         = Column(String(100))
    experience_level = Column(String(50), default="beginner")
    status           = Column(String(20), default="pending")   # pending / analyzed
    created_at       = Column(DateTime, default=datetime.utcnow)

    # Relationships
    owner    = relationship("User", back_populates="ideas")
    response = relationship("AIResponse", back_populates="idea",
                            uselist=False, cascade="all, delete-orphan")


class AIResponse(Base):
    __tablename__ = "ai_responses"

    id             = Column(Integer, primary_key=True, index=True)
    idea_id        = Column(Integer, ForeignKey("ideas.id"), nullable=False, unique=True)
    feasibility    = Column(Text)
    cost_breakdown = Column(Text)
    roadmap        = Column(Text)      # JSON-encoded list of steps
    marketing      = Column(Text)      # JSON-encoded list of tips
    risks          = Column(Text)      # JSON-encoded list of risks
    competitors    = Column(Text)      # JSON-encoded list of competitors
    funding        = Column(Text)      # JSON-encoded list of funding options
    idea_score     = Column(Integer)   # 0-100
    stage          = Column(String(50))  # Idea / MVP / Growth / Scale
    created_at     = Column(DateTime, default=datetime.utcnow)

    # Relationship
    idea = relationship("Idea", back_populates="response")


class UserSettings(Base):
    __tablename__ = "user_settings"

    id              = Column(Integer, primary_key=True, index=True)
    user_id         = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    language        = Column(String(10), default="en")
    voice_input     = Column(Boolean, default=False)
    voice_output    = Column(Boolean, default=False)
    ai_detail_level = Column(String(20), default="detailed")  # brief / detailed / expert
    notifications   = Column(Boolean, default=True)

    # Relationship
    user = relationship("User", back_populates="settings")
