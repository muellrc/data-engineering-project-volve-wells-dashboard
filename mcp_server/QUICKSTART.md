# MCP Server Quick Start Guide

## Quick Setup

1. **Build and start the MCP server:**
   ```bash
   docker-compose build dev-mcp-server
   docker-compose up dev-mcp-server
   ```

2. **Verify the server is running:**
   ```bash
   docker-compose ps dev-mcp-server
   ```

## Testing with MCP Inspector

1. **Install MCP Inspector:**
   ```bash
   npx @modelcontextprotocol/inspector
   ```

2. **Connect to the server:**
   - Use stdio transport
   - Command: `docker exec -i <container-name> python -m mcp_server.server`
   - Or run locally: `python -m mcp_server.server`

## Available Tools

Once connected, you can use these tools:

- `query_production_data` - Query production data
- `get_well_statistics` - Get statistical summaries
- `query_wells_by_location` - Find wells by location
- `detect_production_anomalies` - Detect anomalies
- `get_well_details` - Get well information
- `get_wellbore_details` - Get wellbore information
- `list_all_wells` - List all wells
- `get_database_schema` - Get table schemas

## Example: Query Production Data

```python
# Tool call example
{
  "name": "query_production_data",
  "arguments": {
    "wellbore_name": "NO 15/9-F-1 C",
    "start_date": "2016-01-01",
    "end_date": "2016-12-31",
    "limit": 50
  }
}
```

## Troubleshooting

- **Database not accessible:** Make sure PostgreSQL is running and healthy
- **Import errors:** Verify all dependencies are installed
- **Connection issues:** Check environment variables and network connectivity

For more details, see [README.md](README.md).
