from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from ..core.database import Base

class BankAccount(Base):
    __tablename__ = "bank_accounts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    bank_name = Column(String(100), nullable=False) # e.g. "HDFC Bank", "SBI", "ICICI", "Axis"
    account_name = Column(String(100), nullable=False) # e.g. "Primary Salary A/C", "Savings", "Emergency Fund"
    account_number_last4 = Column(String(10), nullable=False, default="XXXX") # e.g. "4921"
    initial_balance = Column(Float, nullable=False, default=0.0) # User entered amount
    current_balance = Column(Float, nullable=False, default=0.0) # Dynamic balance adjusted by debits & credits
    color_hex = Column(String(10), nullable=False, default="#6366F1")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", back_populates="bank_accounts")
    transactions = relationship("Transaction", back_populates="bank_account", cascade="all, delete-orphan")
