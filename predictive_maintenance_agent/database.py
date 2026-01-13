"""
Database connection and maintenance work order management.
Simulates SAP Plant Maintenance system.
"""
import os
from typing import Dict, List, Any, Optional
from datetime import datetime, date
from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool


class DatabaseManager:
    """Manages database connections and maintenance work orders."""
    
    def __init__(self):
        """Initialize database connection."""
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = os.getenv("DB_PORT", "5432")
        db_name = os.getenv("DB_NAME", "postgres")
        db_user = os.getenv("DB_USER", "postgres")
        db_password = os.getenv("DB_PASSWORD", "postgres")
        
        connection_string = (
            f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        )
        
        self.engine = create_engine(
            connection_string,
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10
        )
    
    def get_connection(self):
        """Get database connection."""
        return self.engine.connect()
    
    def execute_query(self, query: str, params: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Execute a query and return results."""
        with self.get_connection() as conn:
            result = conn.execute(text(query), params or {})
            columns = result.keys()
            rows = result.fetchall()
            return [dict(zip(columns, row)) for row in rows]
    
    def get_production_data(self, well_legal_name: Optional[str] = None, 
                           days: int = 90) -> List[Dict[str, Any]]:
        """Get recent production data for analysis."""
        query = """
            SELECT 
                p.wellbore,
                p.productiontime as date_on_production,
                p.boreoilvol as oil_prod,
                p.boregasvol as gas_prod,
                p.borewatvol as water_prod,
                p.borewivol as water_inj,
                wb.well_legal_name
            FROM production_data p
            LEFT JOIN wellbores_data wb ON p.wellbore = wb.wellbore_name
            WHERE p.productiontime >= CURRENT_DATE - INTERVAL ':days days'
        """
        
        if well_legal_name:
            query += " AND wb.well_legal_name = :well_legal_name"
        
        query += " ORDER BY p.productiontime DESC"
        
        params = {"days": days}
        if well_legal_name:
            params["well_legal_name"] = well_legal_name
        
        return self.execute_query(query, params)
    
    def get_well_statistics(self, well_legal_name: str, days: int = 90) -> Dict[str, Any]:
        """Get statistical summary for a well."""
        query = """
            SELECT 
                COUNT(*) as data_points,
                AVG(p.boreoilvol) as avg_oil_prod,
                AVG(p.boregasvol) as avg_gas_prod,
                AVG(p.borewatvol) as avg_water_prod,
                MIN(p.boreoilvol) as min_oil_prod,
                MAX(p.boreoilvol) as max_oil_prod,
                STDDEV(p.boreoilvol) as stddev_oil_prod,
                MAX(p.productiontime) as last_production_date
            FROM production_data p
            LEFT JOIN wellbores_data wb ON p.wellbore = wb.wellbore_name
            WHERE wb.well_legal_name = :well_legal_name
            AND p.productiontime >= CURRENT_DATE - INTERVAL ':days days'
        """
        
        result = self.execute_query(query, {"well_legal_name": well_legal_name, "days": days})
        return result[0] if result else {}
    
    def create_work_order(
        self,
        well_legal_name: str,
        wellbore_name: Optional[str],
        maintenance_type: str,
        priority: str,
        scheduled_date: date,
        estimated_duration_hours: float,
        description: str,
        predicted_failure_date: Optional[date] = None,
        confidence_score: Optional[float] = None
    ) -> int:
        """Create a maintenance work order (SAP PM simulation)."""
        query = """
            INSERT INTO maintenance_work_orders (
                well_legal_name,
                wellbore_name,
                maintenance_type,
                priority,
                scheduled_date,
                estimated_duration_hours,
                description,
                predicted_failure_date,
                confidence_score,
                status
            ) VALUES (
                :well_legal_name,
                :wellbore_name,
                :maintenance_type,
                :priority,
                :scheduled_date,
                :estimated_duration_hours,
                :description,
                :predicted_failure_date,
                :confidence_score,
                'scheduled'
            )
            RETURNING work_order_id
        """
        
        result = self.execute_query(query, {
            "well_legal_name": well_legal_name,
            "wellbore_name": wellbore_name,
            "maintenance_type": maintenance_type,
            "priority": priority,
            "scheduled_date": scheduled_date,
            "estimated_duration_hours": estimated_duration_hours,
            "description": description,
            "predicted_failure_date": predicted_failure_date,
            "confidence_score": confidence_score
        })
        
        return result[0]["work_order_id"] if result else None
    
    def get_work_orders(
        self,
        well_legal_name: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get maintenance work orders."""
        query = "SELECT * FROM maintenance_work_orders WHERE 1=1"
        params = {}
        
        if well_legal_name:
            query += " AND well_legal_name = :well_legal_name"
            params["well_legal_name"] = well_legal_name
        
        if status:
            query += " AND status = :status"
            params["status"] = status
        
        query += " ORDER BY scheduled_date ASC, priority DESC LIMIT :limit"
        params["limit"] = limit
        
        return self.execute_query(query, params)
    
    def update_work_order_status(
        self,
        work_order_id: int,
        status: str,
        notes: Optional[str] = None
    ) -> bool:
        """Update work order status."""
        query = """
            UPDATE maintenance_work_orders
            SET status = :status,
                notes = COALESCE(:notes, notes),
                completed_at = CASE WHEN :status = 'completed' THEN CURRENT_TIMESTAMP ELSE completed_at END
            WHERE work_order_id = :work_order_id
        """
        
        self.execute_query(query, {
            "work_order_id": work_order_id,
            "status": status,
            "notes": notes
        })
        
        return True


_db_manager: Optional[DatabaseManager] = None


def get_db_manager() -> DatabaseManager:
    """Get singleton database manager instance."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager
