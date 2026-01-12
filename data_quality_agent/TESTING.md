# Data Quality Agent Testing Guide

## Quick Test Results

✅ **Database Connection**: Working
- Successfully connects to PostgreSQL
- Found 3 tables: `production_data`, `wells_data`, `wellbores_data`

✅ **Quality Checks**: Working
- Missing values detection works
- Duplicate detection works
- Value range validation works

✅ **Agent Tools**: Working
- Table investigation works
- Column investigation works
- Sample data retrieval works

✅ **Agent Workflow**: Working
- Quality check execution works
- Issue investigation works
- Report generation works (without LLM)

⚠️ **LLM Reasoning**: Requires API key configuration

## Testing Methods

### 1. Test Database Connection

```bash
docker-compose run --rm dev-data-quality-agent python -c \
  "import sys; sys.path.insert(0, '/app'); from database import get_db_manager; \
   db = get_db_manager(); print('Tables:', db.get_all_tables())"
```

### 2. Test Quality Checks

```bash
docker-compose run --rm dev-data-quality-agent python -c \
  "import sys; sys.path.insert(0, '/app'); \
   from quality_checks import DataQualityChecker; \
   from database import get_db_manager; \
   db = get_db_manager(); \
   checker = DataQualityChecker(db); \
   issues = checker.check_missing_values('production_data', ['wellbore']); \
   print(f'Found {len(issues)} issues')"
```

### 3. Test Agent Tools

```bash
docker-compose run --rm dev-data-quality-agent python -c \
  "import sys; sys.path.insert(0, '/app'); from agent_tools import AgentTools; \
   tools = AgentTools(); \
   result = tools.investigate_table('production_data'); \
   print(f'Issues found: {result[\"issues_found\"]}')"
```

### 4. Test Agent Workflow

```bash
docker-compose run --rm dev-data-quality-agent python -c \
  "import sys; sys.path.insert(0, '/app'); from agent import DataQualityAgent; \
   agent = DataQualityAgent(); \
   results = agent.run_quality_check(); \
   print(f'Total issues: {results[\"total_issues\"]}')"
```

### 5. Test API Endpoints

```bash
# Start service
docker-compose up -d dev-data-quality-agent

# Test health
curl http://localhost:8001/health

# Test quick check
curl http://localhost:8001/check/quick

# Test full check (without LLM)
curl -X POST "http://localhost:8001/check" \
  -H "Content-Type: application/json" \
  -d '{"include_llm_reasoning": false, "investigate_issues": true}'
```

### 6. Test with LLM Reasoning

```bash
# Set API key
export LLM_API_KEY=sk-your-key

# Start service with API key
LLM_API_KEY=sk-your-key docker-compose up dev-data-quality-agent

# Test full check with LLM
curl -X POST "http://localhost:8001/check" \
  -H "Content-Type: application/json" \
  -d '{"include_llm_reasoning": true, "investigate_issues": true}'
```

## Expected Behavior

- ✅ Service starts without errors
- ✅ Database connection succeeds
- ✅ Quality checks execute correctly
- ✅ Agent tools work
- ✅ API endpoints respond correctly
- ✅ LLM reasoning works (with API key)
- ✅ Reports are generated

## Troubleshooting

**Service won't start:**
- Check database is running: `docker-compose ps dev-postgres-db`
- Verify environment variables are set
- Check logs: `docker-compose logs dev-data-quality-agent`

**Quality checks failing:**
- Ensure database has data (run Luigi workflow first)
- Check database schema matches expected structure
- Verify table and column names are correct

**LLM reasoning not working:**
- Verify LLM_API_KEY is set
- Check API key is valid
- Verify LLM_PROVIDER is correct
- For Ollama: ensure it's running locally

**Agent tools errors:**
- Check database connection
- Verify table/column names exist
- Review tool implementation

## Next Steps

Once basic testing passes:
1. Test with actual LLM API (set API key)
2. Test error handling with invalid inputs
3. Test performance with large datasets
4. Add integration tests for each endpoint
5. Test report generation quality
