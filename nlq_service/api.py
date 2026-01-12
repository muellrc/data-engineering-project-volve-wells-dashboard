"""
FastAPI application for Natural Language Query service.
Provides REST API endpoints for converting natural language to SQL and executing queries.
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import logging

from .database import get_db_manager
from .llm_client import LLMClient
from .sql_validator import SQLValidator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Volve Wells Natural Language Query API",
    description="Convert natural language questions to SQL queries and execute them safely",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response models
class QueryRequest(BaseModel):
    """Request model for natural language query."""
    question: str = Field(..., description="Natural language question about the data")
    include_explanation: bool = Field(True, description="Include explanation of the generated SQL")
    max_results: int = Field(100, ge=1, le=1000, description="Maximum number of results to return")


class QueryResponse(BaseModel):
    """Response model for query execution."""
    question: str
    sql: str
    explanation: Optional[str] = None
    results: List[Dict[str, Any]]
    row_count: int
    execution_time_ms: float
    model_info: Optional[Dict[str, str]] = None


class SQLValidationResponse(BaseModel):
    """Response model for SQL validation."""
    is_valid: bool
    error_message: Optional[str] = None
    sanitized_sql: Optional[str] = None


# Initialize services
db_manager = get_db_manager()
llm_client = LLMClient()
sql_validator = SQLValidator()


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "Volve Wells Natural Language Query API",
        "version": "0.1.0",
        "endpoints": {
            "/query": "POST - Convert natural language to SQL and execute",
            "/validate-sql": "POST - Validate SQL query without executing",
            "/schema": "GET - Get database schema information",
            "/health": "GET - Health check"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Test database connection
        tables = db_manager.get_all_tables()
        return {
            "status": "healthy",
            "database": "connected",
            "tables": len(tables)
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")


@app.get("/schema")
async def get_schema():
    """Get database schema information."""
    try:
        tables = db_manager.get_all_tables()
        schema_info = {}
        
        for table in tables:
            columns = db_manager.get_table_schema(table)
            schema_info[table] = [
                {
                    "name": col["column_name"],
                    "type": col["data_type"],
                    "nullable": col["is_nullable"] == "YES"
                }
                for col in columns
            ]
        
        return {
            "tables": schema_info,
            "table_count": len(tables)
        }
    except Exception as e:
        logger.error(f"Error getting schema: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving schema: {str(e)}")


@app.post("/query", response_model=QueryResponse)
async def execute_natural_language_query(request: QueryRequest):
    """
    Convert natural language question to SQL and execute it.
    
    This endpoint:
    1. Takes a natural language question
    2. Uses LLM to generate SQL query
    3. Validates the SQL for safety
    4. Executes the query
    5. Returns results
    """
    import time
    start_time = time.time()
    
    try:
        # Get database schema context
        schema_context = db_manager.get_database_schema_context()
        
        # Generate SQL from natural language
        logger.info(f"Generating SQL for question: {request.question}")
        llm_result = llm_client.generate_sql(
            natural_language_query=request.question,
            schema_context=schema_context
        )
        
        generated_sql = llm_result["sql"]
        explanation = llm_result.get("explanation", "")
        
        # Clean up SQL (remove markdown code blocks if present)
        if generated_sql.startswith("```"):
            # Remove markdown code blocks
            lines = generated_sql.split("\n")
            generated_sql = "\n".join([l for l in lines if not l.strip().startswith("```")])
        
        generated_sql = generated_sql.strip()
        
        # Validate SQL
        is_valid, error_message = sql_validator.validate_query(generated_sql)
        if not is_valid:
            logger.warning(f"Invalid SQL generated: {error_message}")
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Generated SQL query is not safe to execute",
                    "reason": error_message,
                    "generated_sql": generated_sql
                }
            )
        
        # Sanitize query
        sanitized_sql = sql_validator.sanitize_query(generated_sql)
        
        # Add LIMIT if not present and max_results is specified
        if request.max_results and "LIMIT" not in sanitized_sql.upper():
            sanitized_sql = f"{sanitized_sql} LIMIT {request.max_results}"
        
        # Execute query
        logger.info(f"Executing SQL: {sanitized_sql[:100]}...")
        results = db_manager.execute_query(sanitized_sql)
        
        execution_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        return QueryResponse(
            question=request.question,
            sql=sanitized_sql,
            explanation=explanation if request.include_explanation else None,
            results=results,
            row_count=len(results),
            execution_time_ms=round(execution_time, 2),
            model_info={
                "provider": llm_result.get("provider", "unknown"),
                "model": llm_result.get("model", "unknown")
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing query: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}"
        )


@app.post("/validate-sql", response_model=SQLValidationResponse)
async def validate_sql(sql: str = Query(..., description="SQL query to validate")):
    """
    Validate a SQL query without executing it.
    
    Useful for testing SQL generation or validating user-provided queries.
    """
    try:
        is_valid, error_message = sql_validator.validate_query(sql)
        sanitized = sql_validator.sanitize_query(sql) if is_valid else None
        
        return SQLValidationResponse(
            is_valid=is_valid,
            error_message=error_message,
            sanitized_sql=sanitized
        )
    except Exception as e:
        logger.error(f"Error validating SQL: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error validating SQL: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
