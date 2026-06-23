# FinanceGPT v3 Implementation Plan (Android-First Architecture)

## Vision
**FinanceGPT** is an AI Financial Operating System that remembers every transaction, understands spending behavior, analyzes financial habits, tracks budgets, and imports data natively on Android.

Goal: "Tell FinanceGPT where money went once, and it remembers everything forever."

---

## Zero-Hallucination Architecture
**Rule:** AI Never Invents Numbers.
All calculations come from PostgreSQL. GPT is used exclusively to:
1. Extract data (NLP / OCR)
2. Categorize expenses
3. Explain insights

---

## Tech Stack
- **Frontend:** Android Native (Kotlin + Jetpack Compose)
- **Backend:** FastAPI (Python)
- **Database:** PostgreSQL (with SQLAlchemy)
- **Authentication:** JWT Auth
- **AI Engine:** GPT-4o Mini (via OpenAI API)

---

## MVP Focus Areas (Phase 1)
1. **Chat Expense Tracking**
   - User types: "Spent ₹120 on chai"
   - Backend calls GPT-4o Mini -> extracts JSON -> saves to PostgreSQL.
2. **Income Tracking**
   - Natural language input for tracking income.
3. **Dashboard Analytics**
   - Visualizations generated purely from database records.
4. **UPI Screenshot Scanner**
   - Use OpenAI Vision or OCR to parse screenshot text and automatically save the expense.
5. **Budget Tracking**
   - Smart budgets with percentage warnings.

---

## Folder Structure
```text
c:\Project\finance gpt\
├── android-app/            # Kotlin + Jetpack Compose Android Project
├── backend/                # Python FastAPI Server
│   ├── .env                # API Keys & DB Config
│   ├── main.py             # FastAPI App & Endpoints
│   ├── models.py           # SQLAlchemy Database Models
│   ├── schemas.py          # Pydantic validation schemas
│   ├── database.py         # DB connection setup
│   └── auth.py             # JWT logic
└── PLAN.md                 # This file
```

---

## Next Steps for Execution (Completed)
- [x] Clean up old Next.js files
- [x] Initialize FastAPI environment and Database connection
- [x] Build FastAPI Models and Endpoints (Chat, Dashboard, Auth)
- [x] Initialize Android Jetpack Compose Project
- [x] Connect Android UI to FastAPI Backend
- [x] Test the End-to-End Chat extraction flow
- [x] Build Dashboard UI
- [x] Build UPI Screenshot Scanner UI

## Phase 2 (Current Focus)
- [ ] Build Login & Registration UI on Android (replacing dummy token)
- [ ] Build Budget Tracking UI (view budgets, progress bars, and percentage warnings)
- [ ] Implement Income vs Expense visual charts on the Dashboard
