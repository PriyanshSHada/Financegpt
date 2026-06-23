from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum
import datetime
from .database import Base

class TransactionType(str, enum.Enum):
    EXPENSE = "expense"
    INCOME = "income"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)

    transactions = relationship("Transaction", back_populates="owner")
    budgets = relationship("Budget", back_populates="owner")

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float, nullable=False)
    category = Column(String, index=True)
    description = Column(String)
    date = Column(DateTime, default=datetime.datetime.utcnow)
    type = Column(Enum(TransactionType), default=TransactionType.EXPENSE)
    
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="transactions")

class Budget(Base):
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String, index=True)
    limit_amount = Column(Float, nullable=False)
    
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="budgets")
