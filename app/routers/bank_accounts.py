from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..core.dependencies import get_current_user
from ..models.user import User
from ..models.bank_account import BankAccount
from ..schemas.bank_schema import BankAccountCreate, BankAccountResponse, BankAccountUpdate

router = APIRouter(prefix="/bank-accounts", tags=["Bank Accounts"])

@router.get("/", response_model=List[BankAccountResponse])
def get_user_bank_accounts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    accounts = db.query(BankAccount).filter(BankAccount.user_id == current_user.id).order_by(BankAccount.created_at.desc()).all()
    return accounts

@router.post("/", response_model=BankAccountResponse, status_code=status.HTTP_201_CREATED)
def create_bank_account(
    account_in: BankAccountCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    new_account = BankAccount(
        user_id=current_user.id,
        bank_name=account_in.bank_name,
        account_name=account_in.account_name,
        account_number_last4=account_in.account_number_last4,
        initial_balance=account_in.initial_balance,
        current_balance=account_in.initial_balance,
        color_hex=account_in.color_hex or "#6366F1",
    )
    db.add(new_account)
    db.commit()
    db.refresh(new_account)
    return new_account

@router.put("/{account_id}", response_model=BankAccountResponse)
def update_bank_account(
    account_id: str,
    account_update: BankAccountUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    account = db.query(BankAccount).filter(BankAccount.id == account_id, BankAccount.user_id == current_user.id).first()
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bank account not found")

    update_data = account_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(account, key, value)

    db.commit()
    db.refresh(account)
    return account

@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bank_account(
    account_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    account = db.query(BankAccount).filter(BankAccount.id == account_id, BankAccount.user_id == current_user.id).first()
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bank account not found")
    
    db.delete(account)
    db.commit()
    return None
