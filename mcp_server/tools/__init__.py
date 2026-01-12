# MCP Tools module
try:
    from .database_tools import get_database_tools, TOOL_HANDLERS
except ImportError:
    # Fallback for when running as script
    from database_tools import get_database_tools, TOOL_HANDLERS

__all__ = ["get_database_tools", "TOOL_HANDLERS"]
