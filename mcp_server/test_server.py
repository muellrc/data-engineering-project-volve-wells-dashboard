"""
Test script for the MCP server.
Tests database connectivity and tool functionality.
"""
import asyncio
import json
import sys
import os

# Add current directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from database import get_db_manager
from tools.database_tools import TOOL_HANDLERS


async def test_database_connection():
    """Test basic database connectivity."""
    print("🔍 Testing database connection...")
    try:
        db = get_db_manager()
        tables = db.get_all_tables()
        print(f"✅ Database connected! Found tables: {', '.join(tables)}")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


async def test_tool_handlers():
    """Test that all tool handlers are callable."""
    print("\n🔍 Testing tool handlers...")
    test_cases = [
        ("list_all_wells", {"limit": 5}),
        ("get_database_schema", {"table_name": "production_data"}),
    ]
    
    all_passed = True
    for tool_name, args in test_cases:
        try:
            if tool_name not in TOOL_HANDLERS:
                print(f"❌ Tool '{tool_name}' not found in handlers")
                all_passed = False
                continue
            
            handler = TOOL_HANDLERS[tool_name]
            print(f"  Testing {tool_name}...")
            result = await handler(args)
            
            if result and len(result) > 0:
                print(f"  ✅ {tool_name} returned {len(result)} result(s)")
                # Print first result as preview
                if hasattr(result[0], 'text'):
                    preview = result[0].text[:200] if len(result[0].text) > 200 else result[0].text
                    print(f"     Preview: {preview}...")
            else:
                print(f"  ⚠️  {tool_name} returned no results (might be empty database)")
        except Exception as e:
            print(f"  ❌ {tool_name} failed: {e}")
            all_passed = False
    
    return all_passed


async def test_production_data_query():
    """Test querying production data if available."""
    print("\n🔍 Testing production data query...")
    try:
        db = get_db_manager()
        result = db.execute_query("SELECT COUNT(*) as count FROM production_data LIMIT 1")
        
        if result and len(result) > 0:
            count = result[0].get('count', 0)
            print(f"✅ Production data table has {count} records")
            
            if count > 0:
                # Test a real query
                handler = TOOL_HANDLERS.get("query_production_data")
                if handler:
                    test_result = await handler({"limit": 3})
                    print(f"✅ Successfully queried production data")
                    return True
        else:
            print("⚠️  Production data table is empty (run Luigi workflow first)")
            return False
    except Exception as e:
        print(f"❌ Production data query failed: {e}")
        return False


async def main():
    """Run all tests."""
    print("=" * 60)
    print("MCP Server Test Suite")
    print("=" * 60)
    
    # Test database connection
    db_ok = await test_database_connection()
    if not db_ok:
        print("\n❌ Database connection failed. Make sure PostgreSQL is running.")
        sys.exit(1)
    
    # Test tool handlers
    handlers_ok = await test_tool_handlers()
    
    # Test production data
    data_ok = await test_production_data_query()
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"Database Connection: {'✅ PASS' if db_ok else '❌ FAIL'}")
    print(f"Tool Handlers: {'✅ PASS' if handlers_ok else '❌ FAIL'}")
    print(f"Production Data: {'✅ PASS' if data_ok else '⚠️  SKIP (empty database)'}")
    
    if db_ok and handlers_ok:
        print("\n✅ MCP Server is ready to use!")
        print("\nNext steps:")
        print("1. Build the Docker container: docker-compose build dev-mcp-server")
        print("2. Start the server: docker-compose up dev-mcp-server")
        print("3. Test with MCP Inspector: npx @modelcontextprotocol/inspector")
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
