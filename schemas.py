from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import date
from models import TransactionType, UserRole


# ─── Auth Schemas ────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: UserRole = UserRole.viewer

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v


class UserOut(BaseModel):
    id: int
    username: str
    email: str
    role: UserRole

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


# ─── Transaction Schemas ──────────────────────────────────────────────────────

class TransactionCreate(BaseModel):
    amount: float
    type: TransactionType
    category: str
    date: date
    notes: Optional[str] = None

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Amount must be greater than zero")
        return v

    @field_validator("category")
    @classmethod
    def category_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Category cannot be blank")
        return v.strip()


class TransactionUpdate(BaseModel):
    amount: Optional[float] = None
    type: Optional[TransactionType] = None
    category: Optional[str] = None
    date: Optional[date] = None
    notes: Optional[str] = None

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v <= 0:
            raise ValueError("Amount must be greater than zero")
        return v


class TransactionOut(BaseModel):
    id: int
    amount: float
    type: TransactionType
    category: str
    date: date
    notes: Optional[str]
    owner_id: int

    model_config = {"from_attributes": True}


# ─── Summary Schemas ──────────────────────────────────────────────────────────

class CategoryBreakdown(BaseModel):
    category: str
    total: float


class MonthlySummary(BaseModel):
    year: int
    month: int
    income: float
    expenses: float
    balance: float


class FinancialSummary(BaseModel):
    total_income: float
    total_expenses: float
    current_balance: float
    category_breakdown: list[CategoryBreakdown]
    monthly_summaries: list[MonthlySummary]
    recent_transactions: list[TransactionOut]
