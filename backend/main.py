import logging

from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
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


logger = logging.getLogger(__name__)


def _extract_json(raw: str) -> dict:
    """Strip markdown code fences that Meta Llama sometimes adds around JSON output."""
    import re
    # Remove ```json ... ``` or ``` ... ``` wrappers
    cleaned = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned.strip())
    return json.loads(cleaned)

app = FastAPI(title="FinanceGPT API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tighten this in production to specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def _build_ai_client() -> tuple[OpenAI, str]:
    """
    Support both the current Bedrock-based deployment and older OpenAI-style
    environment variable names so production doesn't fail with a vague 500.
    """
    bedrock_key = os.getenv("BEDROCK_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    if bedrock_key:
        base_url = os.getenv("BEDROCK_API_BASE", "https://bedrock-mantle.us-east-1.api.aws/v1")
        model = os.getenv("META_MODEL", "meta.llama3-3-70b-instruct-v1:0")
        return OpenAI(api_key=bedrock_key, base_url=base_url), model

    if openai_key:
        base_url = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        return OpenAI(api_key=openai_key, base_url=base_url), model

    raise RuntimeError(
        "Missing AI credentials. Set either BEDROCK_API_KEY for Bedrock or OPENAI_API_KEY for OpenAI."
    )


# Initialize the OpenAI-compatible client once at startup.
client, META_MODEL = _build_ai_client()

@app.on_event("startup")
def startup_event():
    try:
        models.Base.metadata.create_all(bind=engine)
        logger.info("Database tables created/verified successfully")
    except Exception as e:
        logger.exception("Database initialization failed - verify DATABASE_URL is correct in environment variables")
        logger.error("Database URL format should be: postgresql://postgres:PASSWORD@db.YOUR_PROJECT_ID.supabase.co:5432/postgres")
        logger.error("For Supabase, ensure the username is 'postgres' (not 'postgres.project-id')")
        raise

@app.get("/health")
def health_check():
    db_status = "ok"
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:
        db_status = f"down: {exc.__class__.__name__}"

    ai_provider = "bedrock" if os.getenv("BEDROCK_API_KEY") else "openai" if os.getenv("OPENAI_API_KEY") else "missing"
    return {"status": "ok", "database": db_status, "ai_provider": ai_provider}

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
    try:
        user = db.query(models.User).filter(models.User.username == username).first()
    except SQLAlchemyError:
        logger.exception("Database error while fetching current user")
        raise HTTPException(status_code=503, detail="Database unavailable")
    if user is None:
        raise credentials_exception
    return user

@app.post("/register", response_model=schemas.UserResponse)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    try:
        db_user = db.query(models.User).filter(models.User.username == user.username).first()
        if db_user:
            raise HTTPException(status_code=400, detail="Username already registered")
        hashed_password = auth.get_password_hash(user.password)
        new_user = models.User(username=user.username, hashed_password=hashed_password)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    except HTTPException:
        raise
    except SQLAlchemyError:
        logger.exception("Database error during registration")
        raise HTTPException(status_code=503, detail="Database unavailable")

@app.post("/token", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    try:
        user = db.query(models.User).filter(models.User.username == form_data.username).first()
        if not user or not auth.verify_password(form_data.password, user.hashed_password):
            raise HTTPException(status_code=400, detail="Incorrect username or password")

        access_token_expires = auth.timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = auth.create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}
    except HTTPException:
        raise
    except SQLAlchemyError:
        logger.exception("Database error during login")
        raise HTTPException(status_code=503, detail="Database unavailable")

@app.post("/chat", response_model=schemas.ChatResponse)
def chat_transaction(request: schemas.ChatRequest, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        system_prompt = (
            "You are a helpful financial assistant. "
            "Always reply in plain JSON with two keys: "
            "'reply' (your friendly text response) and "
            "'extracted_transaction' (null if no money mentioned, otherwise an object with "
            "'amount' as a number, 'category' as a string, 'description' as a string, "
            "and 'type' as either 'expense' or 'income'). "
            "Output raw JSON only, no markdown."
        )
        response = client.chat.completions.create(
            model=META_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": request.message}
            ]
        )
        message_content = response.choices[0].message.content or ""
        if not message_content.strip():
            raise HTTPException(status_code=502, detail="AI provider returned an empty response")

        try:
            extracted_data = _extract_json(message_content)
        except json.JSONDecodeError:
            logger.exception("AI response was not valid JSON")
            raise HTTPException(status_code=502, detail="AI provider returned invalid JSON")
        
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
    except SQLAlchemyError:
        logger.exception("Database error during chat")
        raise HTTPException(status_code=503, detail="Database unavailable")
    except Exception as e:
        logger.exception("Chat processing failed")
        raise HTTPException(status_code=503, detail=f"AI provider error: {str(e)}")

@app.get("/dashboard")
def get_dashboard(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    from sqlalchemy import func
    
    # Calculate totals using DB aggregates
    try:
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
    except SQLAlchemyError:
        logger.exception("Database error while loading dashboard")
        raise HTTPException(status_code=503, detail="Database unavailable")

@app.post("/budgets", response_model=schemas.BudgetResponse)
def create_budget(budget: schemas.BudgetCreate, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        new_budget = models.Budget(
            category=budget.category,
            limit_amount=budget.limit_amount,
            owner_id=current_user.id
        )
        db.add(new_budget)
        db.commit()
        db.refresh(new_budget)
        return new_budget
    except SQLAlchemyError:
        logger.exception("Database error during budget creation")
        raise HTTPException(status_code=503, detail="Database unavailable")

@app.get("/budgets", response_model=list[schemas.BudgetResponse])
def get_budgets(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        return db.query(models.Budget).filter(models.Budget.owner_id == current_user.id).all()
    except SQLAlchemyError:
        logger.exception("Database error while loading budgets")
        raise HTTPException(status_code=503, detail="Database unavailable")

@app.post("/upload-screenshot", response_model=schemas.TransactionResponse)
def upload_screenshot(file: UploadFile = File(...), current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        contents = file.file.read()
        base64_image = base64.b64encode(contents).decode('utf-8')
        
        # NOTE: Meta Llama vision models on Bedrock support image inputs.
        # If your chosen model does not support vision, this endpoint will return an error.
        screenshot_prompt = (
            "Look at this UPI payment screenshot and extract the transaction. "
            "Reply with raw JSON only (no markdown) using these keys: "
            "amount (number), category (string), description (string), "
            "type ('expense' or 'income')."
        )
        response = client.chat.completions.create(
            model=META_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": screenshot_prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                }
            ]
        )
        message_content = response.choices[0].message.content or ""
        if not message_content.strip():
            raise HTTPException(status_code=502, detail="AI provider returned an empty response")

        try:
            extracted_data = _extract_json(message_content)
        except json.JSONDecodeError:
            logger.exception("AI response was not valid JSON for screenshot extraction")
            raise HTTPException(status_code=502, detail="AI provider returned invalid JSON")
        
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
    except SQLAlchemyError:
        logger.exception("Database error during screenshot processing")
        raise HTTPException(status_code=503, detail="Database unavailable")
    except Exception as e:
        logger.exception("Screenshot processing failed")
        raise HTTPException(status_code=503, detail=f"AI provider error: {str(e)}")
