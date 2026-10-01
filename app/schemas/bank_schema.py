from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class BankAccountBase(BaseModel):
    bank_name: str = Field(..., example="HDFC Bank")
    account_name: str = Field(..., example="Salary Account")
    account_number_last4: str = Field(default="XXXX", example="4921")
    initial_balance: float = Field(default=0.0, ge=0.0, example=50000.0)
    color_hex: Optional[str] = Field(default="#6366F1")

class BankAccountCreate(BankAccountBase):
    pass

class BankAccountUpdate(BaseModel):
    account_name: Optional[str] = None
    bank_name: Optional[str] = None
    account_number_last4: Optional[str] = None
    current_balance: Optional[float] = None
    color_hex: Optional[str] = None

class BankAccountResponse(BankAccountBase):
    id: str
    user_id: str
    current_balance: float
    created_at: datetime

    class Config:
        from_attributes = True
