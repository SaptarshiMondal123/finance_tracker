from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import User
from schemas import FinancialSummary
from services import summary_service
from dependencies import require_analyst_or_above

router = APIRouter(prefix="/summary", tags=["Summary & Analytics"])


@router.get("/", response_model=FinancialSummary)
def get_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_analyst_or_above)
):
    """
    Analyst/Admin: get a full financial summary including:
    - Total income, expenses, and current balance
    - Category-wise breakdown
    - Monthly income vs expense totals
    - Recent 5 transactions
    """
    return summary_service.get_financial_summary(db, current_user)
