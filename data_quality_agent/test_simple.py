#!/usr/bin/env python3
"""
Simple test script that tests the Data Quality Agent components.
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
        return True
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_quality_checks():
    """Test quality check functionality."""
    print("\n🔍 Testing quality checks...")
    try:
        from quality_checks import DataQualityChecker
        from database import get_db_manager
        
        db = get_db_manager()
        checker = DataQualityChecker(db)
        
        # Test missing values check
        issues = checker.check_missing_values('production_data', ['wellbore'])
        print(f"  ✅ Missing values check works (found {len(issues)} issues)")
        
        # Test duplicate check
        issues = checker.check_duplicates('production_data', ['wellbore', 'productiontime'])
        print(f"  ✅ Duplicate check works (found {len(issues)} issues)")
        
        return True
    except Exception as e:
        print(f"❌ Quality checks test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_agent_tools():
    """Test agent tools."""
    print("\n🔍 Testing agent tools...")
    try:
        from agent_tools import AgentTools
        
        tools = AgentTools()
        
        # Test table investigation
        result = tools.investigate_table('production_data')
        print(f"  ✅ Table investigation works (found {result['issues_found']} issues)")
        
        # Test column investigation
        result = tools.investigate_column('production_data', 'wellbore')
        print(f"  ✅ Column investigation works")
        
        return True
    except Exception as e:
        print(f"❌ Agent tools test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_agent():
    """Test agent workflow."""
    print("\n🔍 Testing agent workflow...")
    try:
        from agent import DataQualityAgent
        
        agent = DataQualityAgent()
        
        # Test quality check
        results = agent.run_quality_check()
        print(f"  ✅ Agent quality check works (found {results['total_issues']} issues)")
        
        # Test without LLM
        print("  ℹ️  Testing agent analysis (without LLM)...")
        results = agent.analyze_and_report(include_llm_reasoning=False)
        print(f"  ✅ Agent analysis works (report length: {len(results.get('report', ''))})")
        
        return True
    except Exception as e:
        print(f"❌ Agent test failed: {e}")
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
    print("Data Quality Agent Simple Test Suite")
    print("=" * 60)
    
    db_ok = test_database()
    checks_ok = test_quality_checks()
    tools_ok = test_agent_tools()
    agent_ok = test_agent()
    api_ok = test_api_import()
    
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"Database: {'✅ PASS' if db_ok else '❌ FAIL'}")
    print(f"Quality Checks: {'✅ PASS' if checks_ok else '❌ FAIL'}")
    print(f"Agent Tools: {'✅ PASS' if tools_ok else '❌ FAIL'}")
    print(f"Agent Workflow: {'✅ PASS' if agent_ok else '❌ FAIL'}")
    print(f"API Module: {'✅ PASS' if api_ok else '❌ FAIL'}")
    
    if db_ok and checks_ok and tools_ok and agent_ok and api_ok:
        print("\n✅ All core components working! Data Quality Agent is ready.")
        print("\nNext steps:")
        print("1. Set LLM_API_KEY for LLM reasoning features")
        print("2. Build the Docker container: docker-compose build dev-data-quality-agent")
        print("3. Start the service: docker-compose up dev-data-quality-agent")
        print("4. Test API: curl http://localhost:8001/health")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed.")
        sys.exit(1)
