# Learning Guide: Natural Language Query Interface

## Table of Contents
1. [What is a Natural Language Query Interface?](#what-is-a-natural-language-query-interface)
2. [Why Do We Need NLQ?](#why-do-we-need-nlq)
3. [How NLQ Works](#how-nlq-works)
4. [Step-by-Step Implementation](#step-by-step-implementation)
5. [Testing the NLQ Service](#testing-the-nlq-service)
6. [Key Concepts and Learning Outcomes](#key-concepts-and-learning-outcomes)

---

## What is a Natural Language Query Interface?

### Definition

A **Natural Language Query (NLQ) Interface** is a system that allows users to query databases using everyday language instead of SQL. It uses Large Language Models (LLMs) to convert questions like "What wells produced the most oil?" into SQL queries, executes them, and returns results in a user-friendly format.

Instead of learning SQL, you can just ask: "Show me the top 10 wells by production" and get results!

---

## Why Do We Need NLQ?

### The Problem

Traditional database querying has barriers:
1. **SQL Knowledge Required**: Users need to learn SQL syntax
2. **Schema Understanding**: Must know table and column names
3. **Complex Queries**: Joins, aggregations, and subqueries are difficult
4. **Time Consuming**: Writing SQL takes time, even for experts

### The Solution: NLQ

NLQ provides:
- ✅ **No SQL Knowledge Needed**: Ask questions in natural language
- ✅ **Schema Awareness**: LLM understands database structure automatically
- ✅ **Complex Query Handling**: LLM can generate sophisticated SQL
- ✅ **Fast Results**: Get answers in seconds, not minutes

### Benefits

1. **Accessibility**: Non-technical users can query data
2. **Speed**: Faster than writing SQL manually
3. **Accuracy**: LLM uses schema context for correct queries
4. **Learning Tool**: See how questions translate to SQL

---

## How NLQ Works

### Architecture Overview

```
┌─────────────┐
│   User      │
│  Question   │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│   REST API      │
│   (FastAPI)     │
└──────┬──────────┘
       │
       ├─────────────────┐
       │                 │
       ▼                 ▼
┌──────────────┐  ┌──────────────┐
│  LLM Client  │  │   Database   │
│              │  │   Schema     │
│  Generates   │  │   Context    │
│  SQL Query   │  │              │
└──────┬───────┘  └──────────────┘
       │
       ▼
┌──────────────┐
│   SQL        │
│  Validator   │
│  (Safety)    │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  PostgreSQL  │
│  Database    │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   Results    │
│  + Explanation│
└──────────────┘
```

### Process Flow

1. **User Question**: "What wells produced the most oil in 2016?"
2. **Schema Context**: System retrieves database schema (tables, columns, types)
3. **LLM Generation**: LLM converts question to SQL using schema context
4. **Validation**: SQL validator checks query is safe (read-only, no dangerous operations)
5. **Execution**: Query runs against PostgreSQL
6. **Response**: Results + SQL + explanation returned to user

### Example Transformation

**Input (Natural Language):**
```
"What wells produced the most oil in 2016?"
```

**Generated SQL:**
```sql
SELECT wellbore, SUM(boreoilvol) as total_oil
FROM production_data
WHERE productiontime >= '2016-01-01' 
  AND productiontime < '2017-01-01'
GROUP BY wellbore
ORDER BY total_oil DESC
LIMIT 10
```

**Output (Results):**
```json
{
  "question": "What wells produced the most oil in 2016?",
  "sql": "SELECT wellbore, SUM(boreoilvol)...",
  "results": [
    {"wellbore": "NO 15/9-F-1 C", "total_oil": 1234567.89},
    ...
  ],
  "explanation": "This query finds wells with highest oil production..."
}
```

---

## Step-by-Step Implementation

Let's break down the Volve Wells NLQ Service implementation to understand each component.

### Step 1: Project Structure

```
nlq_service/
├── __init__.py              # Package marker
├── api.py                   # FastAPI REST API
├── database.py             # Database connection & schema
├── llm_client.py           # LLM integration
├── sql_validator.py        # SQL safety validation
├── Dockerfile              # Container configuration
├── requirements.txt        # Python dependencies
├── README.md               # Documentation
└── example_usage.py        # Usage examples
```

**Why this structure?**
- **Separation of concerns**: Each module has a single responsibility
- **Modularity**: Easy to swap LLM providers or add features
- **Testability**: Each component can be tested independently

---

### Step 2: Database Layer (`database.py`)

**Purpose**: Handle database connections and provide schema context for LLMs

#### Key Components

**1. DatabaseManager Class**
```python
class DatabaseManager:
    def __init__(self, connection_string):
        self.engine = create_engine(connection_string)
```

**What it does:**
- Creates connection pool to PostgreSQL
- Provides query execution methods
- Generates schema context for LLMs

**2. Schema Context Generation**

```python
def get_database_schema_context(self) -> str:
    """Get formatted schema for LLM context."""
    # Retrieves all tables and columns
    # Formats as readable text for LLM
```

**Why this matters:**
- LLMs need to know database structure to generate correct SQL
- Schema context acts as "RAG" (Retrieval Augmented Generation)
- Ensures generated SQL uses correct table/column names

**Learning Point**: Schema context is crucial for accurate SQL generation. Without it, LLMs might guess table names incorrectly.

---

### Step 3: LLM Client (`llm_client.py`)

**Purpose**: Interface with LLMs to convert natural language to SQL

#### Key Components

**1. Multi-Provider Support**

```python
class LLMProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"
```

**Why multiple providers?**
- Flexibility: Use different LLMs based on needs/cost
- Fallback options: If one provider is down
- Local options: Ollama for privacy-sensitive deployments

**2. SQL Generation Method**

```python
def generate_sql(
    self, 
    natural_language_query: str, 
    schema_context: str
) -> Dict[str, Any]:
    # Builds prompt with schema
    # Calls LLM API
    # Returns SQL + explanation
```

**Prompt Engineering:**

The system prompt includes:
- Database schema (tables, columns, types)
- Rules (only SELECT, use correct names, etc.)
- Examples (few-shot learning)

**Example Prompt:**
```
You are a SQL query generator. Convert natural language questions to PostgreSQL SQL queries.

Database Schema:
Table: production_data
  - productiontime: timestamp (NULL)
  - wellbore: text (NULL)
  - boreoilvol: float (NULL)
  ...

Rules:
1. Only generate SELECT queries (read-only)
2. Use proper SQL syntax for PostgreSQL
3. Use table and column names exactly as shown
...
```

**Learning Point**: Good prompts are essential. The LLM needs clear instructions and context to generate accurate SQL.

---

### Step 4: SQL Validator (`sql_validator.py`)

**Purpose**: Ensure generated SQL is safe to execute

#### Security Layers

**1. Keyword Filtering**

```python
DANGEROUS_KEYWORDS = [
    'DROP', 'DELETE', 'TRUNCATE', 'ALTER', 
    'CREATE', 'INSERT', 'UPDATE', ...
]
```

**What it does:**
- Blocks dangerous SQL operations
- Prevents data modification
- Ensures read-only access

**2. Pattern Detection**

```python
dangerous_patterns = [
    r';\s*(DROP|DELETE|...)',  # SQL injection attempts
    r'--',                      # Comments (could hide malicious code)
    r'UNION.*SELECT',           # Union-based injection
    ...
]
```

**Why this matters:**
- LLMs can sometimes generate unsafe SQL
- Validator acts as a safety net
- Protects against both accidental and malicious queries

**3. Syntax Validation**

```python
# Check for balanced parentheses
if query.count('(') != query.count(')'):
    return False, "Unbalanced parentheses"
```

**Learning Point**: Never trust LLM output blindly. Always validate before execution!

---

### Step 5: REST API (`api.py`)

**Purpose**: Provide HTTP endpoints for NLQ functionality

#### Key Endpoints

**1. POST /query**

```python
@app.post("/query")
async def execute_natural_language_query(request: QueryRequest):
    # 1. Get schema context
    # 2. Generate SQL using LLM
    # 3. Validate SQL
    # 4. Execute query
    # 5. Return results
```

**Request/Response Flow:**
```
User → API → LLM → Validator → Database → Results → User
```

**2. POST /validate-sql**

Allows testing SQL without execution:
- Useful for debugging
- Helps understand LLM output
- Educational tool

**3. GET /schema**

Returns database schema:
- Helps users understand available data
- Useful for crafting better questions
- Documentation tool

**Learning Point**: REST APIs make the service accessible from any language/platform.

---

### Step 6: Integration Points

#### Docker Integration

**Dockerfile:**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
```

**docker-compose.yaml:**
```yaml
dev-nlq-service:
  build: ./nlq_service
  environment:
    - LLM_PROVIDER=openai
    - LLM_API_KEY=${LLM_API_KEY}
    - DB_HOST=dev-postgres-db
  ports:
    - "8000:8000"
```

**Key Settings:**
- Environment variables for configuration
- Port mapping for API access
- Dependency on PostgreSQL

---

## Technical Implementation Details

### Technology Stack

**Core Dependencies:**
- `fastapi` (v0.104.0): ASGI web framework for REST API, automatic OpenAPI documentation
- `uvicorn[standard]` (v0.24.0): ASGI server implementation with standard extras (uvloop, httptools)
- `sqlalchemy` (v2.0.45): Database ORM and connection pooling
- `psycopg2-binary` (v2.9.11): PostgreSQL database adapter
- `openai` (v1.0.0+): OpenAI API client library
- `anthropic` (v0.18.0+): Anthropic Claude API client
- `pydantic` (v2.0.0+): Data validation using Python type annotations

**Python Version:** 3.11 (slim Docker image)

### FastAPI Application Architecture

**Application Initialization:**
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Volve Wells Natural Language Query API",
    version="0.1.0"
)
app.add_middleware(CORSMiddleware, allow_origins=["*"])
```

FastAPI uses ASGI (Asynchronous Server Gateway Interface) for async request handling. CORS middleware enables cross-origin requests for web integration. Automatic OpenAPI schema generation at `/docs` endpoint.

**Request/Response Models:**
```python
from pydantic import BaseModel, Field

class QueryRequest(BaseModel):
    question: str = Field(..., description="Natural language question")
    include_explanation: bool = Field(True)
    max_results: int = Field(100, ge=1, le=1000)
```

Pydantic models provide automatic request validation, type conversion, and OpenAPI schema generation. Field constraints (`ge`, `le`) enforce business rules at API boundary.

### LLM Client Implementation

**Multi-Provider Architecture:**
```python
class LLMProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"
```

Enum-based provider selection. Each provider has separate initialization method (`_init_openai`, `_init_anthropic`, `_init_ollama`). Ollama uses OpenAI-compatible API wrapper for code reuse.

**OpenAI Client:**
```python
from openai import OpenAI
self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
```

Uses `openai` library v1.0+ with structured client API. `base_url` parameter enables custom endpoints (e.g., Ollama at `http://localhost:11434/v1`). API key from environment variable.

**Anthropic Client:**
```python
from anthropic import Anthropic
self.client = Anthropic(api_key=self.api_key)
```

Anthropic SDK uses different API structure. Messages API (`client.messages.create()`) instead of chat completions. System prompts passed separately, not in messages array.

**Ollama Client:**
```python
from openai import OpenAI
base_url = self.base_url or "http://localhost:11434/v1"
self.client = OpenAI(api_key="ollama", base_url=base_url)
```

Ollama provides OpenAI-compatible API endpoints, allowing reuse of OpenAI client library. Default base URL is `http://localhost:11434/v1` (Ollama's OpenAI-compatible endpoint). When using Docker Compose, use `http://dev-ollama:11434/v1` for internal communication. API key is not validated by Ollama but required by client library. Supports local models like `llama3.1`, `mistral`, `codellama` for privacy-sensitive deployments and cost reduction.

**SQL Generation Method:**
```python
def generate_sql(self, natural_language_query: str, schema_context: str) -> Dict[str, Any]:
    system_prompt = self._build_system_prompt(schema_context)
    user_prompt = f"Convert this question to SQL: {natural_language_query}"
    
    response = self.client.chat.completions.create(
        model=self.model,
        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
        temperature=0.1
    )
```

Temperature set to 0.1 for deterministic SQL generation. System prompt includes database schema (RAG pattern). Response parsed as JSON when possible, falls back to plain text extraction.

**Prompt Engineering:**
System prompt structure:
1. Role definition ("You are a SQL query generator")
2. Database schema (formatted table/column information)
3. Rules (only SELECT, use exact names, PostgreSQL syntax)
4. Optional few-shot examples

Schema context generated from `information_schema.columns` query, formatted as readable text for LLM consumption.

### SQL Validation Implementation

**Validation Layers:**
```python
class SQLValidator:
    DANGEROUS_KEYWORDS = ['DROP', 'DELETE', 'TRUNCATE', ...]
    
    @staticmethod
    def validate_query(query: str) -> Tuple[bool, Optional[str]]:
        # 1. Empty check
        # 2. SELECT-only enforcement
        # 3. Keyword filtering (word boundaries)
        # 4. Pattern detection (regex)
        # 5. Syntax validation (parentheses)
```

Multi-layer validation approach:
- **Keyword Filtering**: Uses regex word boundaries (`\b`) to avoid false positives (e.g., "SELECT" in "SELECTED" won't match)
- **Pattern Detection**: Regex patterns for SQL injection attempts (`; DROP`, `UNION SELECT`, etc.)
- **Syntax Check**: Basic parentheses balancing

**Sanitization:**
```python
def sanitize_query(query: str) -> str:
    query = re.sub(r'--.*$', '', query, flags=re.MULTILINE)  # Remove comments
    query = re.sub(r'/\*.*?\*/', '', query, flags=re.DOTALL)  # Remove block comments
    query = ' '.join(query.split())  # Normalize whitespace
```

Removes SQL comments (single-line `--` and multi-line `/* */`). Normalizes whitespace to single spaces. Does not modify SQL logic, only formatting.

### Database Schema Context Generation

**Schema Retrieval:**
```python
def get_database_schema_context(self) -> str:
    tables = self.get_all_tables()
    schema_parts = []
    for table in tables:
        columns = self.get_table_schema(table)
        # Format as: "Table: table_name\n  - column: type (nullable)\n"
```

Queries `information_schema.columns` for each table. Formats as structured text for LLM consumption. Includes column names, data types, and nullability. Acts as RAG (Retrieval Augmented Generation) context.

**Schema Query:**
```sql
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = :table_name
ORDER BY ordinal_position
```

Uses PostgreSQL's information schema. `ordinal_position` ensures columns listed in table definition order. Parameterized query prevents injection.

### API Endpoint Implementation

**Query Endpoint:**
```python
@app.post("/query", response_model=QueryResponse)
async def execute_natural_language_query(request: QueryRequest):
    # 1. Get schema context
    schema_context = db_manager.get_database_schema_context()
    
    # 2. Generate SQL
    llm_result = llm_client.generate_sql(request.question, schema_context)
    generated_sql = llm_result["sql"]
    
    # 3. Validate SQL
    is_valid, error = sql_validator.validate_query(generated_sql)
    
    # 4. Sanitize and execute
    sanitized_sql = sql_validator.sanitize_query(generated_sql)
    results = db_manager.execute_query(sanitized_sql)
```

Async endpoint handles full workflow. Error handling at each step returns appropriate HTTP status codes. Execution time tracked for performance monitoring.

**Error Handling:**
- 400 Bad Request: Invalid SQL generated or validation failed
- 500 Internal Server Error: LLM API errors, database connection issues
- 503 Service Unavailable: Health check failures

### Performance Optimization

**Connection Pooling:**
SQLAlchemy connection pool reused across requests. Default pool size 5, overflow 10. Connections persist for request lifetime, reducing connection overhead.

**Query Limits:**
- Default limit: 100 rows
- Maximum limit: 1000 rows (enforced by Pydantic validation)
- LIMIT clause automatically appended if not present

**LLM Response Caching:**
Not implemented in current version. Future optimization: cache SQL generation results for identical questions.

### Security Implementation

**SQL Injection Prevention:**
- All database queries use SQLAlchemy parameter binding
- No string concatenation for SQL construction
- Input validation via Pydantic models
- SQL validator blocks dangerous operations

**API Security:**
- CORS configured (currently permissive, should be restricted in production)
- No authentication implemented (add API keys or OAuth for production)
- Rate limiting not implemented (add middleware for production)

**LLM API Key Management:**
- API keys stored in environment variables
- Never logged or exposed in responses
- Optional feature (service works without LLM for validation-only)

### Docker Configuration

**Container Setup:**
- Base: `python:3.11-slim`
- Port: 8000 (mapped to host)
- Environment: Database and LLM configuration
- Command: `uvicorn api:app --host 0.0.0.0 --port 8000`

**Uvicorn Configuration:**
- ASGI server with auto-reload disabled (production mode)
- Host `0.0.0.0` binds to all interfaces
- Standard workers (single process, can add workers for scaling)

---

## Testing the NLQ Service

### Test Levels

We test at multiple levels:

1. **Unit Tests**: Individual components
2. **Integration Tests**: Components working together
3. **API Tests**: HTTP endpoint functionality
4. **End-to-End Tests**: Full workflow

---

### Test 1: Database Connection

**Purpose**: Verify database connectivity and schema generation

```bash
docker-compose run --rm dev-nlq-service python -c \
  "import sys; sys.path.insert(0, '/app'); \
   from database import get_db_manager; \
   db = get_db_manager(); \
   schema = db.get_database_schema_context(); \
   print('Schema length:', len(schema))"
```

**What to check:**
- ✅ Connection succeeds
- ✅ Schema context is generated
- ✅ Contains expected tables

**Expected Output:**
```
Schema length: 500+ (contains all table schemas)
```

---

### Test 2: SQL Validation

**Purpose**: Verify SQL validator works correctly

```bash
docker-compose run --rm dev-nlq-service python -c "
import sys
sys.path.insert(0, '/app')
from sql_validator import SQLValidator

# Test valid query
is_valid, error = SQLValidator.validate_query('SELECT * FROM production_data LIMIT 10')
print('Valid query:', is_valid)

# Test dangerous query
is_valid, error = SQLValidator.validate_query('DROP TABLE production_data')
print('Dangerous query valid:', is_valid)
print('Error:', error)
"
```

**What to check:**
- ✅ Valid SELECT queries pass
- ✅ Dangerous queries are blocked
- ✅ Error messages are clear

---

### Test 3: LLM Client (Requires API Key)

**Purpose**: Verify LLM integration works

```bash
# Set API key first
export LLM_API_KEY=sk-your-key

docker-compose run --rm dev-nlq-service python -c "
import sys, os
sys.path.insert(0, '/app')
os.environ['LLM_API_KEY'] = os.getenv('LLM_API_KEY', '')
from llm_client import LLMClient
from database import get_db_manager

db = get_db_manager()
schema = db.get_database_schema_context()
client = LLMClient()

result = client.generate_sql(
    'What wells produced the most oil?',
    schema
)
print('Generated SQL:', result['sql'][:100])
"
```

**What to check:**
- ✅ LLM client initializes
- ✅ SQL is generated
- ✅ SQL is syntactically correct

---

### Test 4: API Health Check

**Purpose**: Verify API is running

```bash
# Start service
docker-compose up -d dev-nlq-service

# Test health endpoint
curl http://localhost:8000/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "tables": 3
}
```

---

### Test 5: Full Query Flow

**Purpose**: Test complete NLQ workflow

```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How many wells are in the database?",
    "include_explanation": true,
    "max_results": 10
  }'
```

**What to check:**
- ✅ Question is converted to SQL
- ✅ SQL is validated
- ✅ Query executes successfully
- ✅ Results are returned
- ✅ Explanation is provided

**Expected Response:**
```json
{
  "question": "How many wells are in the database?",
  "sql": "SELECT COUNT(DISTINCT well_legal_name) FROM wells_data",
  "explanation": "This query counts unique wells...",
  "results": [{"count": 15}],
  "row_count": 1,
  "execution_time_ms": 123.45
}
```

---

### Test 6: Error Handling

**Purpose**: Verify error handling works

```bash
# Test with invalid question (might generate bad SQL)
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Delete all data",
    "max_results": 10
  }'
```

**What to check:**
- ✅ Dangerous queries are rejected
- ✅ Error messages are helpful
- ✅ Service doesn't crash

---

### Test Checklist

Use this checklist to verify everything works:

- [ ] Database connection succeeds
- [ ] Schema context is generated correctly
- [ ] SQL validator blocks dangerous queries
- [ ] SQL validator allows safe queries
- [ ] LLM client can generate SQL (with API key)
- [ ] API health check works
- [ ] POST /query endpoint works
- [ ] POST /validate-sql endpoint works
- [ ] GET /schema endpoint works
- [ ] Error handling works correctly
- [ ] Results are formatted properly

---

## Key Concepts and Learning Outcomes

### Concepts Learned

1. **LLM Integration**
   - How to use LLMs for code generation
   - Prompt engineering for SQL generation
   - Multi-provider support

2. **RAG (Retrieval Augmented Generation)**
   - Using database schema as context
   - Improving LLM accuracy with domain knowledge
   - Context injection patterns

3. **Security in AI Systems**
   - Validating LLM output
   - SQL injection prevention
   - Read-only query enforcement

4. **REST API Design**
   - FastAPI framework
   - Request/response models
   - Error handling patterns

5. **System Integration**
   - Docker containerization
   - Environment variable configuration
   - Service dependencies

### Learning Outcomes

After studying this implementation, you should understand:

✅ **What NLQ is and why it's useful**
- Natural language to SQL conversion
- Makes databases accessible to non-technical users

✅ **How NLQ systems work**
- LLM-based SQL generation
- Schema context for accuracy
- Validation for safety

✅ **How to implement an NLQ service**
- LLM client integration
- SQL validation patterns
- REST API design

✅ **How to test NLQ services**
- Component testing
- API testing
- End-to-end testing

✅ **Best practices**
- Security (SQL validation)
- Error handling
- Prompt engineering
- Code organization

### Next Steps for Learning

1. **Improve Prompts**: Experiment with different prompt strategies
2. **Add Caching**: Cache frequently asked questions
3. **Query Optimization**: Suggest query improvements
4. **Multi-turn Conversations**: Handle follow-up questions
5. **Result Visualization**: Generate charts from results
6. **Query History**: Track and learn from past queries
7. **User Feedback**: Learn from user corrections

### Common Pitfalls to Avoid

❌ **Trusting LLM Output**: Always validate SQL before execution
✅ **Solution**: Implement comprehensive SQL validation

❌ **Poor Schema Context**: Vague or incomplete schema leads to bad SQL
✅ **Solution**: Provide detailed, formatted schema context

❌ **No Error Handling**: LLM failures crash the service
✅ **Solution**: Wrap LLM calls in try-catch blocks

❌ **Hardcoded Prompts**: Can't adapt to different databases
✅ **Solution**: Build prompts dynamically from schema

❌ **No Rate Limiting**: API can be abused
✅ **Solution**: Add rate limiting middleware

---

## Summary

A Natural Language Query interface is a **bridge** between users and databases. It:

1. **Accepts questions** in natural language
2. **Uses LLMs** to generate SQL queries
3. **Validates queries** for safety
4. **Executes queries** against the database
5. **Returns results** with explanations

The Volve Wells NLQ Service implementation demonstrates:
- ✅ LLM integration (OpenAI, Anthropic, Ollama)
- ✅ SQL validation and safety
- ✅ REST API design
- ✅ Schema-aware query generation
- ✅ Comprehensive error handling

By understanding this implementation, you've learned how to:
- Build NLQ systems for your own databases
- Integrate LLMs into data applications
- Create safe, validated query interfaces
- Design REST APIs for AI-powered services

---

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Anthropic API Documentation](https://docs.anthropic.com/)
- [Ollama Documentation](https://ollama.ai/docs)
- [SQL Injection Prevention](https://owasp.org/www-community/attacks/SQL_Injection)
- [Prompt Engineering Guide](https://www.promptingguide.ai/)

---

*This guide is part of the Volve Wells AI Platform project, demonstrating MCP, LLM and agentic AI concepts through practical implementation.*
