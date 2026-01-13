"""
Simple test script for Predictive Maintenance Agent components.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_database():
    """Test database connection."""
    print("Testing database connection...")
    try:
        from database import get_db_manager
        db = get_db_manager()
        tables = db.execute_query("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        print(f"✅ Database connected. Found {len(tables)} tables")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_predictive_model():
    """Test predictive model."""
    print("\nTesting predictive model...")
    try:
        from database import get_db_manager
        from predictive_models import PredictiveModel
        
        db = get_db_manager()
        model = PredictiveModel(db)
        
        # Get first well
        wells = db.execute_query("""
            SELECT DISTINCT wb.well_legal_name
            FROM production_data p
            LEFT JOIN wellbores_data wb ON p.wellbore = wb.wellbore_name
            WHERE wb.well_legal_name IS NOT NULL
            LIMIT 1
        """)
        if wells:
            well_name = wells[0]["well_legal_name"]
            predictions = model.analyze_well(well_name, days=90)
            print(f"✅ Predictive model working. Found {len(predictions)} predictions for {well_name}")
            return True
        else:
            print("⚠️  No wells found in database")
            return False
    except Exception as e:
        print(f"❌ Predictive model test failed: {e}")
        return False

def test_agent_tools():
    """Test agent tools."""
    print("\nTesting agent tools...")
    try:
        from agent_tools import AgentTools
        
        tools = AgentTools()
        wells = tools.get_well_list()
        print(f"✅ Agent tools working. Found {len(wells)} wells")
        return True
    except Exception as e:
        print(f"❌ Agent tools test failed: {e}")
        return False

def test_scheduler():
    """Test maintenance scheduler."""
    print("\nTesting maintenance scheduler...")
    try:
        from maintenance_scheduler import MaintenanceScheduler
        
        scheduler = MaintenanceScheduler()
        upcoming = scheduler.get_upcoming_maintenance(days=30)
        print(f"✅ Scheduler working. Found {len(upcoming)} upcoming maintenance items")
        return True
    except Exception as e:
        print(f"❌ Scheduler test failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("Predictive Maintenance Agent - Simple Tests")
    print("=" * 50)
    
    results = [
        test_database(),
        test_predictive_model(),
        test_agent_tools(),
        test_scheduler()
    ]
    
    print("\n" + "=" * 50)
    print(f"Tests passed: {sum(results)}/{len(results)}")
    print("=" * 50)
