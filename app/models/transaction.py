from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from ..core.database import Base

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    bank_account_id = Column(String(36), ForeignKey("bank_accounts.id", ondelete="SET NULL"), nullable=True, index=True)
    
    amount = Column(Float, nullable=False)
    type = Column(String(10), nullable=False) # "debit" or "credit"
    category = Column(String(50), nullable=False, default="other")
    merchant = Column(String(255), nullable=False)
    note = Column(String(500), nullable=True, default="")
    date = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    account_info = Column(String(100), nullable=False, default="Bank Account")
    ref_number = Column(String(100), nullable=True)
    balance_after = Column(Float, nullable=True)
    raw_sms = Column(Text, nullable=True)
    is_from_sms = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", back_populates="transactions")
    bank_account = relationship("BankAccount", back_populates="transactions")
