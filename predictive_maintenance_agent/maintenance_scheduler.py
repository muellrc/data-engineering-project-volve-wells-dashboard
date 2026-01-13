"""
Maintenance work order scheduling logic.
Creates and manages maintenance schedules in SAP PM simulation.
"""
from typing import Dict, List, Any, Optional
from datetime import date, timedelta
from .database import get_db_manager
from .predictive_models import MaintenancePrediction, MaintenanceType, Priority


class MaintenanceScheduler:
    """Schedules maintenance work orders."""
    
    def __init__(self):
        """Initialize scheduler."""
        self.db = get_db_manager()
    
    def create_work_orders_from_predictions(
        self,
        predictions: List[MaintenancePrediction],
        auto_schedule: bool = True
    ) -> List[Dict[str, Any]]:
        """Create work orders from predictions."""
        created_orders = []
        
        for prediction in predictions:
            # Check if similar work order already exists
            existing = self._check_existing_work_order(prediction)
            if existing:
                continue  # Skip if already scheduled
            
            # Calculate scheduled date
            if auto_schedule:
                scheduled_date = self._calculate_scheduled_date(prediction)
            else:
                scheduled_date = prediction.predicted_failure_date - timedelta(days=7)
            
            # Create work order
            work_order_id = self.db.create_work_order(
                well_legal_name=prediction.well_legal_name,
                wellbore_name=prediction.wellbore_name,
                maintenance_type=prediction.maintenance_type.value,
                priority=prediction.priority.value,
                scheduled_date=scheduled_date,
                estimated_duration_hours=prediction.estimated_duration_hours,
                description=prediction.recommended_action,
                predicted_failure_date=prediction.predicted_failure_date,
                confidence_score=prediction.confidence_score
            )
            
            created_orders.append({
                "work_order_id": work_order_id,
                "well_legal_name": prediction.well_legal_name,
                "scheduled_date": scheduled_date.isoformat(),
                "priority": prediction.priority.value,
                "maintenance_type": prediction.maintenance_type.value
            })
        
        return created_orders
    
    def _check_existing_work_order(self, prediction: MaintenancePrediction) -> bool:
        """Check if similar work order already exists."""
        existing = self.db.get_work_orders(
            well_legal_name=prediction.well_legal_name,
            status="scheduled"
        )
        
        # Check for similar scheduled maintenance within 30 days
        for order in existing:
            scheduled = order["scheduled_date"]
            if isinstance(scheduled, str):
                scheduled = date.fromisoformat(scheduled)
            
            days_diff = abs((scheduled - date.today()).days)
            if days_diff < 30 and order["maintenance_type"] == prediction.maintenance_type.value:
                return True
        
        return False
    
    def _calculate_scheduled_date(self, prediction: MaintenancePrediction) -> date:
        """Calculate optimal scheduled date for maintenance."""
        # Schedule 1 week before predicted failure, but not in the past
        target_date = prediction.predicted_failure_date - timedelta(days=7)
        
        if target_date < date.today():
            # If target is in past, schedule for next week
            target_date = date.today() + timedelta(days=7)
        
        # Adjust for priority (critical gets scheduled sooner)
        if prediction.priority == Priority.CRITICAL:
            target_date = min(target_date, date.today() + timedelta(days=3))
        elif prediction.priority == Priority.HIGH:
            target_date = min(target_date, date.today() + timedelta(days=7))
        
        return target_date
    
    def get_upcoming_maintenance(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get upcoming maintenance schedules."""
        return self.db.get_work_orders(status="scheduled")
