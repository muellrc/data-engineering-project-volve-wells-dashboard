"""
Tools available to the Predictive Maintenance Agent.
These tools allow the agent to investigate wells and create maintenance schedules.
"""
from typing import Dict, Any, List, Optional
from datetime import date, timedelta
from .database import get_db_manager
from .predictive_models import PredictiveModel, MaintenancePrediction


class AgentTools:
    """Tools that the agent can use to investigate and schedule maintenance."""
    
    def __init__(self):
        """Initialize agent tools."""
        self.db = get_db_manager()
        self.predictive_model = PredictiveModel(self.db)
    
    def analyze_well(self, well_legal_name: str, days: int = 90) -> Dict[str, Any]:
        """
        Analyze a well for maintenance needs.
        
        Args:
            well_legal_name: Legal name of the well
            days: Number of days of historical data to analyze
            
        Returns:
            Dictionary with analysis results and predictions
        """
        predictions = self.predictive_model.analyze_well(well_legal_name, days)
        stats = self.db.get_well_statistics(well_legal_name, days)
        
        return {
            "well_legal_name": well_legal_name,
            "analysis_period_days": days,
            "data_points": stats.get("data_points", 0),
            "predictions_count": len(predictions),
            "predictions": [
                {
                    "wellbore_name": p.wellbore_name,
                    "maintenance_type": p.maintenance_type.value,
                    "priority": p.priority.value,
                    "predicted_failure_date": p.predicted_failure_date.isoformat(),
                    "confidence_score": p.confidence_score,
                    "reason": p.reason,
                    "recommended_action": p.recommended_action,
                    "estimated_duration_hours": p.estimated_duration_hours
                }
                for p in predictions
            ],
            "statistics": stats
        }
    
    def get_well_list(self) -> List[Dict[str, str]]:
        """Get list of all wells."""
        query = """
            SELECT DISTINCT wb.well_legal_name
            FROM production_data p
            LEFT JOIN wellbores_data wb ON p.wellbore = wb.wellbore_name
            WHERE wb.well_legal_name IS NOT NULL
            ORDER BY wb.well_legal_name
        """
        results = self.db.execute_query(query)
        return [{"well_legal_name": r["well_legal_name"]} for r in results]
    
    def get_existing_schedules(
        self,
        well_legal_name: Optional[str] = None,
        days_ahead: int = 90
    ) -> List[Dict[str, Any]]:
        """Get existing maintenance schedules."""
        query = """
            SELECT *
            FROM maintenance_work_orders
            WHERE scheduled_date <= CURRENT_DATE + INTERVAL ':days days'
            AND status IN ('scheduled', 'in_progress')
        """
        
        params = {"days": days_ahead}
        if well_legal_name:
            query = query.replace("WHERE", "WHERE well_legal_name = :well_legal_name AND")
            params["well_legal_name"] = well_legal_name
        
        query += " ORDER BY scheduled_date ASC"
        
        return self.db.execute_query(query, params)
    
    def check_maintenance_history(
        self,
        well_legal_name: str,
        months: int = 12
    ) -> Dict[str, Any]:
        """Check maintenance history for a well."""
        query = """
            SELECT 
                COUNT(*) as total_work_orders,
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
                COUNT(CASE WHEN maintenance_type = 'predictive' THEN 1 END) as predictive,
                MAX(scheduled_date) as last_maintenance_date
            FROM maintenance_work_orders
            WHERE well_legal_name = :well_legal_name
            AND created_at >= CURRENT_DATE - INTERVAL ':months months'
        """
        
        results = self.db.execute_query(query, {
            "well_legal_name": well_legal_name,
            "months": months
        })
        
        return results[0] if results else {}
    
    def compare_wells(self, well_names: List[str]) -> Dict[str, Any]:
        """Compare multiple wells for maintenance prioritization."""
        comparisons = []
        
        for well_name in well_names:
            analysis = self.analyze_well(well_name)
            history = self.check_maintenance_history(well_name)
            
            comparisons.append({
                "well_legal_name": well_name,
                "predictions_count": analysis["predictions_count"],
                "high_priority_count": sum(
                    1 for p in analysis["predictions"]
                    if p["priority"] in ["high", "critical"]
                ),
                "last_maintenance": history.get("last_maintenance_date"),
                "total_maintenance_count": history.get("total_work_orders", 0)
            })
        
        # Sort by priority
        comparisons.sort(
            key=lambda x: (x["high_priority_count"], x["predictions_count"]),
            reverse=True
        )
        
        return {
            "wells_compared": len(well_names),
            "comparisons": comparisons,
            "recommended_priority_order": [c["well_legal_name"] for c in comparisons]
        }


TOOL_HANDLERS = {
    "analyze_well": lambda args: AgentTools().analyze_well(
        args.get("well_legal_name"),
        args.get("days", 90)
    ),
    "get_well_list": lambda args: AgentTools().get_well_list(),
    "get_existing_schedules": lambda args: AgentTools().get_existing_schedules(
        args.get("well_legal_name"),
        args.get("days_ahead", 90)
    ),
    "check_maintenance_history": lambda args: AgentTools().check_maintenance_history(
        args.get("well_legal_name"),
        args.get("months", 12)
    ),
    "compare_wells": lambda args: AgentTools().compare_wells(
        args.get("well_names", [])
    )
}
