"""
Predictive Maintenance Agent.
Uses LLM reasoning to analyze wells and create maintenance schedules.
"""
import os
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, date
from .database import get_db_manager
from .predictive_models import PredictiveModel, MaintenancePrediction
from .agent_tools import AgentTools
from .maintenance_scheduler import MaintenanceScheduler


class LLMClient:
    """LLM client for agent reasoning."""
    
    def __init__(self):
        """Initialize LLM client."""
        self.provider = os.getenv("LLM_PROVIDER", "openai").lower()
        self.api_key = os.getenv("LLM_API_KEY")
        self.model = os.getenv("LLM_MODEL", self._get_default_model())
        self.base_url = os.getenv("LLM_BASE_URL")
        self._init_client()
    
    def _get_default_model(self) -> str:
        """Get default model for provider."""
        defaults = {
            "openai": "gpt-4o-mini",
            "anthropic": "claude-3-5-sonnet-20241022",
            "ollama": "llama3.1"
        }
        return defaults.get(self.provider, "gpt-4o-mini")
    
    def _init_client(self):
        """Initialize LLM client based on provider."""
        if self.provider == "openai":
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
            except ImportError:
                raise ImportError("openai package not installed")
        elif self.provider == "anthropic":
            try:
                from anthropic import Anthropic
                self.client = Anthropic(api_key=self.api_key)
            except ImportError:
                raise ImportError("anthropic package not installed")
        elif self.provider == "ollama":
            try:
                from openai import OpenAI
                base_url = self.base_url or "http://localhost:11434/v1"
                self.client = OpenAI(api_key="ollama", base_url=base_url)
            except ImportError:
                raise ImportError("openai package not installed")
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    def analyze_maintenance_strategy(
        self,
        predictions: List[Dict[str, Any]],
        well_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Use LLM to analyze maintenance strategy."""
        prompt = f"""Analyze these maintenance predictions and provide strategic recommendations:

Well: {well_context.get('well_legal_name')}
Data Points: {well_context.get('data_points', 0)}
Predictions: {len(predictions)}

Predictions Details:
{json.dumps(predictions, indent=2)}

Provide:
1. Priority assessment (which predictions are most critical)
2. Scheduling recommendations (optimal timing)
3. Resource allocation suggestions
4. Risk mitigation strategies
5. Cost-benefit analysis

Return as JSON with keys: priority_assessment, scheduling_recommendations, resource_allocation, risk_mitigation, cost_benefit
"""
        
        if self.provider == "anthropic":
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            content = response.content[0].text
        else:
            # OpenAI and Ollama use OpenAI-compatible API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a maintenance planning expert. Provide structured JSON responses."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"} if self.provider == "ollama" else None
            )
            content = response.choices[0].message.content
        
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {
                "analysis": content,
                "format": "text"
            }
    
    def generate_maintenance_report(
        self,
        work_orders: List[Dict[str, Any]],
        analysis: Dict[str, Any]
    ) -> str:
        """Generate maintenance report."""
        prompt = f"""Generate a comprehensive maintenance planning report in Markdown format.

Work Orders Created: {len(work_orders)}
Analysis: {json.dumps(analysis, indent=2)}

Generate:
- Executive Summary
- Maintenance Schedule Overview
- Priority Breakdown
- Resource Requirements
- Risk Assessment
- Recommendations
"""
        
        if self.provider == "anthropic":
            response = self.client.messages.create(
                model=self.model,
                max_tokens=3000,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            return response.content[0].text
        else:
            # OpenAI and Ollama use OpenAI-compatible API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a maintenance planning expert. Generate professional reports."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            return response.choices[0].message.content


class PredictiveMaintenanceAgent:
    """Intelligent agent for predictive maintenance."""
    
    def __init__(self):
        """Initialize the agent."""
        self.db = get_db_manager()
        self.predictive_model = PredictiveModel(self.db)
        self.agent_tools = AgentTools()
        self.scheduler = MaintenanceScheduler()
        self.llm_client = LLMClient() if os.getenv("LLM_API_KEY") else None
    
    def analyze_and_schedule(
        self,
        well_legal_name: Optional[str] = None,
        include_llm_reasoning: bool = True,
        auto_schedule: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze wells and create maintenance schedules.
        
        Args:
            well_legal_name: Specific well to analyze (None = all wells)
            include_llm_reasoning: Use LLM for strategic analysis
            auto_schedule: Automatically create work orders
            
        Returns:
            Complete analysis and scheduling results
        """
        # Step 1: Get wells to analyze
        if well_legal_name:
            wells = [{"well_legal_name": well_legal_name}]
        else:
            wells = self.agent_tools.get_well_list()
        
        # Step 2: Analyze each well
        all_predictions = []
        well_analyses = []
        
        for well in wells:
            well_name = well["well_legal_name"]
            analysis = self.agent_tools.analyze_well(well_name)
            well_analyses.append(analysis)
            
            # Convert predictions to MaintenancePrediction objects
            from .predictive_models import MaintenanceType, Priority
            for pred_dict in analysis["predictions"]:
                all_predictions.append(MaintenancePrediction(
                    well_legal_name=well_name,
                    wellbore_name=pred_dict.get("wellbore_name"),
                    maintenance_type=MaintenanceType(pred_dict["maintenance_type"]),
                    priority=Priority(pred_dict["priority"]),
                    predicted_failure_date=date.fromisoformat(pred_dict["predicted_failure_date"]),
                    confidence_score=pred_dict["confidence_score"],
                    reason=pred_dict["reason"],
                    recommended_action=pred_dict["recommended_action"],
                    estimated_duration_hours=pred_dict["estimated_duration_hours"]
                ))
        
        # Step 3: LLM reasoning (if available)
        llm_analysis = None
        if include_llm_reasoning and self.llm_client and well_analyses:
            # Analyze first well with most predictions
            main_analysis = max(well_analyses, key=lambda x: x["predictions_count"])
            if main_analysis["predictions"]:
                llm_analysis = self.llm_client.analyze_maintenance_strategy(
                    main_analysis["predictions"],
                    main_analysis
                )
        
        # Step 4: Create work orders
        work_orders = []
        if auto_schedule and all_predictions:
            work_orders = self.scheduler.create_work_orders_from_predictions(
                all_predictions,
                auto_schedule=True
            )
        
        # Step 5: Generate report
        report = None
        if self.llm_client and work_orders:
            report = self.llm_client.generate_maintenance_report(work_orders, llm_analysis or {})
        
        return {
            "timestamp": datetime.now().isoformat(),
            "wells_analyzed": len(wells),
            "total_predictions": len(all_predictions),
            "work_orders_created": len(work_orders),
            "well_analyses": well_analyses,
            "llm_analysis": llm_analysis,
            "work_orders": work_orders,
            "report": report
        }
    
    def get_maintenance_schedule(
        self,
        well_legal_name: Optional[str] = None,
        days_ahead: int = 90
    ) -> Dict[str, Any]:
        """Get current maintenance schedule."""
        schedules = self.agent_tools.get_existing_schedules(well_legal_name, days_ahead)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "schedules_count": len(schedules),
            "schedules": schedules
        }
