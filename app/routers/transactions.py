from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..core.dependencies import get_current_user
from ..models.user import User
from ..models.bank_account import BankAccount
from ..models.transaction import Transaction
from ..schemas.transaction_schema import (
    TransactionCreate,
    TransactionResponse,
    SpendAnalyticsResponse,
    CategoryBreakdownItem,
    DailyTrendItem,
)

router = APIRouter(prefix="/transactions", tags=["Transactions"])

@router.get("/", response_model=List[TransactionResponse])
def get_transactions(
    type_filter: Optional[str] = Query(None, pattern="^(debit|credit)$"),
    bank_account_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Transaction).filter(Transaction.user_id == current_user.id)
    if type_filter:
        query = query.filter(Transaction.type == type_filter)
    if bank_account_id:
        query = query.filter(Transaction.bank_account_id == bank_account_id)
    
    return query.order_by(Transaction.date.desc()).all()

def _find_matching_bank_account(db: Session, user_id: str, bank_account_id: Optional[str], account_info: Optional[str], raw_sms: Optional[str]) -> Optional[BankAccount]:
    user_accounts = db.query(BankAccount).filter(BankAccount.user_id == user_id).all()
    if not user_accounts:
        return None

    # 1. Exact ID match
    if bank_account_id:
        for acc in user_accounts:
            if acc.id == bank_account_id:
                return acc

    # 2. Match by Bank Name or Account Number in account_info or raw_sms
    text_to_search = f"{account_info or ''} {raw_sms or ''}".lower()
    for acc in user_accounts:
        b_name = acc.bank_name.lower()
        if b_name in text_to_search or ("icici" in b_name and "icici" in text_to_search) or ("hdfc" in b_name and "hdfc" in text_to_search) or ("sbi" in b_name and "sbi" in text_to_search) or ("axis" in b_name and "axis" in text_to_search) or ("kotak" in b_name and "kotak" in text_to_search):
            return acc
        if acc.account_number and acc.account_number in text_to_search:
            return acc

    # 3. If user has only 1 connected bank account, associate with that account
    if len(user_accounts) == 1:
        return user_accounts[0]

    return None

@router.post("/", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def create_transaction(
    tx_in: TransactionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Match connected bank account
    bank_acc = _find_matching_bank_account(
        db=db,
        user_id=current_user.id,
        bank_account_id=tx_in.bank_account_id,
        account_info=tx_in.account_info,
        raw_sms=tx_in.raw_sms
    )

    # Create transaction
    new_tx = Transaction(
        user_id=current_user.id,
        bank_account_id=bank_acc.id if bank_acc else tx_in.bank_account_id,
        amount=tx_in.amount,
        type=tx_in.type.lower(),
        category=tx_in.category,
        merchant=tx_in.merchant,
        note=tx_in.note or "",
        date=tx_in.date or datetime.now(timezone.utc),
        account_info=tx_in.account_info or (f"{bank_acc.bank_name} A/C" if bank_acc else "Bank Account"),
        ref_number=tx_in.ref_number,
        balance_after=tx_in.balance_after,
        raw_sms=tx_in.raw_sms,
        is_from_sms=tx_in.is_from_sms or False,
    )
    db.add(new_tx)

    # Dynamic Bank Balance Adjustment
    if bank_acc:
        if new_tx.type == "debit":
            bank_acc.current_balance -= new_tx.amount
        elif new_tx.type == "credit":
            bank_acc.current_balance += new_tx.amount

    db.commit()
    db.refresh(new_tx)
    return new_tx

@router.post("/batch", response_model=List[TransactionResponse], status_code=status.HTTP_201_CREATED)
def create_transactions_batch(
    tx_list: List[TransactionCreate],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    created_list = []
    for tx_in in tx_list:
        # Check duplicate by raw_sms or ref_number
        if tx_in.raw_sms:
            existing = db.query(Transaction).filter(
                Transaction.user_id == current_user.id,
                Transaction.raw_sms == tx_in.raw_sms
            ).first()
            if existing:
                continue

        if tx_in.ref_number:
            existing_ref = db.query(Transaction).filter(
                Transaction.user_id == current_user.id,
                Transaction.ref_number == tx_in.ref_number
            ).first()
            if existing_ref:
                continue

        bank_acc = _find_matching_bank_account(
            db=db,
            user_id=current_user.id,
            bank_account_id=tx_in.bank_account_id,
            account_info=tx_in.account_info,
            raw_sms=tx_in.raw_sms
        )

        new_tx = Transaction(
            user_id=current_user.id,
            bank_account_id=bank_acc.id if bank_acc else tx_in.bank_account_id,
            amount=tx_in.amount,
            type=tx_in.type.lower(),
            category=tx_in.category,
            merchant=tx_in.merchant,
            note=tx_in.note or "",
            date=tx_in.date or datetime.now(timezone.utc),
            account_info=tx_in.account_info or (f"{bank_acc.bank_name} A/C" if bank_acc else "Bank Account"),
            ref_number=tx_in.ref_number,
            balance_after=tx_in.balance_after,
            raw_sms=tx_in.raw_sms,
            is_from_sms=tx_in.is_from_sms or False,
        )
        db.add(new_tx)

        if bank_acc:
            if new_tx.type == "debit":
                bank_acc.current_balance -= new_tx.amount
            elif new_tx.type == "credit":
                bank_acc.current_balance += new_tx.amount

        created_list.append(new_tx)

    db.commit()
    for tx in created_list:
        db.refresh(tx)
    return created_list

@router.get("/analytics", response_model=SpendAnalyticsResponse)
def get_spend_analytics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Transaction).filter(Transaction.user_id == current_user.id)
    if start_date:
        query = query.filter(Transaction.date >= start_date)
    if end_date:
        query = query.filter(Transaction.date <= end_date)
    
    transactions = query.all()

    debits = [t for t in transactions if t.type == "debit"]
    credits = [t for t in transactions if t.type == "credit"]

    total_debits = sum(t.amount for t in debits)
    total_credits = sum(t.amount for t in credits)

    # Debit category breakdown
    debit_cat_map = {}
    for t in debits:
        debit_cat_map[t.category] = debit_cat_map.get(t.category, 0.0) + t.amount
    
    debit_category_breakdown = [
        CategoryBreakdownItem(
            category=cat,
            total_amount=amt,
            count=len([t for t in debits if t.category == cat]),
            percentage=(amt / total_debits * 100) if total_debits > 0 else 0.0
        )
        for cat, amt in sorted(debit_cat_map.items(), key=lambda item: item[1], reverse=True)
    ]

    # Credit category breakdown
    credit_cat_map = {}
    for t in credits:
        credit_cat_map[t.category] = credit_cat_map.get(t.category, 0.0) + t.amount
    
    credit_category_breakdown = [
        CategoryBreakdownItem(
            category=cat,
            total_amount=amt,
            count=len([t for t in credits if t.category == cat]),
            percentage=(amt / total_credits * 100) if total_credits > 0 else 0.0
        )
        for cat, amt in sorted(credit_cat_map.items(), key=lambda item: item[1], reverse=True)
    ]

    # Daily trend points
    date_map = {}
    for t in transactions:
        d_str = t.date.strftime("%Y-%m-%d")
        if d_str not in date_map:
            date_map[d_str] = {"debit": 0.0, "credit": 0.0}
        if t.type == "debit":
            date_map[d_str]["debit"] += t.amount
        else:
            date_map[d_str]["credit"] += t.amount

    daily_trends = [
        DailyTrendItem(
            date=d_str,
            debit_amount=vals["debit"],
            credit_amount=vals["credit"]
        )
        for d_str, vals in sorted(date_map.items())
    ]

    return SpendAnalyticsResponse(
        total_debits=total_debits,
        total_credits=total_credits,
        net_balance=total_credits - total_debits,
        debit_count=len(debits),
        credit_count=len(credits),
        debit_category_breakdown=debit_category_breakdown,
        credit_category_breakdown=credit_category_breakdown,
        daily_trends=daily_trends,
    )

@router.delete("/{tx_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    tx_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    tx = db.query(Transaction).filter(Transaction.id == tx_id, Transaction.user_id == current_user.id).first()
    if not tx:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    
    # Revert bank balance
    if tx.bank_account_id:
        bank_acc = db.query(BankAccount).filter(BankAccount.id == tx.bank_account_id).first()
        if bank_acc:
            if tx.type == "debit":
                bank_acc.current_balance += tx.amount
            elif tx.type == "credit":
                bank_acc.current_balance -= tx.amount

    db.delete(tx)
    db.commit()
    return None
