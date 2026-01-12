# MCP Server for Volve Wells Database Queries

This MCP (Model Context Protocol) server exposes database query tools for the Volve Wells Dashboard, allowing LLMs to interact with the PostgreSQL database through a standardized protocol.

## Overview

The MCP server provides a set of tools that enable natural language interactions with the Volve wells production database. It implements the Model Context Protocol, which allows AI assistants and LLMs to query and analyze well data programmatically.

## Features

The server exposes the following tools:

1. **query_production_data** - Query production data with filters for wellbore, date ranges, and limits
2. **get_well_statistics** - Get statistical summaries (totals, averages, min/max) for wells
3. **query_wells_by_location** - Find wells within a geographic radius
4. **detect_production_anomalies** - Detect statistical anomalies in production metrics
5. **get_well_details** - Get detailed information about a specific well
6. **get_wellbore_details** - Get detailed information about a specific wellbore
7. **list_all_wells** - List all wells in the database
8. **get_database_schema** - Get schema information for database tables

## Architecture

```
mcp_server/
├── __init__.py
├── server.py              # Main MCP server implementation
├── database.py            # Database connection and query utilities
├── tools/
│   ├── __init__.py
│   └── database_tools.py  # Tool definitions and handlers
├── Dockerfile
├── requirements.txt
└── README.md
```

## Setup

### Prerequisites

- Python 3.11+
- PostgreSQL database (running via docker-compose)
- MCP Python SDK

### Installation

1. **Using Docker (Recommended)**

   The MCP server is included in the docker-compose setup:

   ```bash
   docker-compose build dev-mcp-server
   docker-compose up dev-mcp-server
   ```

2. **Local Development**

   ```bash
   cd mcp_server
   pip install -r requirements.txt
   ```

### Environment Variables

The server uses the following environment variables (set automatically in docker-compose):

- `DB_HOST` - PostgreSQL host (default: `dev-postgres-db`)
- `DB_PORT` - PostgreSQL port (default: `5432`)
- `DB_NAME` - Database name (default: `postgres`)
- `DB_USER` - Database user (default: `postgres`)
- `DB_PASSWORD` - Database password (default: `postgres`)

## Usage

### Running the Server

The MCP server communicates via stdio (standard input/output), which is the standard MCP transport protocol.

**With Docker:**
```bash
docker-compose up dev-mcp-server
```

**Locally:**
```bash
python -m mcp_server.server
```

### Connecting to the Server

The server uses stdio transport, so it's typically invoked by MCP clients. To test the server, you can use the MCP Inspector:

```bash
npx @modelcontextprotocol/inspector
```

Or connect from an MCP-compatible client (like Claude Desktop, Cursor, etc.) by configuring the server path.

### Example Tool Calls

Once connected, you can call tools like:

**Query Production Data:**
```json
{
  "name": "query_production_data",
  "arguments": {
    "wellbore_name": "NO 15/9-F-1 C",
    "start_date": "2016-01-01",
    "end_date": "2016-12-31",
    "limit": 100
  }
}
```

**Get Well Statistics:**
```json
{
  "name": "get_well_statistics",
  "arguments": {
    "well_legal_name": "15/9-F-1",
    "start_date": "2016-01-01",
    "end_date": "2016-12-31"
  }
}
```

**Detect Anomalies:**
```json
{
  "name": "detect_production_anomalies",
  "arguments": {
    "metric": "boreoilvol",
    "threshold_std": 2.5,
    "start_date": "2016-01-01"
  }
}
```

## Integration with LLMs

This MCP server can be integrated with:

- **Claude Desktop** - Add to MCP settings
- **Cursor** - Configure as MCP server
- **Custom Applications** - Use MCP client libraries

### Example Integration (Claude Desktop)

Add to your Claude Desktop MCP settings (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

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

## Development

### Project Structure

- `server.py` - Main server entry point, handles MCP protocol
- `database.py` - Database connection management and query execution
- `tools/database_tools.py` - Tool definitions and async handlers

### Adding New Tools

1. Define the tool in `tools/database_tools.py`:
   ```python
   Tool(
       name="my_new_tool",
       description="Tool description",
       inputSchema={...}
   )
   ```

2. Create an async handler function:
   ```python
   async def handle_my_new_tool(arguments: Dict[str, Any]) -> List[TextContent]:
       # Implementation
       return [TextContent(type="text", text=json.dumps(result))]
   ```

3. Register the handler in `TOOL_HANDLERS`:
   ```python
   TOOL_HANDLERS = {
       ...
       "my_new_tool": handle_my_new_tool,
   }
   ```

### Testing

Test individual tools by running the server and using the MCP Inspector or a test client.

## Security Considerations

- The server currently uses read-only queries (no INSERT/UPDATE/DELETE)
- All queries use parameterized statements to prevent SQL injection
- Database credentials are passed via environment variables
- Consider adding authentication/authorization for production use

## Troubleshooting

**Server won't start:**
- Check database connection: Ensure PostgreSQL is running and accessible
- Verify environment variables are set correctly
- Check Docker logs: `docker-compose logs dev-mcp-server`

**Tools not working:**
- Ensure the database has been populated (run the Luigi workflow first)
- Check database schema matches expected structure
- Review server logs for error messages

**Connection issues:**
- Verify the database is healthy: `docker-compose ps`
- Test database connection manually
- Check network connectivity between containers

## Next Steps

This MCP server foundation enables:
- Natural language query interfaces
- Agentic AI systems that can reason about well data
- Automated data analysis and reporting
- Integration with LLM-powered dashboards

See the main project README for ideas on building LLM and agentic AI features on top of this MCP server.

## License

Same as the main project.
