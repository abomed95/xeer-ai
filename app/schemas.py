"""Schémas Pydantic de l'API."""
from pydantic import BaseModel, EmailStr, Field


# --- Auth ---
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = ""


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UpdateProfileRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=80)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)


class UserOut(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    plan: str
    plan_expires_at: str | None = None
    org_name: str | None = None
    quota: int | None = None          # None = illimité
    questions_used: int = 0
    questions_remaining: int | None = None


class AuthResponse(BaseModel):
    token: str
    user: UserOut


# --- Chat ---
class AskRequest(BaseModel):
    question: str
    top_k: int = 5
    conversation_id: str | None = None


class SourceItem(BaseModel):
    id: str
    page: str
    chunk_index: int | None = None
    source_file: str | None = None
    distance: float
    score: int
    excerpt: str


class AskResponse(BaseModel):
    conversation_id: str
    message_id: int                    # id du message assistant (pour le feedback)
    question: str
    answer: str
    sources: list[SourceItem]
    questions_remaining: int | None = None


class FeedbackRequest(BaseModel):
    rating: int                        # 1 = 👍, -1 = 👎


# --- Facturation ---
class CheckoutRequest(BaseModel):
    provider: str                      # waafi | cacbank | card
    method: str = ""                   # visa | mastercard | waafi | cacpay
    phone: str = ""                    # requis pour waafi
    plan: str = "premium"


class ConfirmPaymentRequest(BaseModel):
    reference: str


class OrgLeadRequest(BaseModel):
    name: str
    email: EmailStr
    organization: str
    message: str = ""


# --- Admin ---
class SetPlanRequest(BaseModel):
    plan: str                          # free | premium | organization
    days: int = 30
    custom_quota: int | None = None
    org_name: str | None = None


class LeadStatusRequest(BaseModel):
    status: str                        # new | contacted | closed
