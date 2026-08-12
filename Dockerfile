FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend folder into /app/backend
COPY backend/ /app/backend/

# Render injects $PORT dynamically; fallback to 8000 for local dev
EXPOSE 8000

# Use shell form so $PORT is expanded at runtime
CMD uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}
