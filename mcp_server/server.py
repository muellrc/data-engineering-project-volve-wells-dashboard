"""
MCP Server for Volve Wells Dashboard Database Queries.

This server exposes database query tools via the Model Context Protocol (MCP),
allowing LLMs to interact with the Volve wells production database.
"""
import asyncio
import sys
from typing import Any, Sequence
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolResult,
    ListToolsResult,
    Tool,
    TextContent,
)
from mcp import McpError

from .tools.database_tools import get_database_tools, TOOL_HANDLERS


# Create MCP server instance
app = Server("volve-wells-database")


@app.list_tools()
async def list_tools() -> ListToolsResult:
    """
    List all available tools.
    
    Returns:
        ListToolsResult containing all registered tools
    """
    tools = get_database_tools()
    return ListToolsResult(tools=tools)


@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any] | None) -> CallToolResult:
    """
    Handle tool execution requests.
    
    Args:
        name: Name of the tool to execute
        arguments: Tool arguments
        
    Returns:
        CallToolResult with tool execution results
    """
    if arguments is None:
        arguments = {}
    
    # Check if tool exists
    if name not in TOOL_HANDLERS:
        from mcp.types import METHOD_NOT_FOUND
        raise McpError(
            METHOD_NOT_FOUND,
            f"Tool '{name}' not found. Available tools: {', '.join(TOOL_HANDLERS.keys())}"
        )
    
    try:
        # Get the handler for this tool
        handler = TOOL_HANDLERS[name]
        
        # Execute the handler
        result = await handler(arguments)
        
        return CallToolResult(content=result)
    
    except Exception as e:
        from mcp.types import INTERNAL_ERROR
        error_msg = f"Error executing tool '{name}': {str(e)}"
        raise McpError(
            INTERNAL_ERROR,
            error_msg
        )


async def main():
    """
    Main entry point for the MCP server.
    Runs the server using stdio transport.
    """
    # Run the server using stdio transport
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
