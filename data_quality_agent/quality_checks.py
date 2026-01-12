"""
Data quality checks and validation rules.
Implements various data quality metrics and checks.
"""
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum


class QualitySeverity(str, Enum):
    """Severity levels for data quality issues."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class QualityIssue:
    """Represents a data quality issue."""
    table: str
    column: Optional[str]
    issue_type: str
    severity: QualitySeverity
    message: str
    affected_rows: Optional[int] = None
    sample_data: Optional[List[Dict]] = None
    recommendation: Optional[str] = None


class DataQualityChecker:
    """Performs various data quality checks on the database."""
    
    def __init__(self, db_manager):
        """
        Initialize data quality checker.
        
        Args:
            db_manager: DatabaseManager instance
        """
        self.db = db_manager
    
    def check_missing_values(self, table: str, columns: Optional[List[str]] = None) -> List[QualityIssue]:
        """
        Check for missing (NULL) values in specified columns.
        
        Args:
            table: Table name to check
            columns: List of column names to check. If None, checks all columns.
            
        Returns:
            List of QualityIssue objects
        """
        issues = []
        
        if columns is None:
            schema = self.db.get_table_schema(table)
            columns = [col["column_name"] for col in schema]
        
        for column in columns:
            query = f"""
                SELECT COUNT(*) as null_count
                FROM {table}
                WHERE {column} IS NULL
            """
            result = self.db.execute_query(query)
            null_count = result[0]["null_count"] if result else 0
            
            if null_count > 0:
                # Get total count for percentage
                total_query = f"SELECT COUNT(*) as total FROM {table}"
                total_result = self.db.execute_query(total_query)
                total = total_result[0]["total"] if total_result else 1
                percentage = (null_count / total) * 100
                
                severity = QualitySeverity.ERROR if percentage > 50 else QualitySeverity.WARNING
                
                issues.append(QualityIssue(
                    table=table,
                    column=column,
                    issue_type="missing_values",
                    severity=severity,
                    message=f"Found {null_count} NULL values ({percentage:.1f}%) in {column}",
                    affected_rows=null_count,
                    recommendation=f"Consider investigating why {null_count} rows have NULL values in {column}"
                ))
        
        return issues
    
    def check_duplicates(self, table: str, key_columns: List[str]) -> List[QualityIssue]:
        """
        Check for duplicate rows based on key columns.
        
        Args:
            table: Table name to check
            key_columns: Columns that should be unique together
            
        Returns:
            List of QualityIssue objects
        """
        issues = []
        
        key_cols_str = ", ".join(key_columns)
        query = f"""
            SELECT {key_cols_str}, COUNT(*) as duplicate_count
            FROM {table}
            GROUP BY {key_cols_str}
            HAVING COUNT(*) > 1
            ORDER BY duplicate_count DESC
            LIMIT 10
        """
        
        duplicates = self.db.execute_query(query)
        
        if duplicates:
            total_duplicates = sum(row["duplicate_count"] - 1 for row in duplicates)
            
            issues.append(QualityIssue(
                table=table,
                column=None,
                issue_type="duplicates",
                severity=QualitySeverity.WARNING,
                message=f"Found {len(duplicates)} duplicate key combinations affecting {total_duplicates} rows",
                affected_rows=total_duplicates,
                sample_data=duplicates[:5],
                recommendation=f"Review duplicate entries in {table} based on {key_cols_str}"
            ))
        
        return issues
    
    def check_data_freshness(self, table: str, timestamp_column: str, max_age_hours: int = 24) -> List[QualityIssue]:
        """
        Check if data is fresh (recently updated).
        
        Args:
            table: Table name to check
            timestamp_column: Column containing timestamp
            max_age_hours: Maximum age in hours before flagging as stale
            
        Returns:
            List of QualityIssue objects
        """
        issues = []
        
        query = f"""
            SELECT MAX({timestamp_column}) as latest_timestamp
            FROM {table}
        """
        
        result = self.db.execute_query(query)
        
        if result and result[0]["latest_timestamp"]:
            latest = result[0]["latest_timestamp"]
            if isinstance(latest, str):
                latest = datetime.fromisoformat(latest.replace('Z', '+00:00'))
            
            age = datetime.now() - latest.replace(tzinfo=None) if latest.tzinfo else datetime.now() - latest
            age_hours = age.total_seconds() / 3600
            
            if age_hours > max_age_hours:
                issues.append(QualityIssue(
                    table=table,
                    column=timestamp_column,
                    issue_type="stale_data",
                    severity=QualitySeverity.WARNING,
                    message=f"Data is {age_hours:.1f} hours old (max: {max_age_hours}h). Latest: {latest}",
                    recommendation=f"Check if data pipeline is running correctly. Last update was {age_hours:.1f} hours ago"
                ))
        
        return issues
    
    def check_value_ranges(self, table: str, column: str, min_value: Optional[float] = None, 
                          max_value: Optional[float] = None) -> List[QualityIssue]:
        """
        Check if values are within expected range.
        
        Args:
            table: Table name
            column: Column name to check
            min_value: Minimum expected value
            max_value: Maximum expected value
            
        Returns:
            List of QualityIssue objects
        """
        issues = []
        conditions = []
        
        if min_value is not None:
            conditions.append(f"{column} < {min_value}")
        if max_value is not None:
            conditions.append(f"{column} > {max_value}")
        
        if not conditions:
            return issues
        
        where_clause = " OR ".join(conditions)
        query = f"""
            SELECT COUNT(*) as outlier_count
            FROM {table}
            WHERE {where_clause}
        """
        
        result = self.db.execute_query(query)
        outlier_count = result[0]["outlier_count"] if result else 0
        
        if outlier_count > 0:
            # Get sample outliers
            sample_query = f"""
                SELECT {column}
                FROM {table}
                WHERE {where_clause}
                LIMIT 5
            """
            samples = self.db.execute_query(sample_query)
            
            range_desc = f"{min_value if min_value else '-∞'} to {max_value if max_value else '+∞'}"
            
            issues.append(QualityIssue(
                table=table,
                column=column,
                issue_type="out_of_range",
                severity=QualitySeverity.ERROR,
                message=f"Found {outlier_count} values outside expected range ({range_desc})",
                affected_rows=outlier_count,
                sample_data=[{column: row[column]} for row in samples],
                recommendation=f"Review {outlier_count} rows with values outside expected range in {column}"
            ))
        
        return issues
    
    def check_referential_integrity(self, child_table: str, child_column: str, 
                                   parent_table: str, parent_column: str) -> List[QualityIssue]:
        """
        Check referential integrity between tables.
        
        Args:
            child_table: Table with foreign key
            child_column: Foreign key column
            parent_table: Referenced table
            parent_column: Referenced column
            
        Returns:
            List of QualityIssue objects
        """
        issues = []
        
        query = f"""
            SELECT COUNT(*) as orphan_count
            FROM {child_table} c
            LEFT JOIN {parent_table} p ON c.{child_column} = p.{parent_column}
            WHERE p.{parent_column} IS NULL
        """
        
        result = self.db.execute_query(query)
        orphan_count = result[0]["orphan_count"] if result else 0
        
        if orphan_count > 0:
            issues.append(QualityIssue(
                table=child_table,
                column=child_column,
                issue_type="referential_integrity",
                severity=QualitySeverity.ERROR,
                message=f"Found {orphan_count} orphaned records in {child_table}.{child_column} referencing {parent_table}.{parent_column}",
                affected_rows=orphan_count,
                recommendation=f"Fix {orphan_count} orphaned records or update referential constraints"
            ))
        
        return issues
    
    def run_all_checks(self) -> List[QualityIssue]:
        """
        Run all data quality checks.
        
        Returns:
            List of all QualityIssue objects found
        """
        all_issues = []
        
        tables = self.db.get_all_tables()
        
        for table in tables:
            # Check missing values for all tables
            all_issues.extend(self.check_missing_values(table))
            
            # Table-specific checks
            if table == "production_data":
                # Check for stale data
                all_issues.extend(self.check_data_freshness(table, "productiontime", max_age_hours=24))
                
                # Check for negative production values (shouldn't happen)
                all_issues.extend(self.check_value_ranges(table, "boreoilvol", min_value=0))
                all_issues.extend(self.check_value_ranges(table, "boregasvol", min_value=0))
                
                # Check for duplicates on wellbore + productiontime
                all_issues.extend(self.check_duplicates(table, ["wellbore", "productiontime"]))
            
            elif table == "wells_data":
                # Check for missing well names
                all_issues.extend(self.check_missing_values(table, ["well_legal_name"]))
            
            elif table == "wellbores_data":
                # Check referential integrity with wells_data
                all_issues.extend(self.check_referential_integrity(
                    "wellbores_data", "well_legal_name",
                    "wells_data", "well_legal_name"
                ))
        
        return all_issues
