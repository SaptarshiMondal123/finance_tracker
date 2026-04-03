from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import Response
from sqlalchemy.orm import Session
from database import get_db
from models import User, TransactionType
from schemas import TransactionCreate, TransactionUpdate, TransactionOut
from services import transaction_service
from dependencies import require_viewer_or_above, require_analyst_or_above, require_admin
from datetime import date
from typing import Optional

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.post("/", response_model=TransactionOut, status_code=status.HTTP_201_CREATED)
def create_transaction(
    data: TransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Admin only: create a new financial transaction."""
    return transaction_service.create_transaction(db, data, current_user)


@router.get("/", response_model=list[TransactionOut])
def list_transactions(
    tx_type: Optional[TransactionType] = Query(None, description="Filter by income or expense"),
    category: Optional[str] = Query(None, description="Filter by category (partial match)"),
    start_date: Optional[date] = Query(None, description="Filter from this date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="Filter until this date (YYYY-MM-DD)"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(20, ge=1, le=100, description="Results per page (max 100)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_viewer_or_above)
):
    """
    List transactions with optional filters. Admins see all; others see their own.
    Supports pagination via skip/limit.
    """
    return transaction_service.get_transactions(
        db, current_user, tx_type, category, start_date, end_date, skip, limit
    )


@router.get("/export/csv")
def export_csv(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_analyst_or_above)
):
    """Analyst/Admin: export transactions as a CSV file download."""
    csv_data = transaction_service.export_transactions_csv(db, current_user)
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=transactions.csv"}
    )


@router.get("/export/json")
def export_json(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_analyst_or_above)
):
    """Analyst/Admin: export transactions as JSON."""
    return transaction_service.export_transactions_json(db, current_user)


@router.get("/{transaction_id}", response_model=TransactionOut)
def get_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_viewer_or_above)
):
    """Fetch a single transaction by ID."""
    tx = transaction_service.get_transaction_or_404(db, transaction_id)
    # Non-admins can only view their own
    from models import UserRole
    if current_user.role != UserRole.admin and tx.owner_id != current_user.id:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Access denied")
    return tx


@router.patch("/{transaction_id}", response_model=TransactionOut)
def update_transaction(
    transaction_id: int,
    data: TransactionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Admin only: update a transaction by ID."""
    return transaction_service.update_transaction(db, transaction_id, data, current_user)


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Admin only: delete a transaction by ID."""
    transaction_service.delete_transaction(db, transaction_id, current_user)
