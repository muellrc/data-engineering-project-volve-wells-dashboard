"""
FastAPI application for Predictive Maintenance Agent.
Provides REST API endpoints for maintenance analysis and scheduling.
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import logging

from .database import get_db_manager
from .agent import PredictiveMaintenanceAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Predictive Maintenance Agent API",
    description="Autonomous agent for predictive maintenance scheduling",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalysisRequest(BaseModel):
    """Request model for maintenance analysis."""
    well_legal_name: Optional[str] = Field(None, description="Specific well to analyze (None = all wells)")
    include_llm_reasoning: bool = Field(True, description="Use LLM for strategic analysis")
    auto_schedule: bool = Field(True, description="Automatically create work orders")


class ScheduleRequest(BaseModel):
    """Request model for schedule query."""
    well_legal_name: Optional[str] = Field(None, description="Filter by well name")
    days_ahead: int = Field(90, ge=1, le=365, description="Days ahead to look")


db_manager = get_db_manager()
agent = PredictiveMaintenanceAgent()


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Predictive Maintenance Agent API",
        "version": "0.1.0",
        "endpoints": {
            "/analyze": "POST - Analyze wells and create maintenance schedules",
            "/schedule": "GET - Get maintenance schedules",
            "/work-orders": "GET - Get work orders",
            "/health": "GET - Health check"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        tables = db_manager.execute_query("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        return {
            "status": "healthy",
            "database": "connected",
            "tables": len(tables)
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")


@app.post("/analyze")
async def analyze_and_schedule(request: AnalysisRequest):
    """Analyze wells and create maintenance schedules."""
    try:
        result = agent.analyze_and_schedule(
            well_legal_name=request.well_legal_name,
            include_llm_reasoning=request.include_llm_reasoning,
            auto_schedule=request.auto_schedule
        )
        return result
    except Exception as e:
        logger.error(f"Error in analysis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing analysis: {str(e)}")


@app.get("/schedule")
async def get_schedule(
    well_legal_name: Optional[str] = Query(None),
    days_ahead: int = Query(90, ge=1, le=365)
):
    """Get maintenance schedules."""
    try:
        result = agent.get_maintenance_schedule(well_legal_name, days_ahead)
        return result
    except Exception as e:
        logger.error(f"Error getting schedule: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving schedule: {str(e)}")


@app.get("/work-orders")
async def get_work_orders(
    well_legal_name: Optional[str] = Query(None),
    status: Optional[str] = Query(None)
):
    """Get maintenance work orders."""
    try:
        work_orders = db_manager.get_work_orders(well_legal_name, status)
        return {
            "count": len(work_orders),
            "work_orders": work_orders
        }
    except Exception as e:
        logger.error(f"Error getting work orders: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving work orders: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
