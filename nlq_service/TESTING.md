# NLQ Service Testing Guide

## Quick Test Results

✅ **Database Connection**: Working
- Successfully connects to PostgreSQL
- Found 3 tables: `production_data`, `wells_data`, `wellbores_data`
- Schema context generation works

✅ **SQL Validator**: Working
- Blocks dangerous queries (DROP, DELETE, etc.)
- Allows safe SELECT queries
- SQL sanitization works

✅ **API Module**: Working (when run as service)

⚠️ **LLM Client**: Requires API key configuration

## Testing Methods

### 1. Test Database Connection

```bash
docker-compose run --rm dev-nlq-service python -c \
  "import sys; sys.path.insert(0, '/app'); from database import get_db_manager; \
   db = get_db_manager(); print('Tables:', db.get_all_tables())"
```

### 2. Test SQL Validator

```bash
docker-compose run --rm dev-nlq-service python -c \
  "import sys; sys.path.insert(0, '/app'); from sql_validator import SQLValidator; \
   is_valid, error = SQLValidator.validate_query('SELECT * FROM production_data LIMIT 10'); \
   print('Valid:', is_valid)"
```

### 3. Test API Startup

```bash
# Start the service
docker-compose up -d dev-nlq-service

# Check health
curl http://localhost:8000/health
```

### 4. Test Full Query Flow

```bash
# Set API key first
export LLM_API_KEY=sk-your-key

# Start service with API key
LLM_API_KEY=sk-your-key docker-compose up dev-nlq-service

# In another terminal, test query
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How many wells are in the database?",
    "include_explanation": true,
    "max_results": 10
  }'
```

### 5. Test SQL Validation Endpoint

```bash
curl -X POST "http://localhost:8000/validate-sql?sql=SELECT * FROM production_data LIMIT 10"
```

### 6. Test Schema Endpoint

```bash
curl http://localhost:8000/schema
```

## Integration Testing

### Test with Python

```python
import requests

# Health check
response = requests.get("http://localhost:8000/health")
print(response.json())

# Ask a question
response = requests.post(
    "http://localhost:8000/query",
    json={
        "question": "What wells produced the most oil?",
        "max_results": 5
    }
)
print(response.json())
```

### Test with curl

```bash
# Simple question
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"question": "List all wells", "max_results": 10}'
```

## Expected Behavior

- ✅ Service starts without errors
- ✅ Database connection succeeds
- ✅ SQL validator blocks dangerous queries
- ✅ API endpoints respond correctly
- ✅ LLM generates SQL (with API key)
- ✅ Error handling works for invalid inputs

## Troubleshooting

**Service won't start:**
- Check database is running: `docker-compose ps dev-postgres-db`
- Verify environment variables are set
- Check logs: `docker-compose logs dev-nlq-service`

**LLM errors:**
- Verify LLM_API_KEY is set
- Check API key is valid
- Verify LLM_PROVIDER is correct
- For Ollama: ensure it's running locally

**SQL generation issues:**
- Ensure database has data (run Luigi workflow first)
- Check database schema matches expected structure
- Review LLM prompt in logs

**Connection issues:**
- Verify the database is healthy: `docker-compose ps`
- Test database connection manually
- Check network connectivity between containers

## Next Steps

Once basic testing passes:
1. Test with actual LLM API (set API key)
2. Test error handling with invalid questions
3. Test performance with complex queries
4. Add integration tests for each endpoint
