"""
Example usage of the Natural Language Query API.
Demonstrates how to interact with the NLQ service.
"""
import requests
import json
from typing import Dict, Any


BASE_URL = "http://localhost:8000"


def ask_question(question: str, include_explanation: bool = True, max_results: int = 10) -> Dict[str, Any]:
    """
    Ask a natural language question and get SQL results.
    
    Args:
        question: Natural language question
        include_explanation: Whether to include SQL explanation
        max_results: Maximum number of results
        
    Returns:
        Query response dictionary
    """
    response = requests.post(
        f"{BASE_URL}/query",
        json={
            "question": question,
            "include_explanation": include_explanation,
            "max_results": max_results
        }
    )
    response.raise_for_status()
    return response.json()


def get_schema() -> Dict[str, Any]:
    """Get database schema information."""
    response = requests.get(f"{BASE_URL}/schema")
    response.raise_for_status()
    return response.json()


def validate_sql(sql: str) -> Dict[str, Any]:
    """Validate a SQL query."""
    response = requests.post(
        f"{BASE_URL}/validate-sql",
        params={"sql": sql}
    )
    response.raise_for_status()
    return response.json()


def main():
    """Example usage demonstrations."""
    print("=" * 60)
    print("Natural Language Query Service - Example Usage")
    print("=" * 60)
    
    # Example questions
    questions = [
        "What wells produced the most oil in 2016?",
        "Show me the average gas production per wellbore",
        "Which wellbores are located near latitude 58.4?",
        "Find wells with declining production over time",
        "What is the total water injected across all wells?",
    ]
    
    print("\n1. Testing Health Check")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"   Status: {response.json()}")
    except Exception as e:
        print(f"   Error: {e}")
        return
    
    print("\n2. Getting Database Schema")
    try:
        schema = get_schema()
        print(f"   Found {schema['table_count']} tables")
        for table_name in schema['tables'].keys():
            print(f"   - {table_name}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n3. Testing Natural Language Queries")
    for i, question in enumerate(questions[:2], 1):  # Test first 2 questions
        print(f"\n   Question {i}: {question}")
        try:
            result = ask_question(question, max_results=5)
            print(f"   SQL: {result['sql'][:100]}...")
            print(f"   Results: {result['row_count']} rows")
            print(f"   Execution time: {result['execution_time_ms']}ms")
            if result.get('explanation'):
                print(f"   Explanation: {result['explanation'][:100]}...")
        except Exception as e:
            print(f"   Error: {e}")
    
    print("\n4. Testing SQL Validation")
    test_queries = [
        "SELECT * FROM production_data LIMIT 10",
        "DROP TABLE production_data",  # Should fail
        "SELECT wellbore, SUM(boreoilvol) FROM production_data GROUP BY wellbore",
    ]
    
    for sql in test_queries:
        print(f"\n   SQL: {sql[:50]}...")
        try:
            result = validate_sql(sql)
            status = "✅ Valid" if result['is_valid'] else "❌ Invalid"
            print(f"   {status}")
            if result.get('error_message'):
                print(f"   Reason: {result['error_message']}")
        except Exception as e:
            print(f"   Error: {e}")
    
    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
