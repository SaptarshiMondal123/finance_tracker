from sqlalchemy.orm import Session
from sqlalchemy import func
from models import Transaction, TransactionType, User, UserRole
from schemas import FinancialSummary, CategoryBreakdown, MonthlySummary, TransactionOut
from collections import defaultdict


def get_financial_summary(db: Session, user: User) -> FinancialSummary:
    """
    Generate a full financial summary for the current user (or all users if admin).
    Includes totals, category breakdown, monthly summaries, and recent activity.
    """
    base_query = db.query(Transaction)
    if user.role != UserRole.admin:
        base_query = base_query.filter(Transaction.owner_id == user.id)

    transactions = base_query.all()

    # ── Totals ────────────────────────────────────────────────────────────────
    total_income = sum(t.amount for t in transactions if t.type == TransactionType.income)
    total_expenses = sum(t.amount for t in transactions if t.type == TransactionType.expense)
    current_balance = total_income - total_expenses

    # ── Category Breakdown ────────────────────────────────────────────────────
    category_totals: dict[str, float] = defaultdict(float)
    for t in transactions:
        category_totals[t.category] += t.amount

    category_breakdown = [
        CategoryBreakdown(category=cat, total=round(total, 2))
        for cat, total in sorted(category_totals.items(), key=lambda x: -x[1])
    ]

    # ── Monthly Summaries ─────────────────────────────────────────────────────
    monthly: dict[tuple, dict] = defaultdict(lambda: {"income": 0.0, "expenses": 0.0})
    for t in transactions:
        key = (t.date.year, t.date.month)
        if t.type == TransactionType.income:
            monthly[key]["income"] += t.amount
        else:
            monthly[key]["expenses"] += t.amount

    monthly_summaries = [
        MonthlySummary(
            year=year,
            month=month,
            income=round(data["income"], 2),
            expenses=round(data["expenses"], 2),
            balance=round(data["income"] - data["expenses"], 2)
        )
        for (year, month), data in sorted(monthly.items(), reverse=True)
    ]

    # ── Recent Activity (last 5) ──────────────────────────────────────────────
    recent = sorted(transactions, key=lambda t: t.date, reverse=True)[:5]
    recent_out = [TransactionOut.model_validate(t) for t in recent]

    return FinancialSummary(
        total_income=round(total_income, 2),
        total_expenses=round(total_expenses, 2),
        current_balance=round(current_balance, 2),
        category_breakdown=category_breakdown,
        monthly_summaries=monthly_summaries,
        recent_transactions=recent_out
    )
