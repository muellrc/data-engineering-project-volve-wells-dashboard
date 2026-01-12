# MCP Server Testing Guide

## Quick Test Results

✅ **Database Connection**: Working
- Successfully connects to PostgreSQL
- Found 3 tables: `production_data`, `wellbores_data`, `wells_data`
- Production data table has 15,633 records

✅ **Tool Definitions**: Working
- All 8 tools are properly defined:
  - `query_production_data`
  - `get_well_statistics`
  - `query_wells_by_location`
  - `detect_production_anomalies`
  - `get_well_details`
  - `get_wellbore_details`
  - `list_all_wells`
  - `get_database_schema`

✅ **Server Module**: Working (when run as module)

## Testing Methods

### 1. Test Database Connection

```bash
docker-compose run --rm dev-mcp-server python -c \
  "import sys; sys.path.insert(0, '/app'); from database import get_db_manager; \
   db = get_db_manager(); print('Tables:', db.get_all_tables())"
```

### 2. Test Tool Definitions

```bash
docker-compose run --rm dev-mcp-server python -c \
  "import sys; sys.path.insert(0, '/app'); from tools.database_tools import get_database_tools; \
   tools = get_database_tools(); print(f'Found {len(tools)} tools')"
```

### 3. Test Server Startup

The server uses stdio transport, so it waits for input. To verify it starts:

```bash
# Start the server (it will wait for stdio input)
docker-compose up dev-mcp-server

# In another terminal, test with MCP Inspector
npx @modelcontextprotocol/inspector
```

### 4. Test with MCP Inspector

1. **Install MCP Inspector** (if not already installed):
   ```bash
   npx @modelcontextprotocol/inspector
   ```

2. **Connect to the server**:
   - Transport: stdio
   - Command: `docker exec -i <container-name> python -m mcp_server.server`
   - Or use the docker-compose service name

3. **Test a tool call**:
   ```json
   {
     "jsonrpc": "2.0",
     "id": 1,
     "method": "tools/list"
   }
   ```

### 5. Test Individual Tool

```bash
# Test query_production_data tool
docker-compose run --rm dev-mcp-server python -c "
import sys, asyncio
sys.path.insert(0, '/app')
from tools.database_tools import handle_query_production_data

async def test():
    result = await handle_query_production_data({'limit': 5})
    print(result[0].text[:500])

asyncio.run(test())
"
```

## Integration Testing

### Test with Claude Desktop

1. Add to Claude Desktop MCP config (`~/Library/Application Support/Claude/claude_desktop_config.json`):

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

2. Restart Claude Desktop
3. The tools should appear in Claude's available tools

### Test with Cursor

1. Add MCP server configuration in Cursor settings
2. Use the same docker exec command
3. Test by asking Claude questions about the wells data

## Expected Behavior

- ✅ Server starts without errors
- ✅ Database connection succeeds
- ✅ All 8 tools are available
- ✅ Tool calls return JSON data
- ✅ Error handling works for invalid inputs

## Troubleshooting

**Server won't start:**
- Check database is running: `docker-compose ps dev-postgres-db`
- Verify environment variables are set
- Check logs: `docker-compose logs dev-mcp-server`

**Tools not working:**
- Ensure database has data (run Luigi workflow first)
- Check database schema matches expected structure
- Verify tool handlers are registered correctly

**Import errors:**
- Server must be run as module: `python -m mcp_server.server`
- PYTHONPATH should include `/app` (set in Dockerfile)

## Next Steps

Once basic testing passes:
1. Test with actual LLM integration (Claude Desktop, Cursor)
2. Test error handling with invalid queries
3. Test performance with large queries
4. Add integration tests for each tool
