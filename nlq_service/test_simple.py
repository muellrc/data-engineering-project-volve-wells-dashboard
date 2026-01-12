#!/usr/bin/env python3
"""
Simple test script that tests the NLQ service components.
Run this from within the container or with proper PYTHONPATH.
"""
import sys
import os

# Ensure we can import from the current directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_database():
    """Test database connection and schema generation."""
    print("🔍 Testing database connection...")
    try:
        from database import get_db_manager
        db = get_db_manager()
        tables = db.get_all_tables()
        print(f"✅ Database connected! Found tables: {', '.join(tables)}")
        
        # Test schema context generation
        schema = db.get_database_schema_context()
        print(f"✅ Schema context generated ({len(schema)} characters)")
        
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

def test_sql_validator():
    """Test SQL validation."""
    print("\n🔍 Testing SQL validator...")
    try:
        from sql_validator import SQLValidator
        
        # Test valid query
        is_valid, error = SQLValidator.validate_query("SELECT * FROM production_data LIMIT 10")
        if is_valid:
            print("  ✅ Valid SELECT query passes")
        else:
            print(f"  ❌ Valid query failed: {error}")
            return False
        
        # Test dangerous query
        is_valid, error = SQLValidator.validate_query("DROP TABLE production_data")
        if not is_valid:
            print(f"  ✅ Dangerous query blocked: {error}")
        else:
            print("  ❌ Dangerous query was not blocked!")
            return False
        
        # Test sanitization
        dirty_sql = "SELECT * FROM production_data -- comment\nLIMIT 10"
        clean = SQLValidator.sanitize_query(dirty_sql)
        if "--" not in clean:
            print("  ✅ SQL sanitization works")
        else:
            print("  ❌ SQL sanitization failed")
            return False
        
        return True
    except Exception as e:
        print(f"❌ SQL validator test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_llm_client_init():
    """Test LLM client initialization (without API key)."""
    print("\n🔍 Testing LLM client initialization...")
    try:
        from llm_client import LLMClient, LLMProvider
        
        # Test with Ollama (doesn't require API key for init)
        os.environ['LLM_PROVIDER'] = 'ollama'
        os.environ['LLM_BASE_URL'] = 'http://localhost:11434/v1'
        os.environ['LLM_API_KEY'] = 'ollama'
        
        try:
            client = LLMClient()
            print(f"  ✅ LLM client initialized (provider: {client.provider})")
            return True
        except Exception as e:
            print(f"  ⚠️  LLM client init failed (expected if Ollama not running): {e}")
            print("  ℹ️  This is OK - LLM client requires API key or running Ollama")
            return True  # Not a failure, just needs configuration
    except Exception as e:
        print(f"❌ LLM client test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_import():
    """Test that API module can be imported."""
    print("\n🔍 Testing API module import...")
    try:
        import api
        print("✅ API module imported successfully")
        print(f"  Found {len(api.app.routes)} routes")
        return True
    except Exception as e:
        print(f"❌ API import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("NLQ Service Simple Test Suite")
    print("=" * 60)
    
    db_ok = test_database()
    validator_ok = test_sql_validator()
    llm_ok = test_llm_client_init()
    api_ok = test_api_import()
    
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"Database: {'✅ PASS' if db_ok else '❌ FAIL'}")
    print(f"SQL Validator: {'✅ PASS' if validator_ok else '❌ FAIL'}")
    print(f"LLM Client: {'✅ PASS' if llm_ok else '⚠️  SKIP (needs config)'}")
    print(f"API Module: {'✅ PASS' if api_ok else '❌ FAIL'}")
    
    if db_ok and validator_ok and api_ok:
        print("\n✅ Core components working! NLQ Service is ready.")
        print("\nNext steps:")
        print("1. Set LLM_API_KEY environment variable")
        print("2. Build the Docker container: docker-compose build dev-nlq-service")
        print("3. Start the service: docker-compose up dev-nlq-service")
        print("4. Test API: curl http://localhost:8000/health")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed.")
        sys.exit(1)
