FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy NLQ service code
COPY . .

# Set environment variables
ENV PYTHONPATH=/app
ENV DB_HOST=dev-postgres-db
ENV DB_PORT=5432
ENV DB_NAME=postgres
ENV DB_USER=postgres
ENV DB_PASSWORD=postgres
ENV LLM_PROVIDER=openai
ENV LLM_MODEL=gpt-4o-mini

# Expose API port
EXPOSE 8000

# Run the API server
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
