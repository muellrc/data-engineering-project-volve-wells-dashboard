# Intelligent Data Quality Agent

An autonomous agentic AI system that monitors data quality, investigates issues using reasoning and tools, and generates comprehensive reports with actionable recommendations.

## Overview

The Data Quality Agent is an intelligent system that combines:
- **Automated Quality Checks**: Statistical validation of data integrity
- **Agentic AI Reasoning**: Uses LLMs to analyze issues and provide insights
- **Tool-Based Investigation**: Autonomous investigation using specialized tools
- **Report Generation**: Creates detailed, human-readable quality reports

## Features

### Data Quality Checks

- **Missing Values Detection**: Identifies NULL values and calculates impact
- **Duplicate Detection**: Finds duplicate records based on key columns
- **Data Freshness**: Monitors if data is up-to-date
- **Value Range Validation**: Checks for outliers and invalid ranges
- **Referential Integrity**: Validates foreign key relationships

### Agentic AI Capabilities

- **Autonomous Investigation**: Agent uses tools to investigate issues
- **LLM Reasoning**: Analyzes root causes and impact
- **Prioritized Recommendations**: Suggests fixes based on severity
- **Report Generation**: Creates comprehensive markdown reports

### Agent Tools

The agent has access to tools for investigation:
- `investigate_table` - Deep dive into table-level issues
- `investigate_column` - Analyze specific column problems
- `get_sample_data` - Examine sample data for patterns
- `compare_with_historical` - Compare current vs historical data

## Architecture

```
User/API Request
    ↓
Data Quality Agent
    ↓
┌───────────┬──────────────┬──────────────┐
│           │              │              │
▼           ▼              ▼              ▼
Quality   Agent          LLM           Report
Checks    Tools        Reasoning      Generator
    │         │              │              │
    └─────────┴──────────────┴──────────────┘
                    │
                    ▼
            Comprehensive Report
```

## API Endpoints

### POST `/check`

Run comprehensive data quality check with optional LLM reasoning.

**Request:**
```json
{
  "include_llm_reasoning": true,
  "investigate_issues": true
}
```

**Response:**
```json
{
  "timestamp": "2024-01-15T10:30:00",
  "total_issues": 15,
  "issues_by_severity": {
    "critical": 0,
    "error": 3,
    "warning": 8,
    "info": 4
  },
  "issues": [...],
  "investigation_results": [...],
  "reasoning": {
    "root_causes": [...],
    "impact_assessment": "...",
    "recommendations": [...]
  },
  "report": "# Data Quality Report\n\n..."
}
```

### GET `/check/quick`

Quick quality check without LLM reasoning (faster).

### GET `/report`

Get the latest data quality report.

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
```

### Using Docker (Recommended)

```bash
# Set LLM API key (optional)
export LLM_API_KEY=sk-your-key-here

# Build and start
docker-compose build dev-data-quality-agent
docker-compose up dev-data-quality-agent
```

The API will be available at: http://localhost:8001

### Local Development

```bash
cd data_quality_agent
pip install -r requirements.txt

# Set environment variables
export LLM_API_KEY=sk-your-key-here
export LLM_PROVIDER=openai

# Run the service
uvicorn api:app --host 0.0.0.0 --port 8001
```

## LLM Provider Configuration

The Data Quality Agent supports multiple LLM providers for reasoning and report generation:

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

# Configure Data Quality Agent to use Ollama:
export LLM_PROVIDER=ollama
export LLM_MODEL=llama3.1
export LLM_BASE_URL=http://dev-ollama:11434/v1
export LLM_API_KEY=ollama  # Not used, but required

# Restart the service
docker-compose restart dev-data-quality-agent
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

**Recommended Models for Data Quality Analysis:**
- `llama3.1` - General purpose, good for reasoning
- `llama3.1:8b` - Smaller, faster version
- `mistral` - Alternative general purpose model
- `neural-chat` - Conversational model, good for report generation

**Note:** The agent can run without LLM (quick check mode), but LLM reasoning provides better root cause analysis and recommendations.

## Usage Examples

### Using curl

```bash
# Run full quality check
curl -X POST "http://localhost:8001/check" \
  -H "Content-Type: application/json" \
  -d '{
    "include_llm_reasoning": true,
    "investigate_issues": true
  }'

# Quick check (no LLM)
curl "http://localhost:8001/check/quick"

# Get report
curl "http://localhost:8001/report"
```

### Using Python

```python
import requests

# Run quality check
response = requests.post(
    "http://localhost:8001/check",
    json={
        "include_llm_reasoning": True,
        "investigate_issues": True
    }
)

result = response.json()
print(f"Total Issues: {result['total_issues']}")
print(f"Report:\n{result['report']}")
```

## How It Works

### 1. Quality Checks

The agent runs automated checks:
- Scans all tables for missing values
- Detects duplicate records
- Validates data freshness
- Checks value ranges
- Verifies referential integrity

### 2. Agent Investigation

For each issue, the agent:
- Uses tools to investigate the problem
- Gathers sample data
- Analyzes patterns
- Collects statistics

### 3. LLM Reasoning

The LLM analyzes all issues and provides:
- Root cause analysis
- Impact assessment
- Prioritized recommendations
- Prevention strategies

### 4. Report Generation

A comprehensive markdown report is generated with:
- Executive summary
- Issue breakdown
- Root causes
- Recommendations
- Action items

## Customization

### Adding Custom Quality Checks

Edit `quality_checks.py` to add new checks:

```python
def check_custom_rule(self, table: str) -> List[QualityIssue]:
    # Your custom check logic
    issues = []
    # ... check implementation
    return issues
```

### Adding Agent Tools

Edit `agent_tools.py` to add new investigation tools:

```python
def custom_investigation(self, args) -> Dict[str, Any]:
    # Your investigation logic
    return {"result": "..."}
```

## Security

- Read-only database access
- All queries use parameterized statements
- LLM reasoning is optional (works without API key)
- No data modification capabilities

## Troubleshooting

**Agent not reasoning:**
- Check LLM_API_KEY is set
- Verify LLM provider is correct
- Check API quota/rate limits

**Quality checks failing:**
- Ensure database is populated
- Verify database schema matches expectations
- Check database connection

**Report generation issues:**
- LLM reasoning requires API key
- Falls back to simple report without LLM
- Check LLM API status

## Next Steps

This agent can be extended with:
- Scheduled monitoring (cron jobs)
- Alerting system (email/Slack notifications)
- Historical tracking (store quality metrics over time)
- Auto-fix capabilities (for simple issues)
- Integration with data pipeline (prevent bad data)

## License

Same as the main project.
