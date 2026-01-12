"""
FastAPI application for Data Quality Agent service.
Provides REST API endpoints for data quality monitoring and reporting.
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime

from .agent import DataQualityAgent
from .quality_checks import QualitySeverity

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Volve Wells Data Quality Agent API",
    description="Intelligent agent for monitoring and analyzing data quality",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize agent
agent = DataQualityAgent()


# Request/Response models
class QualityCheckRequest(BaseModel):
    """Request model for quality check."""
    include_llm_reasoning: bool = Field(True, description="Include LLM reasoning in analysis")
    investigate_issues: bool = Field(True, description="Use agent tools to investigate issues")


class QualityCheckResponse(BaseModel):
    """Response model for quality check."""
    timestamp: str
    total_issues: int
    issues_by_severity: Dict[str, int]
    issues: List[Dict[str, Any]]
    investigation_results: Optional[List[Dict[str, Any]]] = None
    reasoning: Optional[Dict[str, Any]] = None
    report: Optional[str] = None


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "Volve Wells Data Quality Agent API",
        "version": "0.1.0",
        "endpoints": {
            "/check": "POST - Run data quality check",
            "/check/quick": "GET - Quick quality check (no LLM)",
            "/health": "GET - Health check",
            "/report": "GET - Get latest report"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        from .database import get_db_manager
        db = get_db_manager()
        tables = db.get_all_tables()
        return {
            "status": "healthy",
            "database": "connected",
            "tables": len(tables),
            "llm_available": agent.llm_client is not None
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")


@app.post("/check", response_model=QualityCheckResponse)
async def run_quality_check(request: QualityCheckRequest):
    """
    Run comprehensive data quality check with optional LLM reasoning.
    
    This endpoint:
    1. Runs all data quality checks
    2. Optionally investigates issues using agent tools
    3. Optionally uses LLM to reason about issues and generate report
    """
    try:
        logger.info("Running data quality check...")
        
        if request.investigate_issues and request.include_llm_reasoning:
            # Full analysis with LLM
            results = agent.analyze_and_report(include_llm_reasoning=request.include_llm_reasoning)
            
            return QualityCheckResponse(
                timestamp=results["timestamp"],
                total_issues=results["check_results"]["total_issues"],
                issues_by_severity=results["check_results"]["issues_by_severity"],
                issues=results["check_results"]["issues"],
                investigation_results=results["investigation_results"],
                reasoning=results["reasoning"],
                report=results["report"]
            )
        else:
            # Quick check without full investigation
            check_results = agent.run_quality_check()
            
            investigation_results = None
            if request.investigate_issues:
                from .quality_checks import QualityIssue
                issues = [QualityIssue(**issue) for issue in check_results["issues"]]
                investigation_results = agent.investigate_issues(issues)
            
            return QualityCheckResponse(
                timestamp=check_results["timestamp"],
                total_issues=check_results["total_issues"],
                issues_by_severity=check_results["issues_by_severity"],
                issues=check_results["issues"],
                investigation_results=investigation_results
            )
    
    except Exception as e:
        logger.error(f"Error running quality check: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error running quality check: {str(e)}"
        )


@app.get("/check/quick")
async def quick_check():
    """
    Quick data quality check without LLM reasoning.
    Faster but less detailed.
    """
    try:
        check_results = agent.run_quality_check()
        return check_results
    except Exception as e:
        logger.error(f"Error in quick check: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error in quick check: {str(e)}"
        )


@app.get("/report")
async def get_latest_report():
    """
    Get the latest data quality report.
    Runs a full analysis if no cached report exists.
    """
    try:
        # Run full analysis to generate report
        results = agent.analyze_and_report(include_llm_reasoning=agent.llm_client is not None)
        
        return {
            "timestamp": results["timestamp"],
            "report": results["report"],
            "summary": {
                "total_issues": results["check_results"]["total_issues"],
                "issues_by_severity": results["check_results"]["issues_by_severity"]
            }
        }
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating report: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
