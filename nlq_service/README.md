# Natural Language Query Service

A REST API service that converts natural language questions to SQL queries using LLMs and executes them safely against the Volve Wells database.

## Overview

The Natural Language Query (NLQ) service provides a user-friendly interface for querying the Volve Wells database using natural language. It leverages Large Language Models (LLMs) to convert questions like "What wells produced the most oil last year?" into SQL queries, validates them for safety, and returns results in a structured format.

## Features

- 🤖 **LLM-Powered SQL Generation**: Converts natural language to SQL using OpenAI, Anthropic Claude, or local models (Ollama)
- 🔒 **SQL Validation**: Ensures generated queries are safe (read-only, no dangerous operations)
- 📊 **Database Schema Context**: Uses RAG (Retrieval Augmented Generation) with database schema for accurate SQL generation
- 🚀 **REST API**: Easy-to-use HTTP endpoints for integration
- ⚡ **Fast Execution**: Validates and executes queries efficiently
- 📝 **Query Explanations**: Optional explanations of generated SQL queries

## Architecture

```
User Question
    ↓
LLM Client (OpenAI/Anthropic/Ollama)
    ↓
SQL Generation
    ↓
SQL Validator (Safety Check)
    ↓
Database Execution
    ↓
Results + Explanation
```

## API Endpoints

### POST `/query`

Convert natural language to SQL and execute it.

**Request:**
```json
{
  "question": "What wells produced the most oil in 2016?",
  "include_explanation": true,
  "max_results": 10
}
```

**Response:**
```json
{
  "question": "What wells produced the most oil in 2016?",
  "sql": "SELECT wellbore, SUM(boreoilvol) as total_oil FROM production_data WHERE productiontime >= '2016-01-01' AND productiontime < '2017-01-01' GROUP BY wellbore ORDER BY total_oil DESC LIMIT 10",
  "explanation": "This query finds wells with highest oil production in 2016...",
  "results": [...],
  "row_count": 10,
  "execution_time_ms": 45.2,
  "model_info": {
    "provider": "openai",
    "model": "gpt-4o-mini"
  }
}
```

### POST `/validate-sql`

Validate a SQL query without executing it.

**Request:**
```
POST /validate-sql?sql=SELECT * FROM production_data LIMIT 10
```

**Response:**
```json
{
  "is_valid": true,
  "error_message": null,
  "sanitized_sql": "SELECT * FROM production_data LIMIT 10"
}
```

### GET `/schema`

Get database schema information.

**Response:**
```json
{
  "tables": {
    "production_data": [
      {"name": "productiontime", "type": "timestamp", "nullable": true},
      {"name": "wellbore", "type": "text", "nullable": true},
      ...
    ],
    ...
  },
  "table_count": 3
}
```

### GET `/health`

Health check endpoint.

## Setup

### Prerequisites

- Python 3.11+
- PostgreSQL database (running via docker-compose)
- LLM API key (OpenAI, Anthropic, or Ollama running locally)

### Environment Variables

```bash
# Database (set automatically in docker-compose)
DB_HOST=dev-postgres-db
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=postgres

# LLM Configuration
LLM_PROVIDER=openai  # Options: openai, anthropic, ollama
LLM_API_KEY=sk-...   # Your API key
LLM_MODEL=gpt-4o-mini # Model name
LLM_BASE_URL=        # Optional: for custom endpoints (e.g., Ollama)
```

### Using Docker (Recommended)

The NLQ service is included in docker-compose:

```bash
# Set your LLM API key
export LLM_API_KEY=sk-your-key-here
export LLM_PROVIDER=openai  # or anthropic, ollama

# Build and start
docker-compose build dev-nlq-service
docker-compose up dev-nlq-service
```

The API will be available at: http://localhost:8000

### Local Development

```bash
cd nlq_service
pip install -r requirements.txt

# Set environment variables
export LLM_API_KEY=sk-your-key-here
export LLM_PROVIDER=openai

# Run the service
uvicorn api:app --host 0.0.0.0 --port 8000
```

## Usage Examples

### Using curl

```bash
# Ask a question
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Which wellbore had the highest gas production?",
    "include_explanation": true,
    "max_results": 5
  }'

# Get database schema
curl "http://localhost:8000/schema"

# Validate SQL
curl -X POST "http://localhost:8000/validate-sql?sql=SELECT * FROM production_data LIMIT 10"
```

### Using Python

```python
import requests

# Ask a question
response = requests.post(
    "http://localhost:8000/query",
    json={
        "question": "What is the average oil production per well?",
        "include_explanation": True,
        "max_results": 100
    }
)

result = response.json()
print(f"SQL: {result['sql']}")
print(f"Results: {result['results']}")
print(f"Explanation: {result['explanation']}")
```

### Using JavaScript/TypeScript

```typescript
const response = await fetch('http://localhost:8000/query', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    question: 'Show me wells with declining production',
    include_explanation: true,
    max_results: 20
  })
});

const result = await response.json();
console.log('SQL:', result.sql);
console.log('Results:', result.results);
```

## Supported LLM Providers

### OpenAI

```bash
export LLM_PROVIDER=openai
export LLM_API_KEY=sk-...
export LLM_MODEL=gpt-4o-mini  # or gpt-4, gpt-3.5-turbo
```

### Anthropic Claude

```bash
export LLM_PROVIDER=anthropic
export LLM_API_KEY=sk-ant-...
export LLM_MODEL=claude-3-5-sonnet-20241022
```

### Ollama (Local)

```bash
# Start Ollama locally
ollama serve

# Configure service
export LLM_PROVIDER=ollama
export LLM_BASE_URL=http://localhost:11434/v1
export LLM_MODEL=llama3.1
export LLM_API_KEY=ollama  # Not used, but required
```

## Security

The service includes multiple security layers:

1. **SQL Validation**: Only SELECT queries are allowed
2. **Keyword Filtering**: Blocks dangerous SQL keywords (DROP, DELETE, etc.)
3. **Pattern Detection**: Detects SQL injection patterns
4. **Query Sanitization**: Removes comments and normalizes queries
5. **Read-Only Mode**: No write operations permitted

## Error Handling

The service provides detailed error messages:

- **400 Bad Request**: Invalid SQL generated or validation failed
- **500 Internal Server Error**: LLM API errors, database connection issues
- **503 Service Unavailable**: Health check failures

## Performance

- Typical query time: 1-3 seconds (includes LLM generation + execution)
- LLM generation: ~0.5-2 seconds (depends on provider)
- Database execution: ~0.01-0.1 seconds
- Results are limited to 1000 rows by default (configurable)

## Troubleshooting

**LLM API errors:**
- Verify API key is set correctly
- Check API quota/rate limits
- Ensure model name is correct for provider

**SQL generation issues:**
- Check database schema is accessible
- Verify LLM has proper context
- Review generated SQL in error messages

**Database connection errors:**
- Ensure PostgreSQL is running
- Verify environment variables
- Check network connectivity

## Development

### Project Structure

```
nlq_service/
├── __init__.py
├── api.py              # FastAPI application
├── database.py          # Database connection utilities
├── llm_client.py       # LLM integration (OpenAI/Anthropic/Ollama)
├── sql_validator.py    # SQL safety validation
├── Dockerfile
├── requirements.txt
└── README.md
```

### Adding New Features

1. **Custom LLM Prompts**: Modify `llm_client.py` to customize SQL generation
2. **Additional Validation**: Extend `sql_validator.py` for more security rules
3. **Query Caching**: Add caching layer for frequently asked questions
4. **Rate Limiting**: Add rate limiting middleware

## Next Steps

This NLQ service can be extended with:
- Query result caching
- Query history and analytics
- User authentication
- Rate limiting
- Query optimization suggestions
- Integration with the MCP server

## License

Same as the main project.
