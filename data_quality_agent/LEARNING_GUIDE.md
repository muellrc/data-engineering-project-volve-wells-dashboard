# Learning Guide: Intelligent Data Quality Agent (Agentic AI)

## Table of Contents
1. [What is Agentic AI?](#what-is-agentic-ai)
2. [What is a Data Quality Agent?](#what-is-a-data-quality-agent)
3. [How Agentic AI Works](#how-agentic-ai-works)
4. [Step-by-Step Implementation](#step-by-step-implementation)
5. [Testing the Data Quality Agent](#testing-the-data-quality-agent)
6. [Key Concepts and Learning Outcomes](#key-concepts-and-learning-outcomes)

---

## What is Agentic AI?

### Definition

**Agentic AI** refers to AI systems that can:
- **Autonomously reason** about problems
- **Use tools** to investigate and take actions
- **Plan and execute** multi-step workflows
- **Learn from results** and adapt behavior
- **Make decisions** without constant human intervention

Unlike simple chatbots or single-function AI, agentic AI systems can:
- Break down complex tasks into steps
- Choose which tools to use
- Iterate and refine their approach
- Provide explanations for their actions

---

## What is a Data Quality Agent?

### Definition

A **Data Quality Agent** is an autonomous system that:
1. **Monitors** data quality continuously
2. **Detects** issues automatically
3. **Investigates** problems using tools
4. **Reasons** about root causes using LLM
5. **Reports** findings with actionable recommendations

### Why Do We Need It?

**Traditional Approach:**
- Manual data quality checks
- Time-consuming investigation
- Reactive (find issues after they cause problems)
- Requires data engineering expertise

**Agentic AI Approach:**
- Automated, continuous monitoring
- Autonomous investigation
- Proactive (catch issues early)
- Accessible to non-technical users

### Benefits

1. **Automation**: Runs checks automatically
2. **Intelligence**: Understands context and relationships
3. **Efficiency**: Investigates multiple issues in parallel
4. **Insights**: Provides root cause analysis
5. **Actionable**: Suggests specific fixes

---

## How Agentic AI Works

### Architecture Overview

```
┌─────────────────────────────────────────┐
│      Data Quality Agent System          │
└─────────────────────────────────────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
        ▼                       ▼
┌──────────────┐      ┌──────────────┐
│   Quality    │      │   Agent      │
│   Checks     │      │   Tools      │
│              │      │              │
│ • Missing    │      │ • Investigate│
│ • Duplicates │      │ • Sample     │
│ • Ranges     │      │ • Compare    │
└──────┬───────┘      └──────┬───────┘
       │                     │
       └──────────┬──────────┘
                  │
                  ▼
         ┌────────────────┐
         │  LLM Reasoning │
         │                │
         │ • Root Causes  │
         │ • Impact       │
         │ • Recommendations│
         └───────┬────────┘
                 │
                 ▼
         ┌────────────────┐
         │     Report     │
         │   Generator    │
         └────────────────┘
```

### Agent Workflow

1. **Observation**: Agent runs quality checks, discovers issues
2. **Planning**: Agent decides which issues to investigate first
3. **Action**: Agent uses tools to gather more information
4. **Reasoning**: LLM analyzes findings and provides insights
5. **Reporting**: Agent generates comprehensive report

### Tool Use Pattern

The agent follows a **plan-act-reason** loop:

```
Plan: "I need to investigate missing values in production_data"
  ↓
Act: Use investigate_table tool
  ↓
Observe: Get results showing 15% NULL values
  ↓
Reason: LLM analyzes why this might be happening
  ↓
Plan: "Let me check specific columns"
  ↓
Act: Use investigate_column tool
  ↓
...
```

**Learning Point**: This is the core of agentic AI—the agent can use multiple tools in sequence, reasoning about what to do next.

---

## Step-by-Step Implementation

Let's break down the Volve Wells Data Quality Agent implementation.

### Step 1: Project Structure

```
data_quality_agent/
├── __init__.py
├── api.py                  # FastAPI REST API
├── agent.py                # Main agent with LLM reasoning
├── agent_tools.py          # Tools agent can use
├── quality_checks.py      # Data quality validation rules
├── database.py            # Database connection utilities
├── Dockerfile
├── requirements.txt
└── README.md
```

**Why this structure?**
- **Separation**: Quality checks separate from agent logic
- **Modularity**: Tools can be added/removed easily
- **Testability**: Each component testable independently

---

### Step 2: Quality Checks (`quality_checks.py`)

**Purpose**: Define what constitutes "data quality issues"

#### Key Components

**1. QualityIssue Dataclass**

```python
@dataclass
class QualityIssue:
    table: str
    column: Optional[str]
    issue_type: str
    severity: QualitySeverity
    message: str
    affected_rows: Optional[int]
    recommendation: Optional[str]
```

**What it represents:**
- Structured representation of a problem
- Includes severity (info, warning, error, critical)
- Provides recommendations for fixes

**2. DataQualityChecker Class**

```python
class DataQualityChecker:
    def check_missing_values(self, table, columns):
        # Finds NULL values
        # Calculates percentage
        # Returns QualityIssue objects
```

**Types of Checks:**
- **Missing Values**: NULL/NULL percentage
- **Duplicates**: Duplicate key combinations
- **Data Freshness**: How old is the data?
- **Value Ranges**: Outliers and invalid values
- **Referential Integrity**: Orphaned foreign keys

**Learning Point**: Quality checks are deterministic—they always produce the same results for the same data.

---

### Step 3: Agent Tools (`agent_tools.py`)

**Purpose**: Provide tools the agent can use to investigate issues

#### Tool Pattern

```python
class AgentTools:
    def investigate_table(self, table_name):
        # Tool that investigates a table
        # Returns investigation results
        # Agent can call this autonomously
```

**Available Tools:**
1. `investigate_table` - Deep dive into table issues
2. `investigate_column` - Analyze specific column
3. `get_sample_data` - Examine sample records
4. `compare_with_historical` - Compare with past data

**Why Tools Matter:**
- Agent can't directly access database
- Tools provide controlled access
- Each tool has a specific purpose
- Agent chooses which tools to use

**Learning Point**: Tools enable the agent to take actions beyond just reasoning. This is what makes it "agentic" rather than just a chatbot.

---

### Step 4: Agent with LLM Reasoning (`agent.py`)

**Purpose**: Combine quality checks, tools, and LLM reasoning

#### Key Components

**1. Agent Initialization**

```python
class DataQualityAgent:
    def __init__(self):
        self.quality_checker = DataQualityChecker(db)
        self.agent_tools = AgentTools()
        self.llm_client = LLMClient()  # For reasoning
```

**What this creates:**
- Agent has access to quality checks
- Agent has access to investigation tools
- Agent can use LLM for reasoning

**2. Quality Check Execution**

```python
def run_quality_check(self):
    issues = self.quality_checker.run_all_checks()
    # Returns structured list of issues
```

**3. Agent Investigation**

```python
def investigate_issues(self, issues):
    # Agent uses tools to investigate
    for issue in issues:
        result = self.agent_tools.investigate_table(issue.table)
        # Gathers more information
```

**4. LLM Reasoning**

```python
def reason_about_issues(self, issues, context):
    # LLM analyzes issues
    # Provides root cause analysis
    # Suggests recommendations
```

**Prompt Engineering for Reasoning:**

```
You are a data quality analyst. Analyze these issues:

1. Root cause analysis
2. Impact assessment
3. Prioritized recommendations
4. Prevention strategies

Issues: [list of issues]
Context: [database schema, table info]
```

**5. Report Generation**

```python
def generate_report(self, issues, reasoning, investigations):
    # LLM creates comprehensive markdown report
    # Includes summary, analysis, recommendations
```

**Learning Point**: The agent orchestrates multiple components—checks, tools, and LLM—to create a complete solution.

---

### Step 5: REST API (`api.py`)

**Purpose**: Expose agent functionality via HTTP

#### Key Endpoints

**1. POST /check**

```python
@app.post("/check")
async def run_quality_check(request):
    # Runs full agent workflow:
    # 1. Quality checks
    # 2. Investigation
    # 3. LLM reasoning
    # 4. Report generation
```

**2. GET /check/quick**

Quick check without LLM (faster, less detailed).

**3. GET /report**

Get latest quality report.

**Why REST API?**
- Easy integration with other systems
- Can be called from web apps, scripts, schedulers
- Standard HTTP interface

---

## Technical Implementation Details

### Technology Stack

**Core Dependencies:**
- `fastapi` (v0.104.0): REST API framework for agent endpoints
- `uvicorn[standard]` (v0.24.0): ASGI server for async request handling
- `sqlalchemy` (v2.0.45): Database ORM and query execution
- `psycopg2-binary` (v2.9.11): PostgreSQL database adapter
- `openai` (v1.0.0+): OpenAI API client for LLM integration
- `anthropic` (v0.18.0+): Anthropic Claude API client
- `pydantic` (v2.0.0+): Data validation and settings management

**Python Version:** 3.11 (slim Docker image)

### Agentic AI Architecture

**Agent Workflow Pattern:**
```python
class DataQualityAgent:
    def run_quality_check(self, table: Optional[str] = None) -> Dict[str, Any]:
        # 1. Run automated checks
        issues = self.quality_checker.run_all_checks(table)
        
        # 2. Investigate issues using tools
        investigation_results = []
        for issue in critical_issues:
            result = self.agent_tools.investigate_table(issue.table)
            investigation_results.append(result)
        
        # 3. LLM reasoning for root cause analysis
        reasoning = self.llm_client.analyze_issues(issues, investigation_results)
        
        # 4. Generate comprehensive report
        report = self.llm_client.generate_report(issues, reasoning, investigation_results)
```

Multi-step autonomous workflow: observation (checks) → investigation (tools) → reasoning (LLM) → action (report). Agent decides which tools to use based on issue severity and type.

**Tool-Based Investigation:**
Agent has access to investigation tools (`AgentTools` class) that it can call autonomously:
- `investigate_table()`: Runs quality checks on specific table
- `investigate_column()`: Deep dive into column statistics
- `get_sample_data()`: Retrieves sample rows for analysis
- `compare_with_historical()`: Compares current state with historical patterns

Tools return structured data that agent uses for reasoning. Tool selection is deterministic (based on issue type) but extensible to LLM-driven selection.

### Data Quality Check Implementation

**Check Architecture:**
```python
class DataQualityChecker:
    def check_missing_values(self, table: str, columns: Optional[List[str]]) -> List[QualityIssue]:
        query = f"SELECT COUNT(*) as null_count FROM {table} WHERE {column} IS NULL"
        null_count = result[0]["null_count"]
        percentage = (null_count / total) * 100
        severity = QualitySeverity.ERROR if percentage > 50 else QualitySeverity.WARNING
```

Each check method:
1. Executes SQL query to detect issue
2. Calculates metrics (count, percentage, statistics)
3. Determines severity based on thresholds
4. Returns structured `QualityIssue` objects

**Severity Classification:**
- `CRITICAL`: Data corruption, referential integrity violations
- `ERROR`: >50% missing values, duplicate primary keys
- `WARNING`: <50% missing values, data freshness issues
- `INFO`: Minor anomalies, statistical outliers

**Quality Issue Data Structure:**
```python
@dataclass
class QualityIssue:
    table: str
    column: Optional[str]
    issue_type: str
    severity: QualitySeverity
    message: str
    affected_rows: Optional[int]
    sample_data: Optional[List[Dict]]
    recommendation: Optional[str]
```

Dataclass provides type safety and easy serialization. `sample_data` includes example rows for LLM context. `recommendation` field populated by LLM reasoning.

**Check Types Implemented:**
1. **Missing Values**: NULL count and percentage per column
2. **Duplicates**: Duplicate row detection using key columns
3. **Data Freshness**: Last update timestamp comparison
4. **Value Ranges**: Min/max validation against expected ranges
5. **Referential Integrity**: Foreign key constraint validation

### Agent Tools Implementation

**Tool Pattern:**
```python
class AgentTools:
    def investigate_table(self, table_name: str) -> Dict[str, Any]:
        issues = []
        issues.extend(self.quality_checker.check_missing_values(table_name))
        issues.extend(self.quality_checker.check_duplicates(table_name, key_columns))
        
        stats_query = f"SELECT COUNT(*) as row_count FROM {table_name}"
        stats = self.db.execute_query(stats_query)
        
        return {
            "table": table_name,
            "row_count": stats[0]["row_count"],
            "issues_found": len(issues),
            "issues": [self._issue_to_dict(issue) for issue in issues]
        }
```

Tools combine multiple checks and queries to provide comprehensive investigation results. Return structured dictionaries for LLM consumption. Tools are stateless—each call is independent.

**Tool Methods:**
- `investigate_table()`: Runs all checks on table, returns aggregated results
- `investigate_column()`: Column-level statistics (count, distinct, min/max/avg)
- `get_sample_data()`: Retrieves sample rows with optional filtering
- `compare_with_historical()`: Compares current metrics with historical averages (if historical data available)

**Tool Result Format:**
All tools return dictionaries with:
- Investigation target (table/column name)
- Statistics (row counts, value distributions)
- Issues found (list of QualityIssue dictionaries)
- Metadata (timestamp, query used)

### LLM Integration for Reasoning

**LLM Client Architecture:**
```python
class LLMClient:
    def __init__(self, provider: Optional[str] = None):
        self.provider = provider or os.getenv("LLM_PROVIDER", "openai")
        if self.provider == "anthropic":
            self.client = Anthropic(api_key=self.api_key)
        else:
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
```

Multi-provider support (OpenAI, Anthropic, Ollama). Provider selection via environment variable. Anthropic uses different API structure (`messages.create()` vs `chat.completions.create()`). Ollama uses OpenAI-compatible API via `base_url` parameter, enabling local model deployment without external API keys. Default Ollama endpoint: `http://localhost:11434/v1` (or `http://dev-ollama:11434/v1` in Docker Compose). Supports models like `llama3.1`, `mistral` for privacy-sensitive deployments and cost-effective reasoning.

**Root Cause Analysis:**
```python
def analyze_issues(self, issues: List[QualityIssue], investigation_results: List[Dict]) -> Dict[str, Any]:
    prompt = f"""Analyze these data quality issues and provide root cause analysis:
    
    Issues: {json.dumps([self._issue_to_dict(i) for i in issues], indent=2)}
    Investigation Results: {json.dumps(investigation_results, indent=2)}
    
    Provide:
    1. Root cause analysis
    2. Impact assessment
    3. Recommended actions
    """
    
    response = self.client.chat.completions.create(
        model=self.model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
```

LLM receives structured JSON of issues and investigation results. Temperature 0.3 for balanced creativity/consistency. Response parsed as JSON when possible, falls back to text extraction.

**Report Generation:**
```python
def generate_report(self, issues: List[QualityIssue], reasoning: Dict, investigation_results: List[Dict]) -> str:
    prompt = f"""Generate a comprehensive data quality report in Markdown format.
    
    Issues: {len(issues)}
    Critical: {sum(1 for i in issues if i.severity == QualitySeverity.CRITICAL)}
    
    Generate:
    - Executive Summary
    - Issue Breakdown by Severity
    - Root Cause Analysis
    - Impact Assessment
    - Recommendations
    - Action Items
    """
```

LLM generates markdown-formatted report from structured data. Includes executive summary, detailed analysis, and actionable recommendations. Report stored in memory (can be persisted to database/file).

### FastAPI REST API

**Endpoint Structure:**
```python
@app.post("/check", response_model=QualityCheckResponse)
async def run_quality_check(request: QualityCheckRequest):
    agent = DataQualityAgent()
    result = agent.run_quality_check(table=request.table)
    return QualityCheckResponse(**result)

@app.get("/check/quick")
async def quick_check(table: Optional[str] = None):
    checker = DataQualityChecker(get_db_manager())
    issues = checker.run_all_checks(table)
    return {"issues": [self._issue_to_dict(i) for i in issues]}

@app.get("/report")
async def get_report():
    return agent.get_latest_report()
```

Three endpoints:
- `/check`: Full agent workflow (checks + investigation + LLM reasoning + report)
- `/check/quick`: Automated checks only (no LLM, faster)
- `/report`: Retrieve latest generated report

**Request/Response Models:**
```python
class QualityCheckRequest(BaseModel):
    table: Optional[str] = Field(None, description="Table to check (None = all tables)")

class QualityCheckResponse(BaseModel):
    issues: List[Dict[str, Any]]
    investigation_results: List[Dict[str, Any]]
    reasoning: Dict[str, Any]
    report: str
    timestamp: datetime
```

Pydantic models provide validation and OpenAPI documentation. Response includes all agent outputs for transparency.

### Performance Considerations

**Check Optimization:**
- Checks run sequentially (can be parallelized for multiple tables)
- SQL queries use indexes where available (well_legal_name, wellbore_name)
- Sample data limited to 10 rows to reduce payload size
- Historical comparisons cached (if implemented)

**LLM Call Optimization:**
- Root cause analysis only for critical/error issues
- Report generation uses summary of issues (first 10) to reduce token count
- Temperature 0.3 for faster, more deterministic responses
- Max tokens limited (2000 for analysis, 3000 for reports)

**Database Query Patterns:**
- Connection pooling via SQLAlchemy (pool size 5, overflow 10)
- Parameterized queries prevent SQL injection
- Aggregation queries (COUNT, SUM, AVG) used for statistics

### Security Implementation

**SQL Injection Prevention:**
- All queries use SQLAlchemy parameter binding
- Table/column names validated against schema before use
- No dynamic SQL construction from user input

**API Security:**
- CORS middleware configured (permissive in dev, restrict in production)
- No authentication implemented (add API keys/OAuth for production)
- Input validation via Pydantic models

**LLM API Key Management:**
- API keys from environment variables
- Never logged or exposed in responses
- Service works without LLM (quick check mode)

### Docker Configuration

**Container Setup:**
- Base: `python:3.11-slim`
- Port: 8001 (mapped to host)
- Environment: Database and LLM configuration
- Command: `uvicorn api:app --host 0.0.0.0 --port 8001`

**Dependencies:**
- Database connection required (depends_on: dev-postgres-db)
- LLM API key optional (service degrades gracefully without it)

---

## Testing the Data Quality Agent

### Test 1: Quality Checks

**Purpose**: Verify quality checks work correctly

```bash
docker-compose run --rm dev-data-quality-agent python -c "
import sys
sys.path.insert(0, '/app')
from quality_checks import DataQualityChecker
from database import get_db_manager

db = get_db_manager()
checker = DataQualityChecker(db)
issues = checker.check_missing_values('production_data', ['wellbore'])
print(f'Found {len(issues)} issues')
"
```

**What to check:**
- ✅ Checks execute without errors
- ✅ Issues are properly structured
- ✅ Severity levels are correct

---

### Test 2: Agent Tools

**Purpose**: Verify agent tools work

```bash
docker-compose run --rm dev-data-quality-agent python -c "
import sys
sys.path.insert(0, '/app')
from agent_tools import AgentTools

tools = AgentTools()
result = tools.investigate_table('production_data')
print(f'Investigation found {result[\"issues_found\"]} issues')
"
```

**What to check:**
- ✅ Tools can investigate tables
- ✅ Tools return structured data
- ✅ Tools handle errors gracefully

---

### Test 3: Agent Workflow

**Purpose**: Test complete agent workflow

```bash
docker-compose run --rm dev-data-quality-agent python -c "
import sys
sys.path.insert(0, '/app')
from agent import DataQualityAgent

agent = DataQualityAgent()
results = agent.run_quality_check()
print(f'Total issues: {results[\"total_issues\"]}')
"
```

**What to check:**
- ✅ Agent runs quality checks
- ✅ Results are properly formatted
- ✅ Issue grouping works

---

### Test 4: API Endpoints

**Purpose**: Test REST API

```bash
# Start service
docker-compose up -d dev-data-quality-agent

# Test health
curl http://localhost:8001/health

# Test quick check
curl http://localhost:8001/check/quick

# Test full check (requires LLM API key)
curl -X POST "http://localhost:8001/check" \
  -H "Content-Type: application/json" \
  -d '{"include_llm_reasoning": false, "investigate_issues": true}'
```

---

### Test 5: LLM Reasoning (Requires API Key)

**Purpose**: Test agentic reasoning with LLM

```bash
export LLM_API_KEY=sk-your-key

docker-compose run --rm dev-data-quality-agent python -c "
import sys, os
sys.path.insert(0, '/app')
os.environ['LLM_API_KEY'] = os.getenv('LLM_API_KEY', '')
from agent import DataQualityAgent

agent = DataQualityAgent()
results = agent.analyze_and_report(include_llm_reasoning=True)
print('Report generated:', len(results['report']) > 0)
"
```

---

## Key Concepts and Learning Outcomes

### Concepts Learned

1. **Agentic AI**
   - Autonomous reasoning and action
   - Tool use patterns
   - Multi-step workflows

2. **Data Quality**
   - Quality metrics and checks
   - Issue classification
   - Impact assessment

3. **LLM Integration for Reasoning**
   - Using LLMs for analysis, not just generation
   - Structured reasoning prompts
   - Combining deterministic checks with AI reasoning

4. **Tool-Based Architecture**
   - Agent tools pattern
   - Controlled action execution
   - Tool composition

5. **Report Generation**
   - LLM-powered documentation
   - Structured output formatting
   - Actionable recommendations

### Learning Outcomes

After studying this implementation, you should understand:

✅ **What Agentic AI is**
- Systems that reason and act autonomously
- Tool use for taking actions
- Multi-step problem solving

✅ **How Data Quality Agents work**
- Automated quality checks
- Investigation using tools
- LLM reasoning about issues
- Report generation

✅ **How to implement agentic systems**
- Quality check patterns
- Tool definition and use
- LLM reasoning integration
- Workflow orchestration

✅ **Best practices**
- Separation of concerns (checks vs. reasoning)
- Tool-based action patterns
- Error handling in agents
- Structured output formats

### Next Steps for Learning

1. **Add More Tools**: Create tools for data fixes
2. **Scheduled Monitoring**: Run agent on schedule
3. **Alerting**: Send notifications for critical issues
4. **Historical Tracking**: Store quality metrics over time
5. **Auto-Fix**: Implement automatic fixes for simple issues
6. **Multi-Agent Systems**: Multiple agents working together

### Common Pitfalls to Avoid

❌ **No Tool Validation**: Agent tools should validate inputs
✅ **Solution**: Add input validation to all tools

❌ **Infinite Loops**: Agent might get stuck in investigation loops
✅ **Solution**: Add iteration limits and timeouts

❌ **Poor Error Handling**: Tool failures crash the agent
✅ **Solution**: Wrap tool calls in try-catch, continue on errors

❌ **No LLM Fallback**: System fails if LLM is unavailable
✅ **Solution**: Provide simple report generation without LLM

❌ **Unclear Prompts**: LLM reasoning is vague
✅ **Solution**: Use structured prompts with clear output format

---

## Summary

An Intelligent Data Quality Agent is an **autonomous system** that:

1. **Monitors** data quality automatically
2. **Detects** issues using statistical checks
3. **Investigates** problems using tools
4. **Reasons** about root causes using LLM
5. **Reports** findings with actionable recommendations

The Volve Wells Data Quality Agent implementation demonstrates:
- ✅ Agentic AI patterns (tool use, reasoning, planning)
- ✅ Data quality validation
- ✅ LLM integration for analysis
- ✅ REST API for integration
- ✅ Comprehensive reporting

By understanding this implementation, you've learned how to:
- Build agentic AI systems
- Combine deterministic checks with AI reasoning
- Create tools for autonomous agents
- Design systems that reason and act

---

## Additional Resources

- [LangChain Agents Documentation](https://python.langchain.com/docs/modules/agents/)
- [AutoGen Multi-Agent Framework](https://microsoft.github.io/autogen/)
- [Data Quality Best Practices](https://www.datacamp.com/blog/data-quality)
- [LLM Reasoning Patterns](https://www.promptingguide.ai/)

---

*This guide is part of the Volve Wells AI Platform project, demonstrating MCP, LLM and agentic AI concepts through practical implementation.*
