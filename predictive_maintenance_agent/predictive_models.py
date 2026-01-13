"""
Predictive models for maintenance prediction.
Analyzes production data patterns to predict failures.
"""
from typing import Dict, List, Any, Optional
from datetime import datetime, date, timedelta
from dataclasses import dataclass
from enum import Enum


class MaintenanceType(str, Enum):
    """Types of maintenance."""
    PREVENTIVE = "preventive"
    CORRECTIVE = "corrective"
    PREDICTIVE = "predictive"


class Priority(str, Enum):
    """Maintenance priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class MaintenancePrediction:
    """Maintenance prediction result."""
    well_legal_name: str
    wellbore_name: Optional[str]
    maintenance_type: MaintenanceType
    priority: Priority
    predicted_failure_date: date
    confidence_score: float  # 0-100
    reason: str
    recommended_action: str
    estimated_duration_hours: float


class PredictiveModel:
    """Predictive model for maintenance scheduling."""
    
    def __init__(self, db_manager):
        """Initialize predictive model."""
        self.db = db_manager
    
    def analyze_well(self, well_legal_name: str, days: int = 90) -> List[MaintenancePrediction]:
        """Analyze a well and predict maintenance needs."""
        predictions = []
        
        # Get production data
        stats = self.db.get_well_statistics(well_legal_name, days)
        production_data = self.db.get_production_data(well_legal_name, days)
        
        if not stats or stats.get("data_points", 0) < 10:
            return predictions  # Not enough data
        
        # Check for declining production trend
        decline_prediction = self._check_production_decline(well_legal_name, production_data, stats)
        if decline_prediction:
            predictions.append(decline_prediction)
        
        # Check for abnormal patterns
        anomaly_prediction = self._check_anomalies(well_legal_name, production_data, stats)
        if anomaly_prediction:
            predictions.append(anomaly_prediction)
        
        # Check for equipment age/usage
        age_prediction = self._check_equipment_age(well_legal_name, stats)
        if age_prediction:
            predictions.append(age_prediction)
        
        return predictions
    
    def _check_production_decline(
        self,
        well_legal_name: str,
        production_data: List[Dict],
        stats: Dict[str, Any]
    ) -> Optional[MaintenancePrediction]:
        """Check for significant production decline."""
        if len(production_data) < 30:
            return None
        
        # Compare recent vs older production
        recent_days = min(14, len(production_data) // 2)
        recent_avg = sum(d.get("oil_prod", 0) or 0 for d in production_data[:recent_days]) / recent_days
        older_avg = sum(d.get("oil_prod", 0) or 0 for d in production_data[recent_days:recent_days*2]) / recent_days
        
        if older_avg == 0:
            return None
        
        decline_percentage = ((older_avg - recent_avg) / older_avg) * 100
        
        # If decline > 20%, predict maintenance
        if decline_percentage > 20:
            confidence = min(90, 50 + (decline_percentage - 20) * 2)
            days_until_failure = max(7, int(30 - decline_percentage))
            
            return MaintenancePrediction(
                well_legal_name=well_legal_name,
                wellbore_name=production_data[0].get("wellbore") if production_data else None,
                maintenance_type=MaintenanceType.PREDICTIVE,
                priority=Priority.HIGH if decline_percentage > 40 else Priority.MEDIUM,
                predicted_failure_date=date.today() + timedelta(days=days_until_failure),
                confidence_score=confidence,
                reason=f"Production decline of {decline_percentage:.1f}% detected over last {recent_days} days",
                recommended_action="Inspect well equipment, check for blockages or equipment degradation",
                estimated_duration_hours=8.0
            )
        
        return None
    
    def _check_anomalies(
        self,
        well_legal_name: str,
        production_data: List[Dict],
        stats: Dict[str, Any]
    ) -> Optional[MaintenancePrediction]:
        """Check for production anomalies."""
        if not stats.get("stddev_oil_prod"):
            return None
        
        avg_prod = stats.get("avg_oil_prod", 0) or 0
        stddev = stats.get("stddev_oil_prod", 0) or 0
        
        if stddev == 0:
            return None
        
        # Check for values > 2 standard deviations from mean
        anomalies = [
            d for d in production_data[:30]
            if d.get("oil_prod") and abs((d.get("oil_prod") or 0) - avg_prod) > 2 * stddev
        ]
        
        if len(anomalies) > 3:  # More than 3 anomalies in recent data
            return MaintenancePrediction(
                well_legal_name=well_legal_name,
                wellbore_name=production_data[0].get("wellbore") if production_data else None,
                maintenance_type=MaintenanceType.PREDICTIVE,
                priority=Priority.MEDIUM,
                predicted_failure_date=date.today() + timedelta(days=21),
                confidence_score=65.0,
                reason=f"Multiple production anomalies detected ({len(anomalies)} in last 30 days)",
                recommended_action="Investigate production variability, check sensors and equipment",
                estimated_duration_hours=6.0
            )
        
        return None
    
    def _check_equipment_age(
        self,
        well_legal_name: str,
        stats: Dict[str, Any]
    ) -> Optional[MaintenancePrediction]:
        """Check for equipment age-based maintenance."""
        last_prod_date = stats.get("last_production_date")
        if not last_prod_date:
            return None
        
        # Handle different date formats
        if isinstance(last_prod_date, str):
            # Try different date formats
            for fmt in ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"]:
                try:
                    last_prod_date = datetime.strptime(last_prod_date, fmt).date()
                    break
                except ValueError:
                    continue
            else:
                # If all formats fail, try parsing as datetime object
                try:
                    last_prod_date = datetime.fromisoformat(last_prod_date.replace('Z', '+00:00')).date()
                except:
                    return None
        elif isinstance(last_prod_date, datetime):
            last_prod_date = last_prod_date.date()
        
        days_since_last_prod = (date.today() - last_prod_date).days
        
        # If no production for > 60 days, suggest inspection
        if days_since_last_prod > 60:
            return MaintenancePrediction(
                well_legal_name=well_legal_name,
                wellbore_name=None,
                maintenance_type=MaintenanceType.PREVENTIVE,
                priority=Priority.LOW,
                predicted_failure_date=date.today() + timedelta(days=30),
                confidence_score=70.0,
                reason=f"No production data for {days_since_last_prod} days",
                recommended_action="Inspect well equipment and verify operational status",
                estimated_duration_hours=4.0
            )
        
        return None
