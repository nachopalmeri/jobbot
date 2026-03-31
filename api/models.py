from pydantic import BaseModel, EmailStr
from typing import Optional, List
from enum import Enum


class PlanType(str, Enum):
    FREE = "free"
    PRO = "pro"
    PREMIUM = "premium"


class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    CANCELED = "canceled"
    PAST_DUE = "past_due"


class UserBase(BaseModel):
    telegram_id: int
    email: Optional[EmailStr] = None
    name: str


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int
    plan: PlanType = PlanType.FREE
    subscription_status: Optional[SubscriptionStatus] = None
    subscription_expires_at: Optional[str] = None
    ai_analyses_used: int = 0
    ai_analyses_limit: int = 2
    searches_used: int = 0
    searches_limit: int = 5
    job_tracker_enabled: bool = False

    class Config:
        from_attributes = True


class UsageResponse(BaseModel):
    ai_analyses_used: int
    ai_analyses_limit: int
    searches_used: int
    searches_limit: int
    remaining_analyses: int
    remaining_searches: int


class JobApplicationCreate(BaseModel):
    job_title: str
    company: str
    url: str
    notes: Optional[str] = None


class JobApplicationResponse(JobApplicationCreate):
    id: int
    status: str
    applied_at: str

    class Config:
        from_attributes = True
