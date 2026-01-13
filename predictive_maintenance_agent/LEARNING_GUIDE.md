# Learning Guide: Predictive Maintenance Agent (Advanced Agentic AI)

## Table of Contents
1. [What is Predictive Maintenance?](#what-is-predictive-maintenance)
2. [Agentic AI for Maintenance](#agentic-ai-for-maintenance)
3. [Technical Implementation](#technical-implementation)
4. [Step-by-Step Implementation](#step-by-step-implementation)
5. [Technical Implementation Details](#technical-implementation-details)
6. [Testing the Predictive Maintenance Agent](#testing-the-predictive-maintenance-agent)
7. [Key Concepts and Learning Outcomes](#key-concepts-and-learning-outcomes)

---

## What is Predictive Maintenance?

### Definition

**Predictive Maintenance** is a maintenance strategy that uses data analysis, statistical models, and machine learning to predict when equipment failure might occur, enabling maintenance to be scheduled before failures happen.

### Maintenance Types

1. **Preventive Maintenance**: Scheduled maintenance based on time or usage intervals
2. **Corrective Maintenance**: Maintenance performed after failure occurs
3. **Predictive Maintenance**: Maintenance scheduled based on predicted failure dates from data analysis

### Benefits

- Reduces unplanned downtime
- Optimizes maintenance scheduling
- Extends equipment lifespan
- Reduces maintenance costs
- Improves safety

---

## Agentic AI for Maintenance

### Definition

An **Agentic AI system** for maintenance is an autonomous agent that:
1. Analyzes production data patterns
2. Uses predictive models to identify maintenance needs
3. Reasons about maintenance priorities and scheduling
4. Creates and manages maintenance work orders
5. Generates strategic maintenance plans

### Architecture

```
Production Data
    ↓
Predictive Models
    ↓
Agent Tools (Investigation)
    ↓
LLM Reasoning (Strategy)
    ↓
Maintenance Scheduler
    ↓
Work Orders (SAP PM Simulation)
```

---

## Technical Implementation

### System Components

1. **Predictive Models**: Statistical analysis of production data
2. **Agent Tools**: Investigation and analysis tools
3. **LLM Client**: Strategic reasoning and report generation
4. **Maintenance Scheduler**: Work order creation and management
5. **Database Manager**: SAP PM simulation via database table
6. **REST API**: FastAPI endpoints for interaction

### Data Flow

1. Production data retrieved from database
2. Statistical analysis performed (decline, anomalies, age)
3. Predictions generated with confidence scores
4. Agent tools investigate wells and compare priorities
5. LLM analyzes strategy and provides recommendations
6. Scheduler creates work orders in database
7. Report generated with maintenance plan

---

## Step-by-Step Implementation

### Step 1: Database Schema (SAP PM Simulation)

**Table: `maintenance_work_orders`**

```sql
CREATE TABLE maintenance_work_orders (
    work_order_id SERIAL PRIMARY KEY,
    well_legal_name VARCHAR(255) NOT NULL,
    wellbore_name VARCHAR(255),
    maintenance_type VARCHAR(100) NOT NULL,
    priority VARCHAR(20) NOT NULL,
    scheduled_date DATE NOT NULL,
    estimated_duration_hours DECIMAL(10,2),
    description TEXT,
    predicted_failure_date DATE,
    confidence_score DECIMAL(5,2),
    status VARCHAR(20) DEFAULT 'scheduled',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100) DEFAULT 'predictive_maintenance_agent',
    completed_at TIMESTAMP,
    notes TEXT
);
```

**Purpose**: Simulates SAP Plant Maintenance system by storing work orders with all necessary fields for maintenance planning and execution.

### Step 2: Predictive Models

**File: `predictive_models.py`**

Three predictive models analyze production data:

1. **Production Decline Detection**
   - Compares recent vs older production averages
   - Detects decline > 20%
   - Calculates confidence based on decline percentage
   - Predicts failure date based on decline rate

2. **Anomaly Detection**
   - Uses statistical analysis (mean, standard deviation)
   - Identifies values > 2 standard deviations from mean
   - Flags wells with multiple anomalies
   - Predicts maintenance need within 21 days

3. **Equipment Age Analysis**
   - Checks days since last production
   - Identifies wells with > 60 days of inactivity
   - Suggests preventive inspection
   - Low priority maintenance

**Output**: `MaintenancePrediction` objects with:
- Well identification
- Maintenance type
- Priority level
- Predicted failure date
- Confidence score (0-100)
- Reason and recommended action

### Step 3: Agent Tools

**File: `agent_tools.py`**

Tools for autonomous investigation:

- `analyze_well()`: Runs predictive models on specific well
- `get_well_list()`: Retrieves all wells from database
- `get_existing_schedules()`: Gets current maintenance schedules
- `check_maintenance_history()`: Retrieves past maintenance records
- `compare_wells()`: Prioritizes multiple wells for maintenance

**Tool Pattern**: Each tool returns structured dictionaries with investigation results, statistics, and metadata.

### Step 4: Maintenance Scheduler

**File: `maintenance_scheduler.py`**

Schedules maintenance work orders:

- Converts predictions to work orders
- Checks for existing similar work orders (deduplication)
- Calculates optimal scheduled date (1 week before predicted failure)
- Adjusts schedule based on priority (critical = 3 days, high = 7 days)
- Creates work orders in database

**Scheduling Logic**:
- Target date: predicted_failure_date - 7 days
- If target in past: schedule for next week
- Priority adjustment: critical/high get scheduled sooner
- Deduplication: skips if similar work order exists within 30 days

### Step 5: LLM Integration

**File: `agent.py` - LLMClient class**

LLM reasoning for strategic analysis:

- `analyze_maintenance_strategy()`: Analyzes predictions and provides:
  - Priority assessment
  - Scheduling recommendations
  - Resource allocation suggestions
  - Risk mitigation strategies
  - Cost-benefit analysis

- `generate_maintenance_report()`: Creates markdown report with:
  - Executive summary
  - Maintenance schedule overview
  - Priority breakdown
  - Resource requirements
  - Risk assessment
  - Recommendations

**Multi-Provider Support**: OpenAI, Anthropic, Ollama (same pattern as other services)

### Step 6: Agent Orchestration

**File: `agent.py` - PredictiveMaintenanceAgent class**

Main agent workflow:

1. **Get Wells**: Retrieve wells to analyze (all or specific)
2. **Analyze**: Run predictive models on each well
3. **Reason**: Use LLM for strategic analysis (optional)
4. **Schedule**: Create work orders from predictions
5. **Report**: Generate comprehensive maintenance report

**Method**: `analyze_and_schedule()`
- Input: well_legal_name (optional), include_llm_reasoning, auto_schedule
- Output: Complete analysis with predictions, work orders, LLM analysis, and report

### Step 7: REST API

**File: `api.py`**

FastAPI endpoints:

- `POST /analyze`: Analyze wells and create schedules
- `GET /schedule`: Get maintenance schedules
- `GET /work-orders`: Get work orders with filters
- `GET /health`: Health check

**Request/Response Models**: Pydantic models for validation and OpenAPI documentation.

---

## Technical Implementation Details

### Technology Stack

**Core Dependencies:**
- `fastapi` (v0.104.0): REST API framework
- `uvicorn[standard]` (v0.24.0): ASGI server
- `sqlalchemy` (v2.0.45): Database ORM and connection pooling
- `psycopg2-binary` (v2.9.11): PostgreSQL adapter
- `openai` (v1.0.0+): OpenAI API client
- `anthropic` (v0.18.0+): Anthropic Claude API client
- `pydantic` (v2.0.0+): Data validation

**Python Version:** 3.11 (slim Docker image)

### Predictive Model Implementation

**Production Decline Detection:**
```python
def _check_production_decline(self, well_legal_name, production_data, stats):
    recent_days = min(14, len(production_data) // 2)
    recent_avg = sum(d.get("oil_prod", 0) or 0 for d in production_data[:recent_days]) / recent_days
    older_avg = sum(d.get("oil_prod", 0) or 0 for d in production_data[recent_days:recent_days*2]) / recent_days
    
    decline_percentage = ((older_avg - recent_avg) / older_avg) * 100
    
    if decline_percentage > 20:
        confidence = min(90, 50 + (decline_percentage - 20) * 2)
        days_until_failure = max(7, int(30 - decline_percentage))
        # Create MaintenancePrediction
```

Compares recent 14-day average with previous 14-day average. If decline > 20%, creates prediction with confidence score proportional to decline percentage. Failure date calculated based on decline rate.

**Anomaly Detection:**
```python
def _check_anomalies(self, well_legal_name, production_data, stats):
    avg_prod = stats.get("avg_oil_prod", 0) or 0
    stddev = stats.get("stddev_oil_prod", 0) or 0
    
    anomalies = [
        d for d in production_data[:30]
        if d.get("oil_prod") and abs((d.get("oil_prod") or 0) - avg_prod) > 2 * stddev
    ]
    
    if len(anomalies) > 3:
        # Create MaintenancePrediction
```

Uses statistical analysis: mean and standard deviation. Flags values > 2 standard deviations from mean. If > 3 anomalies in last 30 days, creates prediction.

**Equipment Age Analysis:**
```python
def _check_equipment_age(self, well_legal_name, stats):
    last_prod_date = stats.get("last_production_date")
    days_since_last_prod = (date.today() - last_prod_date).days
    
    if days_since_last_prod > 60:
        # Create MaintenancePrediction
```

Checks days since last production. If > 60 days, suggests preventive inspection.

### Database Integration

**Production Data Query:**
```python
def get_production_data(self, well_legal_name, days=90):
    query = """
        SELECT 
            p.wellbore,
            p.productiontime as date_on_production,
            p.boreoilvol as oil_prod,
            p.boregasvol as gas_prod,
            p.borewatvol as water_prod,
            p.borewivol as water_inj,
            wb.well_legal_name
        FROM production_data p
        LEFT JOIN wellbores_data wb ON p.wellbore = wb.wellbore_name
        WHERE p.productiontime >= CURRENT_DATE - INTERVAL ':days days'
    """
```

Joins `production_data` with `wellbores_data` to get `well_legal_name`. Uses parameterized queries for security.

**Work Order Creation:**
```python
def create_work_order(self, well_legal_name, wellbore_name, maintenance_type, 
                     priority, scheduled_date, estimated_duration_hours, 
                     description, predicted_failure_date, confidence_score):
    query = """
        INSERT INTO maintenance_work_orders (
            well_legal_name, wellbore_name, maintenance_type, priority,
            scheduled_date, estimated_duration_hours, description,
            predicted_failure_date, confidence_score, status
        ) VALUES (...)
        RETURNING work_order_id
    """
```

Creates work order with all required fields. Returns work_order_id for tracking.

### Agent Tools Implementation

**Tool Pattern:**
```python
class AgentTools:
    def analyze_well(self, well_legal_name: str, days: int = 90):
        predictions = self.predictive_model.analyze_well(well_legal_name, days)
        stats = self.db.get_well_statistics(well_legal_name, days)
        
        return {
            "well_legal_name": well_legal_name,
            "predictions_count": len(predictions),
            "predictions": [prediction_to_dict(p) for p in predictions],
            "statistics": stats
        }
```

Tools combine predictive models with database queries. Return structured dictionaries for LLM consumption.

**Well Comparison:**
```python
def compare_wells(self, well_names: List[str]):
    comparisons = []
    for well_name in well_names:
        analysis = self.analyze_well(well_name)
        history = self.check_maintenance_history(well_name)
        comparisons.append({
            "well_legal_name": well_name,
            "predictions_count": analysis["predictions_count"],
            "high_priority_count": sum(1 for p in analysis["predictions"] 
                                     if p["priority"] in ["high", "critical"])
        })
    
    comparisons.sort(key=lambda x: (x["high_priority_count"], x["predictions_count"]), reverse=True)
    return {"recommended_priority_order": [c["well_legal_name"] for c in comparisons]}
```

Compares multiple wells, calculates priority scores, returns sorted list for maintenance scheduling.

### Maintenance Scheduler Implementation

**Work Order Creation:**
```python
def create_work_orders_from_predictions(self, predictions, auto_schedule=True):
    created_orders = []
    for prediction in predictions:
        if self._check_existing_work_order(prediction):
            continue  # Skip duplicates
        
        scheduled_date = self._calculate_scheduled_date(prediction) if auto_schedule else prediction.predicted_failure_date - timedelta(days=7)
        
        work_order_id = self.db.create_work_order(...)
        created_orders.append({"work_order_id": work_order_id, ...})
    
    return created_orders
```

Converts predictions to work orders. Checks for duplicates (similar work order within 30 days). Calculates optimal scheduled date.

**Scheduled Date Calculation:**
```python
def _calculate_scheduled_date(self, prediction):
    target_date = prediction.predicted_failure_date - timedelta(days=7)
    
    if target_date < date.today():
        target_date = date.today() + timedelta(days=7)
    
    if prediction.priority == Priority.CRITICAL:
        target_date = min(target_date, date.today() + timedelta(days=3))
    elif prediction.priority == Priority.HIGH:
        target_date = min(target_date, date.today() + timedelta(days=7))
    
    return target_date
```

Schedules 1 week before predicted failure. Adjusts for priority. Ensures date is not in past.

### LLM Integration

**LLM Client Architecture:**
```python
class LLMClient:
    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "openai").lower()
        if self.provider == "openai":
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        elif self.provider == "anthropic":
            from anthropic import Anthropic
            self.client = Anthropic(api_key=self.api_key)
        elif self.provider == "ollama":
            from openai import OpenAI
            base_url = self.base_url or "http://localhost:11434/v1"
            self.client = OpenAI(api_key="ollama", base_url=base_url)
```

Multi-provider support (OpenAI, Anthropic, Ollama). Provider selection via environment variable. Anthropic uses different API structure (`messages.create()` vs `chat.completions.create()`). 

**Ollama Client:**
```python
elif self.provider == "ollama":
    from openai import OpenAI
    base_url = self.base_url or "http://localhost:11434/v1"
    self.client = OpenAI(api_key="ollama", base_url=base_url)
```

Ollama provides OpenAI-compatible API endpoints, allowing reuse of OpenAI client library. Default base URL is `http://localhost:11434/v1` (Ollama's OpenAI-compatible endpoint). When using Docker Compose, use `http://dev-ollama:11434/v1` for internal communication (set via `LLM_BASE_URL` environment variable). API key is not validated by Ollama but required by client library. Supports local models like `llama3.1`, `mistral`, `codellama` for privacy-sensitive deployments and cost reduction.

**Strategic Analysis:**
```python
def analyze_maintenance_strategy(self, predictions, well_context):
    prompt = f"""Analyze these maintenance predictions and provide strategic recommendations:
    
    Well: {well_context.get('well_legal_name')}
    Predictions: {json.dumps(predictions, indent=2)}
    
    Provide:
    1. Priority assessment
    2. Scheduling recommendations
    3. Resource allocation suggestions
    4. Risk mitigation strategies
    5. Cost-benefit analysis
    """
    
    if self.provider == "anthropic":
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        content = response.content[0].text
    else:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            response_format={"type": "json_object"} if self.provider == "ollama" else None
        )
        content = response.choices[0].message.content
    
    return json.loads(content)
```

LLM receives structured predictions and context. Returns JSON with strategic recommendations. Temperature 0.3 for consistency. 

**Provider-Specific Handling:**
- Anthropic: Uses `messages.create()` API with system prompt passed separately
- OpenAI/Ollama: Uses `chat.completions.create()` with system message in messages array
- Ollama: Uses `response_format={"type": "json_object"}` for structured output when supported

Response parsing handles both JSON and plain text formats, with fallback to text extraction if JSON parsing fails.

**Report Generation:**
```python
def generate_maintenance_report(self, work_orders, analysis):
    prompt = f"""Generate a comprehensive maintenance planning report in Markdown format.
    
    Work Orders Created: {len(work_orders)}
    Analysis: {json.dumps(analysis, indent=2)}
    
    Generate:
    - Executive Summary
    - Maintenance Schedule Overview
    - Priority Breakdown
    - Resource Requirements
    - Risk Assessment
    - Recommendations
    """
    
    response = self.client.chat.completions.create(...)
    return response.choices[0].message.content
```

LLM generates markdown report from work orders and analysis. Includes executive summary, schedule, priorities, resources, risks, recommendations.

### Agent Orchestration

**Main Workflow:**
```python
def analyze_and_schedule(self, well_legal_name=None, include_llm_reasoning=True, auto_schedule=True):
    # Step 1: Get wells
    wells = [{"well_legal_name": well_legal_name}] if well_legal_name else self.agent_tools.get_well_list()
    
    # Step 2: Analyze each well
    all_predictions = []
    well_analyses = []
    for well in wells:
        analysis = self.agent_tools.analyze_well(well["well_legal_name"])
        well_analyses.append(analysis)
        all_predictions.extend(convert_to_predictions(analysis["predictions"]))
    
    # Step 3: LLM reasoning
    llm_analysis = None
    if include_llm_reasoning and self.llm_client:
        main_analysis = max(well_analyses, key=lambda x: x["predictions_count"])
        llm_analysis = self.llm_client.analyze_maintenance_strategy(...)
    
    # Step 4: Create work orders
    work_orders = []
    if auto_schedule and all_predictions:
        work_orders = self.scheduler.create_work_orders_from_predictions(all_predictions)
    
    # Step 5: Generate report
    report = None
    if self.llm_client and work_orders:
        report = self.llm_client.generate_maintenance_report(work_orders, llm_analysis)
    
    return {
        "wells_analyzed": len(wells),
        "total_predictions": len(all_predictions),
        "work_orders_created": len(work_orders),
        "well_analyses": well_analyses,
        "llm_analysis": llm_analysis,
        "work_orders": work_orders,
        "report": report
    }
```

Multi-step autonomous workflow: observation (analysis) → reasoning (LLM) → action (scheduling) → reporting.

### FastAPI REST API

**Endpoint Implementation:**
```python
@app.post("/analyze")
async def analyze_and_schedule(request: AnalysisRequest):
    result = agent.analyze_and_schedule(
        well_legal_name=request.well_legal_name,
        include_llm_reasoning=request.include_llm_reasoning,
        auto_schedule=request.auto_schedule
    )
    return result
```

Async endpoint handles full workflow. Error handling returns appropriate HTTP status codes.

**Request Validation:**
```python
class AnalysisRequest(BaseModel):
    well_legal_name: Optional[str] = Field(None, description="Specific well to analyze")
    include_llm_reasoning: bool = Field(True, description="Use LLM for strategic analysis")
    auto_schedule: bool = Field(True, description="Automatically create work orders")
```

Pydantic models provide automatic validation and OpenAPI documentation.

### Performance Considerations

**Query Optimization:**
- Joins use indexes (well_legal_name, wellbore_name)
- Date filters use indexed columns
- LIMIT clauses prevent large result sets
- Connection pooling via SQLAlchemy

**LLM Call Optimization:**
- Strategic analysis only for wells with predictions
- Report generation uses summary of work orders
- Temperature 0.3 for faster, more deterministic responses
- Max tokens limited (2000 for analysis, 3000 for reports)

**Batch Processing:**
- Wells analyzed sequentially (can be parallelized)
- Work orders created in batch
- Deduplication prevents redundant work orders

### Security Implementation

**SQL Injection Prevention:**
- All queries use SQLAlchemy parameter binding
- Table/column names validated
- No dynamic SQL construction from user input

**Input Validation:**
- Pydantic models validate all API inputs
- Type checking ensures parameters match expected types
- Field constraints enforce business rules

**API Security:**
- CORS middleware configured
- No authentication implemented (add API keys/OAuth for production)
- Input validation via Pydantic models

### Docker Configuration

**Container Setup:**
- Base: `python:3.11-slim`
- Port: 8003 (mapped to host)
- Environment: Database and LLM configuration
- Command: `uvicorn api:app --host 0.0.0.0 --port 8003`

**Dependencies:**
- Database connection required (depends_on: dev-postgres-db)
- LLM API key optional (service degrades gracefully without it)

---

## Testing the Predictive Maintenance Agent

### Test Levels

1. **Unit Tests**: Individual components (predictive models, scheduler)
2. **Integration Tests**: Components working together
3. **API Tests**: HTTP endpoint functionality
4. **End-to-End Tests**: Full workflow

### Test 1: Database Connection

**Purpose**: Verify database connectivity and table existence

```bash
docker-compose run --rm dev-predictive-maintenance-agent python -c "
import sys
sys.path.insert(0, '/app')
from database import get_db_manager

db = get_db_manager()
tables = db.execute_query('SELECT table_name FROM information_schema.tables WHERE table_schema = \\'public\\'')
print('Tables:', [t['table_name'] for t in tables])
"
```

**Expected Output:**
```
Tables: ['production_data', 'wells_data', 'wellbores_data', 'maintenance_work_orders']
```

### Test 2: Predictive Models

**Purpose**: Verify predictive models work

```bash
docker-compose run --rm dev-predictive-maintenance-agent python -c "
import sys
sys.path.insert(0, '/app')
from database import get_db_manager
from predictive_models import PredictiveModel

db = get_db_manager()
model = PredictiveModel(db)
wells = db.execute_query('SELECT DISTINCT wb.well_legal_name FROM production_data p LEFT JOIN wellbores_data wb ON p.wellbore = wb.wellbore_name WHERE wb.well_legal_name IS NOT NULL LIMIT 1')
if wells:
    predictions = model.analyze_well(wells[0]['well_legal_name'], days=90)
    print(f'Found {len(predictions)} predictions')
"
```

### Test 3: Agent Tools

**Purpose**: Verify agent tools work

```bash
docker-compose run --rm dev-predictive-maintenance-agent python -c "
import sys
sys.path.insert(0, '/app')
from agent_tools import AgentTools

tools = AgentTools()
wells = tools.get_well_list()
print(f'Found {len(wells)} wells')
"
```

### Test 4: API Endpoints

**Purpose**: Verify REST API works

```bash
# Health check
curl http://localhost:8003/health

# Analyze wells
curl -X POST http://localhost:8003/analyze \
  -H "Content-Type: application/json" \
  -d '{"well_legal_name": null, "include_llm_reasoning": false, "auto_schedule": true}'

# Get schedule
curl http://localhost:8003/schedule?days_ahead=90

# Get work orders
curl http://localhost:8003/work-orders?status=scheduled
```

---

## Key Concepts and Learning Outcomes

### Concepts Learned

1. **Predictive Maintenance**: Using data analysis to predict maintenance needs
2. **Agentic AI**: Autonomous systems that reason and take actions
3. **Predictive Models**: Statistical analysis for failure prediction
4. **Work Order Management**: Creating and managing maintenance schedules
5. **SAP PM Simulation**: Database table structure for maintenance systems
6. **Multi-Step Agent Workflows**: Observation → Reasoning → Action → Reporting
7. **LLM Integration**: Using LLMs for strategic analysis and reporting

### Technical Skills

- Predictive model implementation
- Statistical analysis (decline detection, anomaly detection)
- Agent tool design and implementation
- Work order scheduling algorithms
- Database schema design for maintenance systems
- LLM prompt engineering for maintenance planning
- REST API design for agentic systems

### Learning Outcomes

After implementing this agent, you understand:
- How to build predictive maintenance systems
- How agentic AI systems reason and take actions
- How to integrate LLMs for strategic planning
- How to simulate enterprise systems (SAP PM) with databases
- How to design multi-step autonomous workflows
- How to create work order management systems

---

## References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Anthropic API Documentation](https://docs.anthropic.com/)
- [Ollama Documentation](https://ollama.ai/docs)

---

*This guide is part of the Volve Wells AI Platform project, demonstrating advanced agentic AI concepts through predictive maintenance implementation.*
