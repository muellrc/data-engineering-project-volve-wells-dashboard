"""
Database connection utilities for NLQ service.
Reuses database connection patterns from MCP server.
"""
import os
from typing import List, Dict, Any, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from contextlib import contextmanager


class DatabaseManager:
    """Manages database connections and provides query execution methods."""
    
    def __init__(self, connection_string: Optional[str] = None):
        """
        Initialize database manager.
        
        Args:
            connection_string: PostgreSQL connection string. If None, uses environment variables.
        """
        if connection_string is None:
            db_host = os.getenv("DB_HOST", "dev-postgres-db")
            db_port = os.getenv("DB_PORT", "5432")
            db_name = os.getenv("DB_NAME", "postgres")
            db_user = os.getenv("DB_USER", "postgres")
            db_password = os.getenv("DB_PASSWORD", "postgres")
            
            connection_string = (
                f"postgresql://{db_user}:{db_password}@"
                f"{db_host}:{db_port}/{db_name}"
            )
        
        self.engine: Engine = create_engine(connection_string)
    
    @contextmanager
    def get_connection(self):
        """Get a database connection context manager."""
        conn = self.engine.connect()
        try:
            yield conn
        finally:
            conn.close()
    
    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute a SQL query and return results as a list of dictionaries.
        
        Args:
            query: SQL query string
            params: Optional query parameters for parameterized queries
            
        Returns:
            List of dictionaries representing rows
        """
        with self.get_connection() as conn:
            result = conn.execute(text(query), params or {})
            columns = result.keys()
            rows = result.fetchall()
            
            return [dict(zip(columns, row)) for row in rows]
    
    def get_table_schema(self, table_name: str) -> List[Dict[str, str]]:
        """
        Get schema information for a table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            List of dictionaries with column information
        """
        query = """
            SELECT 
                column_name,
                data_type,
                is_nullable
            FROM information_schema.columns
            WHERE table_name = :table_name
            ORDER BY ordinal_position
        """
        return self.execute_query(query, {"table_name": table_name})
    
    def get_all_tables(self) -> List[str]:
        """
        Get list of all tables in the database.
        
        Returns:
            List of table names
        """
        query = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """
        results = self.execute_query(query)
        return [row["table_name"] for row in results]
    
    def get_database_schema_context(self) -> str:
        """
        Get a formatted string of the database schema for LLM context.
        
        Returns:
            Formatted string describing the database schema
        """
        tables = self.get_all_tables()
        schema_parts = []
        
        for table in tables:
            columns = self.get_table_schema(table)
            column_info = []
            for col in columns:
                nullable = "NULL" if col["is_nullable"] == "YES" else "NOT NULL"
                column_info.append(f"  - {col['column_name']}: {col['data_type']} ({nullable})")
            
            schema_parts.append(f"Table: {table}\n" + "\n".join(column_info))
        
        return "\n\n".join(schema_parts)


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


def get_db_manager() -> DatabaseManager:
    """Get or create the global database manager instance."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager
