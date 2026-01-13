# Predictive Maintenance Agent

An autonomous agentic AI system that analyzes production data to predict maintenance needs and automatically creates maintenance work orders in a SAP Plant Maintenance simulation.

## Overview

The Predictive Maintenance Agent uses production data patterns, statistical analysis, and LLM reasoning to identify when wells require maintenance. It creates maintenance work orders that simulate SAP Plant Maintenance (PM) system integration, scheduling preventive, corrective, and predictive maintenance based on data-driven insights.

## Features

- 🔮 **Predictive Analysis**: Analyzes production decline, anomalies, and equipment age patterns
- 🤖 **Agentic AI**: Autonomous reasoning and decision-making using LLM integration
- 📅 **Automatic Scheduling**: Creates maintenance work orders with optimal scheduling
- 🛠️ **SAP PM Simulation**: Stores work orders in database table simulating SAP Plant Maintenance
- 📊 **Multi-Well Analysis**: Analyzes individual wells or all wells in the database
- 🎯 **Priority-Based Scheduling**: Assigns priority levels (low, medium, high, critical) based on risk
- 📈 **LLM-Powered Strategy**: Uses LLMs for strategic maintenance planning and reporting

## Architecture

```
Production Data Analysis
    ↓
Predictive Models
    ↓
Agent Tools (Investigation)
    ↓
LLM Reasoning (Strategy)
    ↓
Maintenance Scheduler
    ↓
SAP PM Work Orders (Database)
```

## API Endpoints

### POST `/analyze`

Analyze wells and create maintenance schedules.

**Request:**
```json
{
  "well_legal_name": "15/9-F-1",  // Optional: specific well, or null for all wells
  "include_llm_reasoning": true,
  "auto_schedule": true
}
```

**Response:**
```json
{
  "timestamp": "2024-01-15T10:30:00",
  "wells_analyzed": 5,
  "total_predictions": 8,
  "work_orders_created": 6,
  "well_analyses": [...],
  "llm_analysis": {...},
  "work_orders": [...],
  "report": "Markdown report..."
}
```

### GET `/schedule`

Get current maintenance schedules.

**Query Parameters:**
- `well_legal_name` (optional): Filter by well
- `days_ahead` (default: 90): Days ahead to look

**Response:**
```json
{
  "timestamp": "2024-01-15T10:30:00",
  "schedules_count": 12,
  "schedules": [...]
}
```

### GET `/work-orders`

Get maintenance work orders.

**Query Parameters:**
- `well_legal_name` (optional): Filter by well
- `status` (optional): Filter by status (scheduled, in_progress, completed, cancelled)

**Response:**
```json
{
  "count": 15,
  "work_orders": [...]
}
```

### GET `/health`

Health check endpoint.

## Setup

### Prerequisites

- Python 3.11+
- PostgreSQL database (running via docker-compose)
- LLM API key (optional, for reasoning features)

### Environment Variables

```bash
# Database (set automatically in docker-compose)
DB_HOST=dev-postgres-db
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=postgres

# LLM Configuration (optional)
LLM_PROVIDER=openai  # Options: openai, anthropic, ollama
LLM_API_KEY=sk-...   # Your API key
LLM_MODEL=gpt-4o-mini
LLM_BASE_URL=        # Optional: for custom endpoints (e.g., Ollama)
```

### Using Docker (Recommended)

```bash
# Set LLM API key (optional)
export LLM_API_KEY=sk-your-key-here

# Build and start
docker-compose build dev-predictive-maintenance-agent
docker-compose up dev-predictive-maintenance-agent
```

The API will be available at: http://localhost:8003

### Local Development

```bash
cd predictive_maintenance_agent
pip install -r requirements.txt

# Set environment variables
export LLM_API_KEY=sk-your-key-here
export LLM_PROVIDER=openai

# Run the service
uvicorn api:app --host 0.0.0.0 --port 8003
```

## LLM Provider Configuration

The Predictive Maintenance Agent supports multiple LLM providers for reasoning and report generation:

### OpenAI

```bash
export LLM_PROVIDER=openai
export LLM_API_KEY=sk-...
export LLM_MODEL=gpt-4o-mini
```

### Anthropic Claude

```bash
export LLM_PROVIDER=anthropic
export LLM_API_KEY=sk-ant-...
export LLM_MODEL=claude-3-5-sonnet-20241022
```

### Ollama (Local)

Ollama is included in the docker-compose setup. To use it:

**Option 1: Using Docker Compose (Recommended)**
```bash
# Ollama service is already configured in docker-compose.yaml
# Pull a model first:
docker exec -it dev-ollama ollama pull llama3.1

# Configure Predictive Maintenance Agent to use Ollama:
export LLM_PROVIDER=ollama
export LLM_MODEL=llama3.1
export LLM_BASE_URL=http://dev-ollama:11434/v1
export LLM_API_KEY=ollama  # Not used, but required

# Restart the service
docker-compose restart dev-predictive-maintenance-agent
```

**Option 2: Using Local Ollama Installation**
```bash
# Start Ollama locally (if installed on host)
ollama serve

# Pull a model
ollama pull llama3.1

# Configure service
export LLM_PROVIDER=ollama
export LLM_BASE_URL=http://localhost:11434/v1
export LLM_MODEL=llama3.1
export LLM_API_KEY=ollama  # Not used, but required
```

**Recommended Models for Maintenance Planning:**
- `llama3.1` - General purpose, good for reasoning
- `llama3.1:8b` - Smaller, faster version
- `mistral` - Alternative general purpose model
- `neural-chat` - Conversational model, good for report generation

## Usage Examples

### Using curl

```bash
# Analyze all wells and create schedules
curl -X POST "http://localhost:8003/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "well_legal_name": null,
    "include_llm_reasoning": true,
    "auto_schedule": true
  }'

# Analyze specific well
curl -X POST "http://localhost:8003/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "well_legal_name": "15/9-F-1",
    "include_llm_reasoning": true,
    "auto_schedule": true
  }'

# Get maintenance schedule
curl "http://localhost:8003/schedule?days_ahead=30"

# Get work orders
curl "http://localhost:8003/work-orders?status=scheduled"
```

### Using Python

```python
import requests

# Analyze and schedule
response = requests.post(
    "http://localhost:8003/analyze",
    json={
        "well_legal_name": "15/9-F-1",
        "include_llm_reasoning": True,
        "auto_schedule": True
    }
)

result = response.json()
print(f"Created {result['work_orders_created']} work orders")

# Get schedule
schedule = requests.get("http://localhost:8003/schedule?days_ahead=90")
print(schedule.json())
```

## Predictive Models

The agent uses three predictive models:

1. **Production Decline Detection**: Identifies significant production decline (>20%) over recent periods
2. **Anomaly Detection**: Detects statistical anomalies in production patterns
3. **Equipment Age Analysis**: Identifies wells with extended periods of no production

Each model generates predictions with:
- Maintenance type (preventive, corrective, predictive)
- Priority level (low, medium, high, critical)
- Predicted failure date
- Confidence score (0-100)
- Recommended action
- Estimated duration

## Maintenance Work Orders

Work orders are stored in the `maintenance_work_orders` table, simulating SAP Plant Maintenance:

- **work_order_id**: Unique identifier
- **well_legal_name**: Well requiring maintenance
- **wellbore_name**: Specific wellbore (if applicable)
- **maintenance_type**: preventive, corrective, or predictive
- **priority**: low, medium, high, or critical
- **scheduled_date**: When maintenance is scheduled
- **estimated_duration_hours**: Expected duration
- **description**: Maintenance action description
- **predicted_failure_date**: When failure is predicted
- **confidence_score**: Prediction confidence (0-100)
- **status**: scheduled, in_progress, completed, or cancelled

## Security

- All database queries use parameterized statements
- Input validation via Pydantic models
- Read-only access to production data
- Work orders can be created, updated, and queried

## Performance

- Typical analysis time: 2-5 seconds per well (without LLM)
- With LLM reasoning: 5-15 seconds per well
- Batch analysis of all wells: scales linearly
- Work order creation: <100ms per order

## Troubleshooting

**No predictions generated:**
- Ensure production data exists for the well
- Check that at least 30 days of data is available
- Verify well_legal_name matches database

**LLM errors:**
- Verify API key is set correctly
- Check LLM provider configuration
- Ensure Ollama is running if using local models

**Database connection errors:**
- Verify PostgreSQL is running
- Check database credentials
- Ensure maintenance_work_orders table exists

## Next Steps

This agent can be extended with:
- Integration with actual SAP PM systems
- More sophisticated predictive models (ML-based)
- Maintenance cost estimation
- Resource allocation optimization
- Historical maintenance effectiveness tracking

## License

Same as the main project.
