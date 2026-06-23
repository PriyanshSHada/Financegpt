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

@app.post("/chat", response_model=schemas.TransactionResponse)
def chat_transaction(request: schemas.ChatRequest, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Call GPT-4o Mini to extract transaction details
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a financial extraction AI. Extract the transaction details from the user's message. Output JSON strictly matching this schema: {\"amount\": float, \"category\": string (e.g. Food, Travel, Rent, Salary), \"description\": string, \"type\": \"expense\" or \"income\"}"},
                {"role": "user", "content": request.message}
            ],
            response_format={"type": "json_object"}
        )
        
        extracted_data = json.loads(response.choices[0].message.content)

        # Fix BUG 11: Validate amount is positive
        try:
            amount = float(extracted_data.get("amount", 0))
            if amount <= 0:
                raise ValueError()
            extracted_data["amount"] = amount
        except (ValueError, TypeError):
            raise HTTPException(status_code=422, detail="Could not extract a valid positive amount from your message.")
        
        # Create transaction in DB
        new_transaction = models.Transaction(
            amount=extracted_data["amount"],
            category=extracted_data["category"],
            description=extracted_data["description"],
            type=models.TransactionType(extracted_data["type"]),
            owner_id=current_user.id
        )
        db.add(new_transaction)
        db.commit()
        db.refresh(new_transaction)
        return new_transaction

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process chat: {str(e)}")

@app.get("/dashboard")
def get_dashboard(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    transactions = db.query(models.Transaction).filter(models.Transaction.owner_id == current_user.id).all()
    
    total_expense = sum(t.amount for t in transactions if t.type == models.TransactionType.EXPENSE)
    total_income = sum(t.amount for t in transactions if t.type == models.TransactionType.INCOME)
    
    category_expenses = {}
    for t in transactions:
        if t.type == models.TransactionType.EXPENSE:
            category_expenses[t.category] = category_expenses.get(t.category, 0) + t.amount
    
    return {
        "balance": total_income - total_expense,
        "total_income": total_income,
        "total_expense": total_expense,
        "transactions_count": len(transactions),
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

        # Fix BUG 11: Validate amount is positive
        try:
            amount = float(extracted_data.get("amount", 0))
            if amount <= 0:
                raise ValueError()
            extracted_data["amount"] = amount
        except (ValueError, TypeError):
            raise HTTPException(status_code=422, detail="Could not extract a valid positive amount from the screenshot.")
        
        new_transaction = models.Transaction(
            amount=extracted_data["amount"],
            category=extracted_data["category"],
            description=extracted_data["description"],
            type=models.TransactionType(extracted_data["type"]),
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
