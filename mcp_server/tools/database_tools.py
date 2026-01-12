"""
MCP tools for querying the Volve Wells database.
These tools expose database functionality to LLMs via the MCP protocol.
"""
import json
import math
from typing import Any, Dict, List, Optional
from mcp.types import Tool, TextContent

# Handle both relative and absolute imports
import sys
import os
import importlib

# Determine if we're in a package or running as script
_current_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_current_dir)

if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

# Try different import strategies
try:
    # Try as package first
    database_module = importlib.import_module('mcp_server.database')
    get_db_manager = database_module.get_db_manager
except ImportError:
    try:
        # Try relative import (works when tools is a subpackage)
        database_module = importlib.import_module('..database', package='tools')
        get_db_manager = database_module.get_db_manager
    except (ImportError, ValueError):
        # Fallback for direct script execution
        database_module = importlib.import_module('database')
        get_db_manager = database_module.get_db_manager


def get_database_tools() -> List[Tool]:
    """
    Get list of MCP tools for database operations.
    
    Returns:
        List of Tool definitions
    """
    return [
        Tool(
            name="query_production_data",
            description=(
                "Query production data from the Volve wells. "
                "Returns production metrics including oil, gas, water volumes, and flow information. "
                "Use this to analyze production trends, find specific wellbores, or filter by date ranges."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "wellbore_name": {
                        "type": "string",
                        "description": "Optional: Filter by wellbore name (e.g., 'NO 15/9-F-1 C')"
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Optional: Start date in format 'YYYY-MM-DD'"
                    },
                    "end_date": {
                        "type": "string",
                        "description": "Optional: End date in format 'YYYY-MM-DD'"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Optional: Maximum number of results (default: 100, max: 1000)",
                        "default": 100
                    }
                }
            }
        ),
        Tool(
            name="get_well_statistics",
            description=(
                "Get statistical summary for a specific well or all wells. "
                "Returns aggregated metrics like total production, averages, min/max values. "
                "Useful for comparing wells or understanding overall production patterns."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "well_legal_name": {
                        "type": "string",
                        "description": "Optional: Filter by well legal name (e.g., '15/9-F-1')"
                    },
                    "wellbore_name": {
                        "type": "string",
                        "description": "Optional: Filter by wellbore name"
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Optional: Start date in format 'YYYY-MM-DD'"
                    },
                    "end_date": {
                        "type": "string",
                        "description": "Optional: End date in format 'YYYY-MM-DD'"
                    }
                }
            }
        ),
        Tool(
            name="query_wells_by_location",
            description=(
                "Find wells within a geographic area. "
                "Searches by latitude/longitude with a radius. "
                "Useful for finding wells in specific regions or analyzing geographic patterns."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "latitude": {
                        "type": "number",
                        "description": "Center latitude coordinate"
                    },
                    "longitude": {
                        "type": "number",
                        "description": "Center longitude coordinate"
                    },
                    "radius_km": {
                        "type": "number",
                        "description": "Search radius in kilometers (default: 10)",
                        "default": 10
                    }
                },
                "required": ["latitude", "longitude"]
            }
        ),
        Tool(
            name="detect_production_anomalies",
            description=(
                "Detect anomalies in production data. "
                "Identifies wells with unusual production patterns using statistical methods. "
                "Returns wells with production values that deviate significantly from normal patterns."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "metric": {
                        "type": "string",
                        "enum": ["boreoilvol", "boregasvol", "borewatvol", "borewivol"],
                        "description": "Production metric to analyze"
                    },
                    "threshold_std": {
                        "type": "number",
                        "description": "Standard deviation threshold for anomaly detection (default: 2.0)",
                        "default": 2.0
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Optional: Start date in format 'YYYY-MM-DD'"
                    },
                    "end_date": {
                        "type": "string",
                        "description": "Optional: End date in format 'YYYY-MM-DD'"
                    }
                },
                "required": ["metric"]
            }
        ),
        Tool(
            name="get_well_details",
            description=(
                "Get detailed information about a specific well including location, depth, and technical specifications. "
                "Returns well metadata from the wells_data table."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "well_legal_name": {
                        "type": "string",
                        "description": "Well legal name (e.g., '15/9-F-1')"
                    }
                },
                "required": ["well_legal_name"]
            }
        ),
        Tool(
            name="get_wellbore_details",
            description=(
                "Get detailed information about a specific wellbore including coordinates, depths, and rig information. "
                "Returns wellbore metadata from the wellbores_data table."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "wellbore_name": {
                        "type": "string",
                        "description": "Wellbore name (e.g., 'NO 15/9-F-1 C')"
                    }
                },
                "required": ["wellbore_name"]
            }
        ),
        Tool(
            name="list_all_wells",
            description=(
                "Get a list of all wells in the database with their legal names and basic information. "
                "Useful for discovering available wells or getting an overview."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 100)",
                        "default": 100
                    }
                }
            }
        ),
        Tool(
            name="get_database_schema",
            description=(
                "Get the schema information for database tables. "
                "Returns column names, data types, and constraints. "
                "Useful for understanding the database structure before writing queries."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "enum": ["production_data", "wells_data", "wellbores_data"],
                        "description": "Name of the table to get schema for"
                    }
                },
                "required": ["table_name"]
            }
        )
    ]


async def handle_query_production_data(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle query_production_data tool call."""
    db = get_db_manager()
    
    wellbore_name = arguments.get("wellbore_name")
    start_date = arguments.get("start_date")
    end_date = arguments.get("end_date")
    limit = min(arguments.get("limit", 100), 1000)
    
    query = "SELECT * FROM production_data WHERE 1=1"
    params = {}
    
    if wellbore_name:
        query += " AND wellbore = :wellbore_name"
        params["wellbore_name"] = wellbore_name
    
    if start_date:
        query += " AND productiontime >= :start_date"
        params["start_date"] = start_date
    
    if end_date:
        query += " AND productiontime <= :end_date"
        params["end_date"] = end_date
    
    query += f" ORDER BY productiontime DESC LIMIT {limit}"
    
    results = db.execute_query(query, params)
    
    import json
    return [TextContent(
        type="text",
        text=json.dumps(results, indent=2, default=str)
    )]


async def handle_get_well_statistics(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle get_well_statistics tool call."""
    db = get_db_manager()
    
    well_legal_name = arguments.get("well_legal_name")
    wellbore_name = arguments.get("wellbore_name")
    start_date = arguments.get("start_date")
    end_date = arguments.get("end_date")
    
    # Build query with joins to get well information
    query = """
        SELECT 
            COALESCE(w.well_legal_name, 'All Wells') as well_legal_name,
            COALESCE(p.wellbore, 'All Wellbores') as wellbore,
            COUNT(*) as record_count,
            SUM(p.boreoilvol) as total_oil_volume,
            AVG(p.boreoilvol) as avg_oil_volume,
            MIN(p.boreoilvol) as min_oil_volume,
            MAX(p.boreoilvol) as max_oil_volume,
            SUM(p.boregasvol) as total_gas_volume,
            AVG(p.boregasvol) as avg_gas_volume,
            SUM(p.borewatvol) as total_water_volume,
            AVG(p.borewatvol) as avg_water_volume,
            SUM(p.borewivol) as total_injected_water_volume,
            AVG(p.borewivol) as avg_injected_water_volume,
            MIN(p.productiontime) as first_production_date,
            MAX(p.productiontime) as last_production_date
        FROM production_data p
        LEFT JOIN wellbores_data wb ON p.wellbore = wb.wellbore_name
        LEFT JOIN wells_data w ON wb.well_legal_name = w.well_legal_name
        WHERE 1=1
    """
    params = {}
    
    if well_legal_name:
        query += " AND w.well_legal_name = :well_legal_name"
        params["well_legal_name"] = well_legal_name
    
    if wellbore_name:
        query += " AND p.wellbore = :wellbore_name"
        params["wellbore_name"] = wellbore_name
    
    if start_date:
        query += " AND p.productiontime >= :start_date"
        params["start_date"] = start_date
    
    if end_date:
        query += " AND p.productiontime <= :end_date"
        params["end_date"] = end_date
    
    query += " GROUP BY w.well_legal_name, p.wellbore"
    
    results = db.execute_query(query, params)
    
    import json
    return [TextContent(
        type="text",
        text=json.dumps(results, indent=2, default=str)
    )]


async def handle_query_wells_by_location(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle query_wells_by_location tool call."""
    db = get_db_manager()
    
    latitude = arguments["latitude"]
    longitude = arguments["longitude"]
    radius_km = arguments.get("radius_km", 10)
    
    # Convert radius from km to approximate degrees (rough approximation)
    # 1 degree latitude ≈ 111 km
    radius_deg = radius_km / 111.0
    
    query = """
        SELECT 
            w.*,
            SQRT(
                POW((w.geo_latitude - :lat) * 111, 2) + 
                POW((w.geo_longitude - :lon) * 111 * COS(RADIANS(w.geo_latitude)), 2)
            ) as distance_km
        FROM wells_data w
        WHERE 
            w.geo_latitude BETWEEN :min_lat AND :max_lat
            AND w.geo_longitude BETWEEN :min_lon AND :max_lon
        ORDER BY distance_km
    """
    
    params = {
        "lat": latitude,
        "lon": longitude,
        "min_lat": latitude - radius_deg,
        "max_lat": latitude + radius_deg,
        "min_lon": longitude - radius_deg,
        "max_lon": longitude + radius_deg
    }
    
    results = db.execute_query(query, params)
    
    # Filter by actual distance (more accurate)
    filtered_results = []
    for row in results:
        lat_diff = (row["geo_latitude"] - latitude) * 111
        lon_diff = (row["geo_longitude"] - longitude) * 111 * math.cos(math.radians(latitude))
        distance = math.sqrt(lat_diff**2 + lon_diff**2)
        if distance <= radius_km:
            row["distance_km"] = round(distance, 2)
            filtered_results.append(row)
    
    import json
    return [TextContent(
        type="text",
        text=json.dumps(filtered_results, indent=2, default=str)
    )]


async def handle_detect_production_anomalies(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle detect_production_anomalies tool call."""
    db = get_db_manager()
    
    metric = arguments["metric"]
    threshold_std = arguments.get("threshold_std", 2.0)
    start_date = arguments.get("start_date")
    end_date = arguments.get("end_date")
    
    # First, get statistics for the metric
    stats_query = f"""
        SELECT 
            AVG({metric}) as mean,
            STDDEV({metric}) as stddev
        FROM production_data
        WHERE {metric} IS NOT NULL
    """
    
    if start_date:
        stats_query += " AND productiontime >= :start_date"
    if end_date:
        stats_query += " AND productiontime <= :end_date"
    
    params = {}
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
    
    stats = db.execute_query_single(stats_query, params)
    
    if not stats or stats["stddev"] is None:
        return [TextContent(
            type="text",
            text=json.dumps({"error": "Insufficient data for anomaly detection"}, indent=2)
        )]
    
    mean = float(stats["mean"])
    stddev = float(stats["stddev"])
    threshold = mean + (threshold_std * stddev)
    
    # Find anomalies
    anomaly_query = f"""
        SELECT 
            p.*,
            ABS(p.{metric} - :mean) / :stddev as z_score
        FROM production_data p
        WHERE p.{metric} IS NOT NULL
            AND ABS(p.{metric} - :mean) > :threshold_std * :stddev
    """
    
    if start_date:
        anomaly_query += " AND p.productiontime >= :start_date"
    if end_date:
        anomaly_query += " AND p.productiontime <= :end_date"
    
    anomaly_query += " ORDER BY z_score DESC LIMIT 50"
    
    anomaly_params = {
        "mean": mean,
        "stddev": stddev,
        "threshold_std": threshold_std,
        **params
    }
    
    results = db.execute_query(anomaly_query, anomaly_params)
    
    import json
    return [TextContent(
        type="text",
        text=json.dumps({
            "statistics": {
                "mean": mean,
                "stddev": stddev,
                "threshold": threshold
            },
            "anomalies": results
        }, indent=2, default=str)
    )]


async def handle_get_well_details(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle get_well_details tool call."""
    db = get_db_manager()
    
    well_legal_name = arguments["well_legal_name"]
    
    query = "SELECT * FROM wells_data WHERE well_legal_name = :well_legal_name"
    result = db.execute_query_single(query, {"well_legal_name": well_legal_name})
    
    if result:
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2, default=str)
        )]
    else:
        return [TextContent(
            type="text",
            text=json.dumps({"error": f"Well '{well_legal_name}' not found"}, indent=2)
        )]


async def handle_get_wellbore_details(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle get_wellbore_details tool call."""
    db = get_db_manager()
    
    wellbore_name = arguments["wellbore_name"]
    
    query = "SELECT * FROM wellbores_data WHERE wellbore_name = :wellbore_name"
    result = db.execute_query_single(query, {"wellbore_name": wellbore_name})
    
    if result:
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2, default=str)
        )]
    else:
        return [TextContent(
            type="text",
            text=json.dumps({"error": f"Wellbore '{wellbore_name}' not found"}, indent=2)
        )]


async def handle_list_all_wells(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle list_all_wells tool call."""
    db = get_db_manager()
    
    limit = arguments.get("limit", 100)
    
    query = f"""
        SELECT DISTINCT well_legal_name, geo_latitude, geo_longitude, water_depth
        FROM wells_data
        ORDER BY well_legal_name
        LIMIT {limit}
    """
    
    results = db.execute_query(query)
    
    import json
    return [TextContent(
        type="text",
        text=json.dumps(results, indent=2, default=str)
    )]


async def handle_get_database_schema(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle get_database_schema tool call."""
    db = get_db_manager()
    
    table_name = arguments["table_name"]
    schema = db.get_table_schema(table_name)
    
    return [TextContent(
        type="text",
        text=json.dumps({
            "table_name": table_name,
            "columns": schema
        }, indent=2, default=str)
    )]


# Tool handler mapping
TOOL_HANDLERS = {
    "query_production_data": handle_query_production_data,
    "get_well_statistics": handle_get_well_statistics,
    "query_wells_by_location": handle_query_wells_by_location,
    "detect_production_anomalies": handle_detect_production_anomalies,
    "get_well_details": handle_get_well_details,
    "get_wellbore_details": handle_get_wellbore_details,
    "list_all_wells": handle_list_all_wells,
    "get_database_schema": handle_get_database_schema,
}
