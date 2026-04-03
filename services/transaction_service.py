from sqlalchemy.orm import Session
from sqlalchemy import and_
from models import Transaction, TransactionType, User, UserRole
from schemas import TransactionCreate, TransactionUpdate
from fastapi import HTTPException, status
from datetime import date
from typing import Optional
import csv
import json
import io


def get_transaction_or_404(db: Session, transaction_id: int) -> Transaction:
    tx = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return tx


def can_modify(user: User, transaction: Transaction) -> bool:
    """Admins can modify all; others can only modify their own."""
    return user.role == UserRole.admin or transaction.owner_id == user.id


def create_transaction(db: Session, data: TransactionCreate, user: User) -> Transaction:
    tx = Transaction(**data.model_dump(), owner_id=user.id)
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx


def get_transactions(
    db: Session,
    user: User,
    tx_type: Optional[TransactionType] = None,
    category: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    skip: int = 0,
    limit: int = 20
) -> list[Transaction]:
    # Admins see all transactions; others see only their own
    query = db.query(Transaction)
    if user.role != UserRole.admin:
        query = query.filter(Transaction.owner_id == user.id)

    filters = []
    if tx_type:
        filters.append(Transaction.type == tx_type)
    if category:
        filters.append(Transaction.category.ilike(f"%{category}%"))
    if start_date:
        filters.append(Transaction.date >= start_date)
    if end_date:
        filters.append(Transaction.date <= end_date)

    if filters:
        query = query.filter(and_(*filters))

    return query.order_by(Transaction.date.desc()).offset(skip).limit(limit).all()


def update_transaction(
    db: Session, transaction_id: int, data: TransactionUpdate, user: User
) -> Transaction:
    tx = get_transaction_or_404(db, transaction_id)
    if not can_modify(user, tx):
        raise HTTPException(status_code=403, detail="Not authorized to modify this transaction")

    updates = data.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(tx, field, value)

    db.commit()
    db.refresh(tx)
    return tx


def delete_transaction(db: Session, transaction_id: int, user: User) -> None:
    tx = get_transaction_or_404(db, transaction_id)
    if not can_modify(user, tx):
        raise HTTPException(status_code=403, detail="Not authorized to delete this transaction")
    db.delete(tx)
    db.commit()


def export_transactions_csv(db: Session, user: User) -> str:
    """Export all accessible transactions as a CSV string."""
    transactions = get_transactions(db, user, limit=10000)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "amount", "type", "category", "date", "notes", "owner_id"])
    for tx in transactions:
        writer.writerow([tx.id, tx.amount, tx.type.value, tx.category, tx.date, tx.notes, tx.owner_id])
    return output.getvalue()


def export_transactions_json(db: Session, user: User) -> list[dict]:
    """Export all accessible transactions as a list of dicts."""
    transactions = get_transactions(db, user, limit=10000)
    return [
        {
            "id": tx.id,
            "amount": tx.amount,
            "type": tx.type.value,
            "category": tx.category,
            "date": str(tx.date),
            "notes": tx.notes,
            "owner_id": tx.owner_id
        }
        for tx in transactions
    ]
