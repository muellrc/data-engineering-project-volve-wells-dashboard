"""
SQL query validation and safety checks.
Ensures generated SQL queries are safe to execute.
"""
import re
from typing import Tuple, Optional


class SQLValidator:
    """Validates SQL queries for safety before execution."""
    
    # Dangerous SQL keywords that should not be allowed
    DANGEROUS_KEYWORDS = [
        'DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'CREATE', 'INSERT', 
        'UPDATE', 'GRANT', 'REVOKE', 'EXEC', 'EXECUTE', 'MERGE'
    ]
    
    # Allowed keywords (read-only operations)
    ALLOWED_KEYWORDS = [
        'SELECT', 'WITH', 'FROM', 'WHERE', 'JOIN', 'INNER', 'LEFT', 
        'RIGHT', 'FULL', 'OUTER', 'ON', 'GROUP', 'BY', 'HAVING', 
        'ORDER', 'LIMIT', 'OFFSET', 'UNION', 'INTERSECT', 'EXCEPT',
        'DISTINCT', 'AS', 'AND', 'OR', 'NOT', 'IN', 'LIKE', 'BETWEEN',
        'IS', 'NULL', 'COUNT', 'SUM', 'AVG', 'MAX', 'MIN', 'CAST'
    ]
    
    @staticmethod
    def validate_query(query: str) -> Tuple[bool, Optional[str]]:
        """
        Validate a SQL query for safety.
        
        Args:
            query: SQL query string to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not query or not query.strip():
            return False, "Query is empty"
        
        # Normalize query for checking
        query_upper = query.upper().strip()
        
        # Must start with SELECT
        if not query_upper.startswith('SELECT'):
            return False, "Only SELECT queries are allowed"
        
        # Check for dangerous keywords
        for keyword in SQLValidator.DANGEROUS_KEYWORDS:
            # Use word boundaries to avoid false positives
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, query_upper):
                return False, f"Dangerous keyword '{keyword}' is not allowed"
        
        # Check for SQL injection patterns
        dangerous_patterns = [
            r';\s*(DROP|DELETE|TRUNCATE|ALTER|CREATE|INSERT|UPDATE)',
            r'--',  # SQL comments
            r'/\*.*?\*/',  # Multi-line comments
            r'UNION.*SELECT',  # Union-based injection
            r'EXEC\s*\(',  # Executable code
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, query_upper, re.IGNORECASE | re.DOTALL):
                return False, f"Potentially dangerous SQL pattern detected"
        
        # Check for balanced parentheses (basic syntax check)
        if query.count('(') != query.count(')'):
            return False, "Unbalanced parentheses in query"
        
        return True, None
    
    @staticmethod
    def sanitize_query(query: str) -> str:
        """
        Basic query sanitization (removes comments, normalizes whitespace).
        
        Args:
            query: SQL query string
            
        Returns:
            Sanitized query string
        """
        # Remove SQL comments
        query = re.sub(r'--.*$', '', query, flags=re.MULTILINE)
        query = re.sub(r'/\*.*?\*/', '', query, flags=re.DOTALL)
        
        # Normalize whitespace
        query = ' '.join(query.split())
        
        return query.strip()
