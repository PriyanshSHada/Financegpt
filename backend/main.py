from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from . import models, schemas, auth
from .database import engine, get_db
import os
import json
import base64
from openai import OpenAI
from pydantic import BaseModel, Field, ValidationError
from typing import Optional, Literal

class ExtractedTransaction(BaseModel):
    amount: float
    category: str = "Other"
    description: str = "Unknown"
    type: Literal["expense", "income"] = "expense"

class ChatGPTResponse(BaseModel):
    reply: str
    extracted_transaction: Optional[ExtractedTransaction] = None

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="FinanceGPT API")

# Fix BUG 2: Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tighten this in production to specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Initialize OpenAI Client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = auth.jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except auth.JWTError:
        raise credentials_exception
    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

@app.post("/register", response_model=schemas.UserResponse)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = auth.get_password_hash(user.password)
    new_user = models.User(username=user.username, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/token", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    access_token_expires = auth.timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/chat", response_model=schemas.ChatResponse)
def chat_transaction(request: schemas.ChatRequest, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a conversational financial assistant. Reply to the user naturally. If the user mentions a transaction (income or expense), extract it. Output JSON strictly matching this schema: {\"reply\": \"Your conversational response\", \"extracted_transaction\": {\"amount\": float, \"category\": string, \"description\": string, \"type\": \"expense\" or \"income\"} }. If no transaction is mentioned, set \"extracted_transaction\" to null."},
                {"role": "user", "content": request.message}
            ],
            response_format={"type": "json_object"}
        )
        
        extracted_data = json.loads(response.choices[0].message.content)
        
        try:
            parsed_data = ChatGPTResponse(**extracted_data)
        except ValidationError:
            return {"reply": "I processed your request but couldn't understand the exact transaction details.", "transaction": None}

        reply = parsed_data.reply
        transaction_data = parsed_data.extracted_transaction

        new_transaction = None
        if transaction_data and transaction_data.amount > 0:
            new_transaction = models.Transaction(
                amount=transaction_data.amount,
                category=transaction_data.category,
                description=transaction_data.description,
                type=models.TransactionType(transaction_data.type),
                owner_id=current_user.id
            )
            db.add(new_transaction)
            db.commit()
            db.refresh(new_transaction)

        return {"reply": reply, "transaction": new_transaction}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process chat: {str(e)}")

@app.get("/dashboard")
def get_dashboard(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    from sqlalchemy import func
    
    # Calculate totals using DB aggregates
    expense_result = db.query(func.sum(models.Transaction.amount)).filter(
        models.Transaction.owner_id == current_user.id,
        models.Transaction.type == models.TransactionType.EXPENSE
    ).scalar()
    total_expense = float(expense_result) if expense_result else 0.0
    
    income_result = db.query(func.sum(models.Transaction.amount)).filter(
        models.Transaction.owner_id == current_user.id,
        models.Transaction.type == models.TransactionType.INCOME
    ).scalar()
    total_income = float(income_result) if income_result else 0.0

    transactions_count = db.query(models.Transaction).filter(models.Transaction.owner_id == current_user.id).count()
    
    category_expenses_query = db.query(
        models.Transaction.category, func.sum(models.Transaction.amount)
    ).filter(
        models.Transaction.owner_id == current_user.id,
        models.Transaction.type == models.TransactionType.EXPENSE
    ).group_by(models.Transaction.category).all()
    
    category_expenses = {cat: float(amt) for cat, amt in category_expenses_query}
    
    return {
        "balance": total_income - total_expense,
        "total_income": total_income,
        "total_expense": total_expense,
        "transactions_count": transactions_count,
        "category_expenses": category_expenses
    }

@app.post("/budgets", response_model=schemas.BudgetResponse)
def create_budget(budget: schemas.BudgetCreate, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    new_budget = models.Budget(
        category=budget.category,
        limit_amount=budget.limit_amount,
        owner_id=current_user.id
    )
    db.add(new_budget)
    db.commit()
    db.refresh(new_budget)
    return new_budget

@app.get("/budgets", response_model=list[schemas.BudgetResponse])
def get_budgets(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(models.Budget).filter(models.Budget.owner_id == current_user.id).all()

@app.post("/upload-screenshot", response_model=schemas.TransactionResponse)
def upload_screenshot(file: UploadFile = File(...), current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        contents = file.file.read()
        base64_image = base64.b64encode(contents).decode('utf-8')
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Extract the transaction details from this UPI screenshot. Output strictly JSON with keys: amount (float), category (string), description (string), type (string: 'expense' or 'income')."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                }
            ],
            response_format={"type": "json_object"}
        )
        
        extracted_data = json.loads(response.choices[0].message.content)
        
        try:
            parsed_data = ExtractedTransaction(**extracted_data)
            if parsed_data.amount <= 0:
                raise ValueError()
        except (ValidationError, ValueError):
            raise HTTPException(status_code=422, detail="Could not extract valid transaction details from the screenshot.")
        
        new_transaction = models.Transaction(
            amount=parsed_data.amount,
            category=parsed_data.category,
            description=parsed_data.description,
            type=models.TransactionType(parsed_data.type),
            owner_id=current_user.id
        )
        db.add(new_transaction)
        db.commit()
        db.refresh(new_transaction)
        return new_transaction
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process screenshot: {str(e)}")
