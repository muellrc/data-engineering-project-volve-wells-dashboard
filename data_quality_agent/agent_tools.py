"""
Tools available to the Data Quality Agent.
These tools allow the agent to investigate issues and take actions.
"""
from typing import Dict, Any, List, Optional
from .database import get_db_manager
from .quality_checks import DataQualityChecker, QualityIssue


class AgentTools:
    """Tools that the agent can use to investigate and fix data quality issues."""
    
    def __init__(self):
        """Initialize agent tools."""
        self.db = get_db_manager()
        self.quality_checker = DataQualityChecker(self.db)
    
    def investigate_table(self, table_name: str) -> Dict[str, Any]:
        """
        Investigate a specific table for data quality issues.
        
        Args:
            table_name: Name of the table to investigate
            
        Returns:
            Dictionary with investigation results
        """
        issues = []
        
        # Run various checks on the table
        issues.extend(self.quality_checker.check_missing_values(table_name))
        issues.extend(self.quality_checker.check_duplicates(table_name, self._get_key_columns(table_name)))
        
        # Get table statistics
        stats_query = f"SELECT COUNT(*) as row_count FROM {table_name}"
        stats = self.db.execute_query(stats_query)
        row_count = stats[0]["row_count"] if stats else 0
        
        return {
            "table": table_name,
            "row_count": row_count,
            "issues_found": len(issues),
            "issues": [self._issue_to_dict(issue) for issue in issues]
        }
    
    def investigate_column(self, table_name: str, column_name: str) -> Dict[str, Any]:
        """
        Investigate a specific column for data quality issues.
        
        Args:
            table_name: Name of the table
            column_name: Name of the column
            
        Returns:
            Dictionary with investigation results
        """
        issues = []
        
        # Check for missing values
        issues.extend(self.quality_checker.check_missing_values(table_name, [column_name]))
        
        # Get column statistics
        stats_query = f"""
            SELECT 
                COUNT(*) as total_count,
                COUNT({column_name}) as non_null_count,
                COUNT(DISTINCT {column_name}) as distinct_count,
                MIN({column_name}) as min_value,
                MAX({column_name}) as max_value,
                AVG({column_name}) as avg_value
            FROM {table_name}
        """
        
        stats = self.db.execute_query(stats_query)
        
        return {
            "table": table_name,
            "column": column_name,
            "statistics": stats[0] if stats else {},
            "issues_found": len(issues),
            "issues": [self._issue_to_dict(issue) for issue in issues]
        }
    
    def get_sample_data(self, table_name: str, column_name: Optional[str] = None, 
                       limit: int = 10) -> Dict[str, Any]:
        """
        Get sample data from a table or column.
        
        Args:
            table_name: Name of the table
            column_name: Optional column name to filter
            limit: Number of rows to return
            
        Returns:
            Dictionary with sample data
        """
        if column_name:
            query = f"SELECT {column_name} FROM {table_name} LIMIT {limit}"
        else:
            query = f"SELECT * FROM {table_name} LIMIT {limit}"
        
        data = self.db.execute_query(query)
        
        return {
            "table": table_name,
            "column": column_name,
            "sample_count": len(data),
            "data": data
        }
    
    def compare_with_historical(self, table_name: str, column_name: str, 
                               days_back: int = 7) -> Dict[str, Any]:
        """
        Compare current data with historical data.
        
        Args:
            table_name: Name of the table
            column_name: Column to compare
            days_back: Number of days to look back
            
        Returns:
            Dictionary with comparison results
        """
        # This is a simplified version - in production, you'd compare with historical snapshots
        current_query = f"""
            SELECT 
                AVG({column_name}) as current_avg,
                COUNT(*) as current_count
            FROM {table_name}
        """
        
        current = self.db.execute_query(current_query)
        
        return {
            "table": table_name,
            "column": column_name,
            "current_statistics": current[0] if current else {},
            "comparison_period_days": days_back,
            "note": "Historical comparison requires data snapshots"
        }
    
    def _get_key_columns(self, table_name: str) -> List[str]:
        """Get likely key columns for a table."""
        # Simple heuristic - in production, use actual primary keys
        key_mappings = {
            "production_data": ["wellbore", "productiontime"],
            "wells_data": ["well_legal_name"],
            "wellbores_data": ["wellbore_name"]
        }
        return key_mappings.get(table_name, [])
    
    def _issue_to_dict(self, issue) -> Dict[str, Any]:
        """Convert QualityIssue to dictionary."""
        return {
            "table": issue.table,
            "column": issue.column,
            "issue_type": issue.issue_type,
            "severity": issue.severity.value,
            "message": issue.message,
            "affected_rows": issue.affected_rows,
            "recommendation": issue.recommendation
        }


# Tool handler mapping for agent
TOOL_HANDLERS = {
    "investigate_table": lambda tools, args: tools.investigate_table(args["table_name"]),
    "investigate_column": lambda tools, args: tools.investigate_column(args["table_name"], args["column_name"]),
    "get_sample_data": lambda tools, args: tools.get_sample_data(
        args["table_name"], 
        args.get("column_name"), 
        args.get("limit", 10)
    ),
    "compare_with_historical": lambda tools, args: tools.compare_with_historical(
        args["table_name"],
        args["column_name"],
        args.get("days_back", 7)
    )
}
