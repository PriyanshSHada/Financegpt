# FinanceGPT

FinanceGPT is an Android-first personal finance app with a FastAPI backend. It combines natural-language transaction tracking, budget management, dashboard analytics, and screenshot-based expense extraction into one workflow.

The guiding idea is simple: tell FinanceGPT where money went once, and it remembers it.

## What it does

- Track expenses and income from chat messages
- Extract transaction details from UPI or payment screenshots
- Show a financial dashboard with income, expense, balance, and category breakdowns
- Create and monitor budgets by category
- Authenticate users with JWT-based login and registration
- Store all financial records in PostgreSQL

## Tech Stack

- Android: Kotlin, Jetpack Compose, Retrofit, OkHttp
- Backend: FastAPI, SQLAlchemy, Pydantic, Uvicorn
- Database: PostgreSQL
- Auth: JWT
- AI: AWS Bedrock with Meta Llama via an OpenAI-compatible API

## Repository Layout

```text
.
├── android-app/        # Android app source
├── backend/            # FastAPI backend
├── Dockerfile          # Backend container image
├── render.yaml         # Render deployment config
├── .env.example        # Backend environment template
└── PLAN.md             # Implementation notes and project plan
```

## Key Features

### Chat-based transaction tracking
Users can type messages like:

- `Spent 120 on chai`
- `Received 25000 salary`

The backend sends the message to the AI model, parses the JSON response, and stores the transaction if one is detected.

### Screenshot upload
The Android app can pick a screenshot from the gallery and upload it to the backend, which attempts to extract:

- amount
- category
- description
- transaction type

### Dashboard
The dashboard shows:

- total balance
- total income
- total expense
- number of transactions
- per-category expense totals
- active budgets with progress indicators

### Budgets
Users can create category budgets and compare them against spending in the dashboard.

## Backend API

The FastAPI backend exposes these main endpoints:

- `POST /register` - create a new user
- `POST /token` - log in and get a JWT access token
- `POST /chat` - send a finance message to the AI assistant
- `GET /dashboard` - fetch totals and category breakdowns
- `POST /budgets` - create a budget
- `GET /budgets` - list budgets for the current user
- `POST /upload-screenshot` - upload a payment screenshot for extraction

## Environment Variables

Copy `.env.example` to `.env` and fill in the values:

```bash
DATABASE_URL=postgresql://user:password@host:5432/dbname
BEDROCK_API_BASE=https://bedrock-mantle.us-east-1.api.aws/v1
BEDROCK_API_KEY=your_bedrock_api_key
META_MODEL=meta.llama3-3-70b-instruct-v1:0
SECRET_KEY=replace_with_random_hex_string
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

## Local Backend Setup

### 1. Create and activate a virtual environment

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file in `backend/` or the project root and set the variables above.

### 4. Run the API

```bash
uvicorn backend.main:app --reload
```

The API will be available at:

- `http://127.0.0.1:8000`
- OpenAPI docs: `http://127.0.0.1:8000/docs`

## Android App Setup

### 1. Open the project in Android Studio

Open the `android-app/` directory as an Android Studio project.

### 2. Sync Gradle

Let Android Studio download the Gradle and Compose dependencies.

### 3. Point the app to the backend

The app currently uses a production backend URL inside:

- `android-app/app/src/main/java/com/example/financegpt/network/RetrofitClient.kt`

If you want to run against a local backend, update `BASE_URL` to your machine or emulator target, for example:

- Android emulator: `http://10.0.2.2:8000/`
- Physical device: your computer's LAN IP with port `8000`

### 4. Run the app

Build and launch the `android-app` module from Android Studio.

## Backend Container

The repository includes a `Dockerfile` for the backend. It installs the Python dependencies from `backend/requirements.txt` and starts Uvicorn.

## Deployment

There is a `render.yaml` file configured for Render deployment of the backend. It expects:

- `DATABASE_URL`
- `BEDROCK_API_KEY`
- `SECRET_KEY`
- `ALGORITHM`
- `ACCESS_TOKEN_EXPIRE_MINUTES`

## Notes

- The backend uses SQLAlchemy to create tables on startup.
- Transaction amounts and dashboard totals are computed from the database, not invented by the AI.
- The AI is used for extraction, classification, and natural-language responses.

## Contributing

If you add new API endpoints or Android screens, please update this README so the setup and feature list stay accurate.
