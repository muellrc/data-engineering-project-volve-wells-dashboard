#!/usr/bin/env python3
"""
Simple test script that tests the MCP server components.
Run this from within the container or with proper PYTHONPATH.
"""
import sys
import os

# Ensure we can import from the current directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_database():
    """Test database connection."""
    print("🔍 Testing database connection...")
    try:
        from database import get_db_manager
        db = get_db_manager()
        tables = db.get_all_tables()
        print(f"✅ Database connected! Found tables: {', '.join(tables)}")
        
        # Test a simple query
        result = db.execute_query("SELECT COUNT(*) as count FROM production_data LIMIT 1")
        if result:
            count = result[0].get('count', 0)
            print(f"✅ Production data table has {count} records")
        return True
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_tools():
    """Test tool definitions."""
    print("\n🔍 Testing tool definitions...")
    try:
        from tools.database_tools import get_database_tools
        tools = get_database_tools()
        print(f"✅ Found {len(tools)} tools:")
        for tool in tools:
            print(f"   - {tool.name}")
        return True
    except Exception as e:
        print(f"❌ Tools test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_server_import():
    """Test that server module can be imported."""
    print("\n🔍 Testing server module import...")
    try:
        # This should work when run as module
        import importlib
        server_module = importlib.import_module('mcp_server.server')
        print("✅ Server module imported successfully")
        return True
    except Exception as e:
        print(f"❌ Server import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("MCP Server Simple Test Suite")
    print("=" * 60)
    
    db_ok = test_database()
    tools_ok = test_tools()
    server_ok = test_server_import()
    
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"Database: {'✅ PASS' if db_ok else '❌ FAIL'}")
    print(f"Tools: {'✅ PASS' if tools_ok else '❌ FAIL'}")
    print(f"Server Import: {'✅ PASS' if server_ok else '❌ FAIL'}")
    
    if db_ok and tools_ok and server_ok:
        print("\n✅ All tests passed! MCP Server is ready.")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed.")
        sys.exit(1)
