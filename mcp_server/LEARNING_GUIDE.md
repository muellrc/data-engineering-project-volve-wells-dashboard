# Learning Guide: Understanding MCP Servers

## Table of Contents
1. [What is an MCP Server?](#what-is-an-mcp-server)
2. [Why Do We Need MCP?](#why-do-we-need-mcp)
3. [How MCP Works](#how-mcp-works)
4. [Step-by-Step Implementation](#step-by-step-implementation)
5. [Testing the Volve Wells MCP Server](#testing-the-volve-wells-mcp-server)
6. [Key Concepts and Learning Outcomes](#key-concepts-and-learning-outcomes)

---

## What is an MCP Server?

### Definition

**MCP (Model Context Protocol)** is a standardized protocol that allows AI assistants and Large Language Models (LLMs) to interact with external systems, data sources, and tools in a structured way.

An **MCP Server** is a program that:
- Exposes **tools** (functions) that an LLM can call
- Provides **resources** (data) that an LLM can access
- Communicates using the **MCP protocol** (JSON-RPC over stdio or HTTP)
- Acts as a **bridge** between the LLM and your application/data

The LLM doesn't need to know SQL, database connections, or your business logic—it just needs to know what tools are available and how to call them.

---

## Why Do We Need MCP?

### The Problem

LLMs are powerful, but they have limitations:
1. **No direct database access**: Can't query databases directly
2. **No real-time data**: Only know what they were trained on
3. **No system integration**: Can't interact with your applications
4. **Security concerns**: Can't give LLMs direct access to everything

### The Solution: MCP

MCP provides a **safe, standardized way** for LLMs to:
- ✅ Access your data through controlled tools
- ✅ Perform actions in your system
- ✅ Get real-time information
- ✅ Maintain security boundaries

### Benefits

1. **Standardization**: One protocol works with multiple LLMs (Claude, GPT, etc.)
2. **Security**: You control what the LLM can access
3. **Flexibility**: Add new tools without changing the LLM
4. **Separation of Concerns**: LLM handles reasoning, tools handle execution

---

## How MCP Works

### Architecture Overview

```
┌─────────────┐         MCP Protocol         ┌──────────────┐
│             │  (JSON-RPC over stdio/HTTP)  │              │
│   LLM/      │ ◄──────────────────────────► │   MCP        │
│   Client    │                               │   Server     │
│             │                               │              │
└─────────────┘                               └──────┬───────┘
                                                     │
                                                     │ Calls
                                                     │ Functions
                                                     ▼
                                            ┌──────────────┐
                                            │   Your       │
                                            │   Application│
                                            │   / Database │
                                            └──────────────┘
```

### Communication Flow

1. **Initialization**: Client connects to server, exchanges capabilities
2. **Tool Discovery**: Client asks "What tools do you have?" → Server lists tools
3. **Tool Execution**: Client says "Run tool X with parameters Y" → Server executes → Returns result
4. **Error Handling**: If something goes wrong, server returns structured error

### Protocol Details

MCP uses **JSON-RPC 2.0**, which means:
- Messages are JSON objects
- Each request has an `id` for tracking
- Responses match request IDs
- Errors are structured

**Example Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "query_production_data",
    "arguments": {
      "wellbore_name": "NO 15/9-F-1 C",
      "limit": 10
    }
  }
}
```

**Example Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "[{\"productiontime\": \"2016-01-01\", ...}]"
      }
    ]
  }
}
```

---

## Step-by-Step Implementation

Let's break down the Volve Wells MCP Server implementation to understand each component.

### Step 1: Project Structure

```
mcp_server/
├── __init__.py              # Package marker
├── server.py                # Main MCP server (entry point)
├── database.py             # Database connection & utilities
├── tools/
│   ├── __init__.py
│   └── database_tools.py   # Tool definitions & handlers
├── Dockerfile              # Container configuration
├── requirements.txt        # Python dependencies
└── README.md               # Documentation
```

**Why this structure?**
- **Separation of concerns**: Database logic separate from tool logic
- **Modularity**: Easy to add new tools
- **Maintainability**: Clear organization

---

### Step 2: Database Layer (`database.py`)

**Purpose**: Handle all database interactions

#### Key Components

**1. DatabaseManager Class**
```python
class DatabaseManager:
    def __init__(self, connection_string):
        self.engine = create_engine(connection_string)
```

**What it does:**
- Creates a connection pool to PostgreSQL
- Manages database connections efficiently
- Provides reusable query methods

**Why SQLAlchemy?**
- Handles connection pooling automatically
- Prevents connection leaks
- Provides parameterized queries (security)

**2. Query Execution Methods**

```python
def execute_query(self, query: str, params: dict) -> List[Dict]:
    # Executes SQL and returns results as list of dictionaries
```

**Key Points:**
- Uses **parameterized queries** (prevents SQL injection)
- Returns **structured data** (list of dicts)
- Handles connection cleanup automatically

**Learning Point**: Always use parameterized queries! Never concatenate user input into SQL.

---

### Step 3: Tool Definitions (`tools/database_tools.py`)

**Purpose**: Define what tools are available and how to execute them

#### Part A: Tool Schema Definition

```python
Tool(
    name="query_production_data",
    description="Query production data from the Volve wells...",
    inputSchema={
        "type": "object",
        "properties": {
            "wellbore_name": {
                "type": "string",
                "description": "Filter by wellbore name"
            },
            "limit": {
                "type": "integer",
                "default": 100
            }
        }
    }
)
```

**What this does:**
- **Name**: How the LLM will call this tool
- **Description**: Tells the LLM what this tool does (very important for LLM to understand!)
- **InputSchema**: JSON Schema defining what parameters are accepted

**Why JSON Schema?**
- LLMs understand JSON Schema
- Provides validation
- Self-documenting

**Learning Point**: Good descriptions are crucial! The LLM uses them to decide which tool to call.

#### Part B: Tool Handlers

```python
async def handle_query_production_data(arguments: Dict[str, Any]) -> List[TextContent]:
    # 1. Extract parameters
    wellbore_name = arguments.get("wellbore_name")
    limit = arguments.get("limit", 100)
    
    # 2. Build SQL query (parameterized!)
    query = "SELECT * FROM production_data WHERE 1=1"
    params = {}
    if wellbore_name:
        query += " AND wellbore = :wellbore_name"
        params["wellbore_name"] = wellbore_name
    
    # 3. Execute query
    results = db.execute_query(query, params)
    
    # 4. Format response
    return [TextContent(
        type="text",
        text=json.dumps(results, indent=2, default=str)
    )]
```

**Step-by-Step Breakdown:**

1. **Extract Parameters**: Get values from the LLM's request
2. **Build Query**: Construct SQL safely with parameters
3. **Execute**: Run query against database
4. **Format**: Convert to MCP response format (TextContent)

**Why async?**
- MCP protocol is async
- Allows handling multiple requests efficiently
- Better performance for I/O operations

**Why TextContent?**
- MCP standard response format
- Can contain text, JSON, or other content types
- LLM can easily parse the response

---

### Step 4: Server Implementation (`server.py`)

**Purpose**: Handle MCP protocol communication

#### Key Components

**1. Server Initialization**

```python
from mcp.server import Server
from mcp.server.stdio import stdio_server

app = Server("volve-wells-database")
```

**What this does:**
- Creates an MCP server instance
- Sets server name (used in protocol)
- Uses stdio transport (standard input/output)

**Why stdio?**
- Simple and universal
- Works well with Docker
- No network configuration needed

**2. Tool Listing Handler**

```python
@app.list_tools()
async def list_tools() -> ListToolsResult:
    tools = get_database_tools()
    return ListToolsResult(tools=tools)
```

**What happens:**
1. LLM client calls `tools/list` method
2. Server responds with all available tools
3. LLM learns what it can do

**When is this called?**
- On initial connection
- When LLM needs to discover capabilities

**3. Tool Execution Handler**

```python
@app.call_tool()
async def call_tool(name: str, arguments: dict) -> CallToolResult:
    # 1. Validate tool exists
    if name not in TOOL_HANDLERS:
        raise McpError(METHOD_NOT_FOUND, "Tool not found")
    
    # 2. Get handler function
    handler = TOOL_HANDLERS[name]
    
    # 3. Execute handler
    result = await handler(arguments)
    
    # 4. Return result
    return CallToolResult(content=result)
```

**Flow:**
1. **Validate**: Check tool exists
2. **Route**: Find the right handler
3. **Execute**: Run the handler (async)
4. **Return**: Send result back to LLM

**Error Handling:**
- Uses MCP error codes (METHOD_NOT_FOUND, INTERNAL_ERROR)
- Provides helpful error messages
- Maintains protocol compliance

**4. Main Entry Point**

```python
async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
```

**What this does:**
- Sets up stdio streams (stdin/stdout)
- Runs the server
- Handles protocol communication

**Why async with?**
- Properly manages resources
- Ensures cleanup on exit
- Handles connection lifecycle

---

### Step 5: Integration Points

#### Docker Integration

**Dockerfile:**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "-m", "mcp_server.server"]
```

**Why Docker?**
- Consistent environment
- Easy deployment
- Isolated from host system

**docker-compose.yaml:**
```yaml
dev-mcp-server:
  build: ./mcp_server
  depends_on:
    dev-postgres-db:
      condition: service_healthy
  environment:
    - DB_HOST=dev-postgres-db
    - DB_PASSWORD=postgres
  stdin_open: true
  tty: true
```

**Key Settings:**
- `stdin_open: true` - Allows stdio communication
- `tty: true` - Allocates pseudo-TTY
- `depends_on` - Ensures database is ready

---

## Technical Implementation Details

### Technology Stack

**Core Dependencies:**
- `mcp` (v1.25.0): Official MCP Python SDK providing Server class, stdio transport, and protocol types
- `sqlalchemy` (v2.0.45): ORM and database abstraction layer for PostgreSQL connections
- `psycopg2-binary` (v2.9.11): PostgreSQL adapter for Python, binary distribution for easier deployment
- `python-dotenv` (v1.2.1): Environment variable management

**Python Version:** 3.11 (slim Docker image)

### MCP Protocol Implementation

**Server Initialization:**
```python
from mcp.server import Server
from mcp.server.stdio import stdio_server

app = Server("volve-wells-database")
```

The `Server` class from `mcp.server` handles JSON-RPC 2.0 protocol communication. Server name "volve-wells-database" is used in protocol negotiation and logging.

**Transport Layer:**
- Uses `stdio_server()` from `mcp.server.stdio` for standard input/output communication
- Implements async context manager pattern: `async with stdio_server() as (read_stream, write_stream)`
- Reads JSON-RPC messages from stdin, writes responses to stdout
- No network ports required, works through process pipes

**Protocol Handlers:**
- `@app.list_tools()` decorator registers handler for `tools/list` JSON-RPC method
- `@app.call_tool()` decorator registers handler for `tools/call` JSON-RPC method
- Handlers are async functions returning typed results (`ListToolsResult`, `CallToolResult`)

### Database Connection Architecture

**Connection Pooling:**
```python
from sqlalchemy import create_engine

engine = create_engine(
    f"postgresql://{user}:{password}@{host}:{port}/{database}",
    pool_size=5,
    max_overflow=10
)
```

SQLAlchemy's `create_engine` creates a connection pool. Default pool size is 5 connections, with overflow up to 10. Connections are reused across tool invocations, reducing overhead.

**Query Execution Pattern:**
```python
from sqlalchemy import text

with self.get_connection() as conn:
    result = conn.execute(text(query), params or {})
    columns = result.keys()
    rows = result.fetchall()
    return [dict(zip(columns, row)) for row in rows]
```

Uses SQLAlchemy's `text()` constructor for raw SQL with parameter binding. Results are converted to list of dictionaries for JSON serialization. Context manager ensures connection cleanup.

**Parameterized Queries:**
All queries use named parameters (`:param_name`) to prevent SQL injection:
```python
query = "SELECT * FROM production_data WHERE wellbore = :wellbore_name"
params = {"wellbore_name": user_input}
```

SQLAlchemy's parameter binding handles type conversion and escaping automatically.

### Tool Definition Structure

**Tool Schema (JSON Schema):**
```python
Tool(
    name="query_production_data",
    description="...",
    inputSchema={
        "type": "object",
        "properties": {
            "wellbore_name": {
                "type": "string",
                "description": "..."
            }
        }
    }
)
```

Tools use JSON Schema for input validation. The `Tool` class from `mcp.types` serializes to MCP protocol format. Descriptions are critical—LLMs use them to select appropriate tools.

**Tool Handler Pattern:**
```python
async def handle_query_production_data(arguments: Dict[str, Any]) -> List[TextContent]:
    db = get_db_manager()
    # Build query with parameters
    results = db.execute_query(query, params)
    return [TextContent(type="text", text=json.dumps(results, default=str))]
```

All handlers are async functions accepting `Dict[str, Any]` and returning `List[TextContent]`. Results are JSON-serialized strings wrapped in `TextContent` objects for MCP protocol compliance.

### Error Handling

**MCP Error Codes:**
```python
from mcp import McpError
from mcp.types import METHOD_NOT_FOUND, INTERNAL_ERROR

raise McpError(METHOD_NOT_FOUND, "Tool not found")
raise McpError(INTERNAL_ERROR, "Execution failed")
```

Uses MCP-defined error codes from `mcp.types`. `McpError` is raised for protocol-compliant error responses. Error messages are included in JSON-RPC error objects.

**Exception Handling:**
Tool handlers wrap database operations in try-except blocks. Database exceptions are caught and re-raised as `McpError` with `INTERNAL_ERROR` code. This ensures protocol compliance even on failures.

### Async Architecture

**Async/Await Pattern:**
- All tool handlers are `async def` functions
- Database operations use async context managers
- MCP server uses asyncio event loop for concurrent request handling

**Concurrency:**
The MCP server can handle multiple tool calls concurrently. Each tool execution is independent, allowing parallel database queries when multiple tools are called simultaneously.

### Docker Configuration

**Container Setup:**
- Base image: `python:3.11-slim` (Debian-based, minimal size)
- Working directory: `/app`
- Environment variables: Database connection parameters, PYTHONPATH
- Command: `python -m mcp_server.server` (runs as module for proper imports)

**Stdio Configuration:**
- `stdin_open: true` in docker-compose enables stdin reading
- `tty: true` allocates pseudo-TTY for proper stdio handling
- No port mapping required (stdio transport)

### Performance Considerations

**Connection Reuse:**
Database connections are pooled and reused. Connection pool is created once at module import, shared across all tool invocations.

**Query Optimization:**
- All queries use LIMIT clauses to prevent large result sets
- Default limit of 100 rows, maximum 1000 rows enforced
- Indexed columns (well_legal_name, wellbore_name) used in WHERE clauses

**JSON Serialization:**
Results are serialized using `json.dumps()` with `default=str` for datetime handling. Large result sets may impact serialization time—limits prevent excessive data transfer.

### Security Implementation

**SQL Injection Prevention:**
- All user inputs passed as parameters, never concatenated into SQL
- SQLAlchemy's parameter binding handles escaping
- No dynamic SQL construction from user input

**Read-Only Access:**
- Tool handlers only execute SELECT queries
- No INSERT, UPDATE, DELETE operations exposed
- Database user should have read-only permissions in production

**Input Validation:**
- JSON Schema validates tool arguments before handler execution
- Type checking ensures parameters match expected types
- Optional parameters have default values

---

## Testing the Volve Wells MCP Server

### Test Levels

We test at multiple levels to ensure everything works:

1. **Unit Tests**: Individual components
2. **Integration Tests**: Components working together
3. **Protocol Tests**: MCP protocol compliance
4. **End-to-End Tests**: Full workflow

---

### Test 1: Database Connection

**Purpose**: Verify this MCP Server can connect to the database

```bash
docker-compose run --rm dev-mcp-server python -c \
  "import sys; sys.path.insert(0, '/app'); \
   from database import get_db_manager; \
   db = get_db_manager(); \
   print('Tables:', db.get_all_tables())"
```

**What to check:**
- ✅ Connection succeeds
- ✅ Can list tables
- ✅ Tables match expected schema

**Expected Output:**
```
Tables: ['production_data', 'wellbores_data', 'wells_data']
```

**If it fails:**
- Check database is running: `docker-compose ps dev-postgres-db`
- Verify environment variables
- Check network connectivity

---

### Test 2: Tool Definitions

**Purpose**: Verify all tools in this MCP Server are properly defined

```bash
docker-compose run --rm dev-mcp-server python -c \
  "import sys; sys.path.insert(0, '/app'); \
   from tools.database_tools import get_database_tools; \
   tools = get_database_tools(); \
   print(f'Found {len(tools)} tools'); \
   [print(f'  - {t.name}') for t in tools]"
```

**What to check:**
- ✅ All 8 tools are defined
- ✅ Each tool has proper schema
- ✅ Descriptions are clear

**Expected Output:**
```
Found 8 tools
  - query_production_data
  - get_well_statistics
  - query_wells_by_location
  - detect_production_anomalies
  - get_well_details
  - get_wellbore_details
  - list_all_wells
  - get_database_schema
```

---

### Test 3: Tool Execution

**Purpose**: Verify the tools in this MCP Server actually work

```bash
docker-compose run --rm dev-mcp-server python -c "
import sys, asyncio
sys.path.insert(0, '/app')
from tools.database_tools import handle_list_all_wells

async def test():
    result = await handle_list_all_wells({'limit': 3})
    print(result[0].text[:500])  # First 500 chars

asyncio.run(test())
"
```

**What to check:**
- ✅ Handler executes without errors
- ✅ Returns proper format (TextContent)
- ✅ Data is correct

**Expected Output:**
```json
[
  {
    "well_legal_name": "15/9-F-1",
    "geo_latitude": 58.4333,
    "geo_longitude": 1.8833,
    ...
  },
  ...
]
```

---

### Test 4: Server Startup

**Purpose**: Verify the Volve Wells MCP Server can start and accept connections

```bash
# Start server in background
docker-compose up -d dev-mcp-server

# Check it's running
docker-compose ps dev-mcp-server

# View logs
docker-compose logs dev-mcp-server
```

**What to check:**
- ✅ Container starts successfully
- ✅ No error messages in logs
- ✅ Server is waiting for input (stdio)

**Note**: The server will appear to "hang" - this is normal! It's waiting for stdio input.

---

### Test 5: MCP Inspector (Full Protocol Test)

**Purpose**: Test the complete MCP protocol with this MCP Server

**Step 1: Install MCP Inspector**
```bash
npx @modelcontextprotocol/inspector
```

**Step 2: Connect to Server**

In MCP Inspector, configure:
- **Transport**: stdio
- **Command**: `docker exec -i <container-name> python -m mcp_server.server`

**Step 3: Test Tool Listing**

Send this JSON-RPC request:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/list"
}
```

**Expected Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "tools": [
      {
        "name": "query_production_data",
        "description": "Query production data...",
        "inputSchema": {...}
      },
      ...
    ]
  }
}
```

**Step 4: Test Tool Call**

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "list_all_wells",
    "arguments": {
      "limit": 5
    }
  }
}
```

**Expected Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "[{\"well_legal_name\": \"15/9-F-1\", ...}]"
      }
    ]
  }
}
```

---

### Test 6: Integration with LLM Client

**Purpose**: Test with actual LLM (Claude Desktop, Cursor, etc.)

**Step 1: Configure Client**

For Claude Desktop, edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "volve-wells": {
      "command": "docker",
      "args": [
        "exec",
        "-i",
        "data-engineering-project-volve-wells-dashboard-dev-mcp-server-1",
        "python",
        "-m",
        "mcp_server.server"
      ]
    }
  }
}
```

**Step 2: Restart Client**

Restart Claude Desktop to load the configuration.

**Step 3: Test with Natural Language**

Ask Claude:
- "List all the wells in the database"
- "What's the production data for well NO 15/9-F-1 C?"
- "Find wells near latitude 58.4, longitude 1.8"

**What to observe:**
- ✅ Claude understands the request
- ✅ Claude calls the right tool
- ✅ Claude gets the data
- ✅ Claude provides a helpful answer

---

### Test Checklist

Use this checklist to verify everything works:

- [ ] Database connection succeeds
- [ ] All 8 tools are defined
- [ ] Each tool can be executed
- [ ] Server starts without errors
- [ ] MCP Inspector can connect
- [ ] Tool listing works
- [ ] Tool execution works
- [ ] Error handling works (test invalid tool name)
- [ ] LLM client can connect
- [ ] LLM can use tools via natural language

---

## Key Concepts and Learning Outcomes

### Concepts Learned

1. **Protocol Design**
   - How standardized protocols enable interoperability
   - JSON-RPC 2.0 structure
   - Request/response patterns

2. **Async Programming**
   - Why async is important for I/O
   - How to write async handlers
   - Resource management with async context managers

3. **Security**
   - Parameterized queries (SQL injection prevention)
   - Input validation
   - Controlled access (tools vs. direct access)

4. **API Design**
   - Tool schema design
   - Descriptive tool names and descriptions
   - Error handling patterns

5. **System Integration**
   - Docker containerization
   - Service dependencies
   - Environment configuration

### Learning Outcomes

After studying the Volve Wells MCP Server implementation, you should understand:

✅ **What MCP is and why it exists**
- Standardized protocol for LLM integration
- Enables safe, controlled access to systems

✅ **How MCP servers work**
- Tool definition and registration
- Protocol communication (JSON-RPC)
- Request/response handling

✅ **How to implement an MCP server**
- Database layer design
- Tool definition patterns
- Server setup and configuration

✅ **How to test MCP servers**
- Component testing
- Protocol testing
- Integration testing

✅ **Best practices**
- Security (parameterized queries)
- Error handling
- Code organization
- Documentation

### Next Steps for Learning

1. **Add More Tools**: Create new tools for different operations
2. **Add Resources**: Implement resource providers (not just tools)
3. **Error Handling**: Improve error messages and recovery
4. **Performance**: Add caching, connection pooling optimizations
5. **Monitoring**: Add logging and metrics
6. **Authentication**: Add security layers
7. **Testing**: Write automated test suite

### Common Pitfalls to Avoid

❌ **SQL Injection**: Never concatenate user input into SQL
✅ **Solution**: Always use parameterized queries

❌ **Poor Tool Descriptions**: Vague descriptions confuse LLMs
✅ **Solution**: Write clear, detailed descriptions

❌ **Synchronous I/O**: Blocking operations slow down the server
✅ **Solution**: Use async/await for all I/O operations

❌ **No Error Handling**: Crashes break the protocol
✅ **Solution**: Catch exceptions and return proper error codes

❌ **Hardcoded Values**: Makes deployment difficult
✅ **Solution**: Use environment variables for configuration

---

## Summary

An MCP server is a **bridge** between LLMs and your systems. It:

1. **Exposes tools** that LLMs can call
2. **Handles protocol** communication (JSON-RPC)
3. **Executes operations** safely and securely
4. **Returns results** in a format LLMs understand

The Volve Wells MCP Server implementation demonstrates:
- ✅ Clean architecture (separation of concerns)
- ✅ Security best practices (parameterized queries)
- ✅ Proper error handling
- ✅ Docker integration
- ✅ Comprehensive testing

By understanding the Volve Wells MCP Server implementation, you've learned how to:
- Build MCP servers for your own use cases
- Integrate LLMs with your applications
- Create safe, controlled interfaces for AI systems

---

## Additional Resources

- [MCP Specification](https://modelcontextprotocol.io/)
- [MCP Python SDK Documentation](https://github.com/modelcontextprotocol/python-sdk)
- [JSON-RPC 2.0 Specification](https://www.jsonrpc.org/specification)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)

---

*This guide is part of the Volve Wells AI Platform project, demonstrating MCP, LLM and agentic AI concepts through practical implementation.*
