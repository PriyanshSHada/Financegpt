from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from .models import TransactionType

class UserCreate(BaseModel):
    username: str
    password: str

class DashboardResponse(BaseModel):
    balance: float
    total_income: float
    total_expense: float
    transactions_count: int
    category_expenses: dict[str, float]
    class Config:
        from_attributes = True

class UserResponse(BaseModel):
    id: int
    username: str
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class ChatRequest(BaseModel):
    message: str

class TransactionBase(BaseModel):
    amount: float
    category: str
    description: str
    type: TransactionType
    date: Optional[datetime] = None

class TransactionCreate(TransactionBase):
    pass

class TransactionResponse(TransactionBase):
    id: int
    owner_id: int
    class Config:
        from_attributes = True

class BudgetBase(BaseModel):
    category: str
    limit_amount: float

class BudgetCreate(BudgetBase):
    pass

class BudgetResponse(BudgetBase):
    id: int
    owner_id: int
    class Config:
        from_attributes = True

class ChatResponse(BaseModel):
    reply: str
    transaction: Optional[TransactionResponse] = None
