# Testing Guide: Predictive Maintenance Agent

This guide provides comprehensive testing instructions for the Predictive Maintenance Agent.

## Test Environment Setup

### Prerequisites

- Docker and Docker Compose installed
- PostgreSQL database running
- Production data loaded
- LLM API key (optional, for LLM features)

### Start Services

```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f dev-predictive-maintenance-agent
```

## Test Levels

### Level 1: Component Tests

Test individual components in isolation.

#### Test 1.1: Database Connection

```bash
docker-compose run --rm dev-predictive-maintenance-agent python -c "
import sys
sys.path.insert(0, '/app')
from database import get_db_manager

db = get_db_manager()
tables = db.execute_query('SELECT table_name FROM information_schema.tables WHERE table_schema = \\'public\\'')
print('✅ Database connected')
print(f'Tables: {[t[\"table_name\"] for t in tables]}')
"
```

**Expected**: Database connection successful, maintenance_work_orders table exists.

#### Test 1.2: Predictive Models

```bash
docker-compose run --rm dev-predictive-maintenance-agent python -c "
import sys
sys.path.insert(0, '/app')
from database import get_db_manager
from predictive_models import PredictiveModel

db = get_db_manager()
model = PredictiveModel(db)

# Get first well
wells = db.execute_query('''
    SELECT DISTINCT wb.well_legal_name
    FROM production_data p
    LEFT JOIN wellbores_data wb ON p.wellbore = wb.wellbore_name
    WHERE wb.well_legal_name IS NOT NULL
    LIMIT 1
''')

if wells:
    well_name = wells[0]['well_legal_name']
    predictions = model.analyze_well(well_name, days=90)
    print(f'✅ Predictive model working')
    print(f'Well: {well_name}')
    print(f'Predictions: {len(predictions)}')
    for p in predictions:
        print(f'  - {p.maintenance_type.value}: {p.priority.value} (confidence: {p.confidence_score})')
else:
    print('⚠️  No wells found')
"
```

**Expected**: Predictive model analyzes well and generates predictions.

#### Test 1.3: Maintenance Scheduler

```bash
docker-compose run --rm dev-predictive-maintenance-agent python -c "
import sys
sys.path.insert(0, '/app')
from maintenance_scheduler import MaintenanceScheduler

scheduler = MaintenanceScheduler()
upcoming = scheduler.get_upcoming_maintenance(days=30)
print(f'✅ Scheduler working')
print(f'Upcoming maintenance: {len(upcoming)}')
"
```

**Expected**: Scheduler retrieves upcoming maintenance.

#### Test 1.4: Agent Tools

```bash
docker-compose run --rm dev-predictive-maintenance-agent python -c "
import sys
sys.path.insert(0, '/app')
from agent_tools import AgentTools

tools = AgentTools()
wells = tools.get_well_list()
print(f'✅ Agent tools working')
print(f'Wells found: {len(wells)}')
"
```

**Expected**: Agent tools retrieve well list.

### Level 2: Integration Tests

Test components working together.

#### Test 2.1: Full Analysis Workflow

```bash
docker-compose run --rm dev-predictive-maintenance-agent python -c "
import sys
sys.path.insert(0, '/app')
from agent import PredictiveMaintenanceAgent

agent = PredictiveMaintenanceAgent()
result = agent.analyze_and_schedule(
    well_legal_name=None,
    include_llm_reasoning=False,
    auto_schedule=True
)

print(f'✅ Full workflow completed')
print(f'Wells analyzed: {result[\"wells_analyzed\"]}')
print(f'Total predictions: {result[\"total_predictions\"]}')
print(f'Work orders created: {result[\"work_orders_created\"]}')
"
```

**Expected**: Complete workflow executes, work orders created.

#### Test 2.2: Work Order Creation

```bash
docker-compose run --rm dev-predictive-maintenance-agent python -c "
import sys
sys.path.insert(0, '/app')
from database import get_db_manager

db = get_db_manager()
work_orders = db.get_work_orders(status='scheduled', limit=10)
print(f'✅ Work orders retrieved')
print(f'Count: {len(work_orders)}')
for wo in work_orders[:3]:
    print(f'  - WO {wo[\"work_order_id\"]}: {wo[\"well_legal_name\"]} - {wo[\"priority\"]}')
"
```

**Expected**: Work orders retrieved from database.

### Level 3: API Tests

Test REST API endpoints.

#### Test 3.1: Health Check

```bash
curl http://localhost:8003/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "tables": 4
}
```

#### Test 3.2: Analyze Endpoint (No LLM)

```bash
curl -X POST http://localhost:8003/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "well_legal_name": null,
    "include_llm_reasoning": false,
    "auto_schedule": true
  }'
```

**Expected**: Analysis completed, work orders created.

#### Test 3.3: Analyze Specific Well

```bash
curl -X POST http://localhost:8003/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "well_legal_name": "15/9-F-1",
    "include_llm_reasoning": false,
    "auto_schedule": true
  }'
```

**Expected**: Specific well analyzed.

#### Test 3.4: Get Schedule

```bash
curl "http://localhost:8003/schedule?days_ahead=90"
```

**Expected**: Maintenance schedules returned.

#### Test 3.5: Get Work Orders

```bash
curl "http://localhost:8003/work-orders?status=scheduled"
```

**Expected**: Work orders returned.

#### Test 3.6: Get Work Orders by Well

```bash
curl "http://localhost:8003/work-orders?well_legal_name=15/9-F-1"
```

**Expected**: Work orders for specific well returned.

### Level 4: LLM Integration Tests

Test LLM features (requires API key).

#### Test 4.1: Analysis with LLM Reasoning

```bash
# Set API key
export LLM_API_KEY=sk-your-key-here

# Restart service
docker-compose restart dev-predictive-maintenance-agent

# Test with LLM
curl -X POST http://localhost:8003/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "well_legal_name": "15/9-F-1",
    "include_llm_reasoning": true,
    "auto_schedule": true
  }'
```

**Expected**: Analysis includes LLM reasoning and report.

### Level 5: End-to-End Tests

Test complete user workflows.

#### Test 5.1: Complete Maintenance Workflow

```bash
# Step 1: Analyze all wells
curl -X POST http://localhost:8003/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "well_legal_name": null,
    "include_llm_reasoning": true,
    "auto_schedule": true
  }' > analysis_result.json

# Step 2: Get schedule
curl "http://localhost:8003/schedule?days_ahead=90" > schedule.json

# Step 3: Get work orders
curl "http://localhost:8003/work-orders?status=scheduled" > work_orders.json

# Verify results
echo "Analysis completed"
cat analysis_result.json | jq '.work_orders_created'
cat schedule.json | jq '.schedules_count'
cat work_orders.json | jq '.count'
```

**Expected**: Complete workflow executes, all endpoints return data.

## Test Script

Run all tests using the simple test script:

```bash
docker-compose run --rm dev-predictive-maintenance-agent python test_simple.py
```

**Expected Output:**
```
==================================================
Predictive Maintenance Agent - Simple Tests
==================================================
Testing database connection...
✅ Database connected. Found 4 tables

Testing predictive model...
✅ Predictive model working. Found 2 predictions for 15/9-F-1

Testing agent tools...
✅ Agent tools working. Found 5 wells

Testing maintenance scheduler...
✅ Scheduler working. Found 3 upcoming maintenance items

==================================================
Tests passed: 4/4
==================================================
```

## Troubleshooting

### Database Connection Errors

**Error**: `Connection refused` or `database does not exist`

**Solution**:
- Verify PostgreSQL is running: `docker-compose ps dev-postgres-db`
- Check database credentials in environment variables
- Ensure maintenance_work_orders table exists

### No Predictions Generated

**Error**: `predictions_count: 0`

**Solution**:
- Verify production data exists
- Check that at least 30 days of data is available
- Ensure well_legal_name matches database

### LLM API Errors

**Error**: `LLM API error` or `Invalid API key`

**Solution**:
- Verify API key is set: `echo $LLM_API_KEY`
- Check LLM provider configuration
- Ensure Ollama is running if using local models

### Work Orders Not Created

**Error**: `work_orders_created: 0`

**Solution**:
- Check if predictions were generated
- Verify auto_schedule is true
- Check for duplicate work orders (within 30 days)

## Performance Testing

### Load Test

```bash
# Run multiple analyses
for i in {1..10}; do
  curl -X POST http://localhost:8003/analyze \
    -H "Content-Type: application/json" \
    -d '{"well_legal_name": null, "include_llm_reasoning": false, "auto_schedule": true}' &
done
wait
```

### Response Time Test

```bash
time curl -X POST http://localhost:8003/analyze \
  -H "Content-Type: application/json" \
  -d '{"well_legal_name": "15/9-F-1", "include_llm_reasoning": false, "auto_schedule": true}'
```

**Expected**: Response time < 5 seconds (without LLM)

## Test Coverage

### Components Tested

- ✅ Database connection and queries
- ✅ Predictive models (decline, anomaly, age)
- ✅ Agent tools (analysis, comparison)
- ✅ Maintenance scheduler
- ✅ LLM integration (reasoning, reporting)
- ✅ REST API endpoints
- ✅ Work order creation and retrieval

### Scenarios Tested

- ✅ Single well analysis
- ✅ All wells analysis
- ✅ Work order creation
- ✅ Schedule retrieval
- ✅ Work order filtering
- ✅ LLM reasoning (with API key)
- ✅ Report generation

## Next Steps

After testing, you can:
- Integrate with actual SAP PM systems
- Add more sophisticated predictive models
- Implement maintenance cost estimation
- Add resource allocation optimization
- Track maintenance effectiveness
