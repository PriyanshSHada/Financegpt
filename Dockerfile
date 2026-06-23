FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend folder into /app/backend
COPY backend/ /app/backend/

# Expose the port Northflank will route traffic to
EXPOSE 8000

# Command to run the FastAPI application as a module
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
