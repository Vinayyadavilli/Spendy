from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

class TransactionBase(BaseModel):
    amount: float = Field(..., gt=0)
    type: str = Field(..., example="debit") # "debit" or "credit"
    category: str = Field(default="other")
    merchant: str = Field(...)
    note: Optional[str] = ""
    date: Optional[datetime] = None
    account_info: Optional[str] = "Bank Account"
    bank_name: Optional[str] = None
    payment_method: Optional[str] = None
    bank_account_id: Optional[str] = None
    ref_number: Optional[str] = None
    balance_after: Optional[float] = None
    raw_sms: Optional[str] = None
    is_from_sms: Optional[bool] = False

class TransactionCreate(TransactionBase):
    pass

class TransactionResponse(TransactionBase):
    id: str
    user_id: str
    created_at: datetime

    class Config:
        from_attributes = True

class CategoryBreakdownItem(BaseModel):
    category: str
    total_amount: float
    count: int
    percentage: float

class DailyTrendItem(BaseModel):
    date: str
    debit_amount: float
    credit_amount: float

class SpendAnalyticsResponse(BaseModel):
    total_debits: float
    total_credits: float
    net_balance: float
    debit_count: int
    credit_count: int
    debit_category_breakdown: List[CategoryBreakdownItem]
    credit_category_breakdown: List[CategoryBreakdownItem]
    daily_trends: List[DailyTrendItem]

class SmsParseRequest(BaseModel):
    sms_text: str

class SmsParseResponse(BaseModel):
    is_success: bool
    amount: Optional[float] = None
    type: str = "debit"
    merchant: Optional[str] = None
    bank_name: Optional[str] = None
    account_info: Optional[str] = None
    payment_method: Optional[str] = None
    ref_number: Optional[str] = None
    balance_after: Optional[float] = None
    date: Optional[datetime] = None
    category: str = "other"
    error_message: Optional[str] = None

