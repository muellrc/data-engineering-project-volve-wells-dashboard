"""
Intelligent Data Quality Agent.
Uses LLM reasoning to investigate data quality issues and generate reports.
"""
import os
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from .quality_checks import DataQualityChecker, QualityIssue, QualitySeverity
from .agent_tools import AgentTools, TOOL_HANDLERS
from .database import get_db_manager


class LLMClient:
    """Simple LLM client for agent reasoning."""
    
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
    
    def reason_about_issues(self, issues: List[QualityIssue], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use LLM to reason about data quality issues and provide insights.
        
        Args:
            issues: List of quality issues
            context: Additional context about the database
            
        Returns:
            Dictionary with reasoning results
        """
        issues_summary = []
        for issue in issues:
            issues_summary.append({
                "table": issue.table,
                "column": issue.column,
                "type": issue.issue_type,
                "severity": issue.severity.value,
                "message": issue.message,
                "affected_rows": issue.affected_rows
            })
        
        prompt = f"""You are a data quality analyst. Analyze these data quality issues and provide:

1. Root cause analysis for the most critical issues
2. Impact assessment (how these issues affect data usability)
3. Prioritized recommendations for fixing issues
4. Suggested actions to prevent similar issues

Data Quality Issues:
{json.dumps(issues_summary, indent=2)}

Database Context:
- Tables: {', '.join(context.get('tables', []))}
- Total issues found: {len(issues)}

Provide a structured analysis in JSON format with:
- root_causes: List of root cause analyses
- impact_assessment: Description of impact
- recommendations: List of prioritized recommendations
- prevention_actions: List of suggested prevention actions
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
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a data quality analyst. Provide structured JSON responses."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"} if self.provider == "ollama" else None
            )
            content = response.choices[0].message.content
        
        # Try to parse as JSON
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # If not JSON, return as text
            return {
                "analysis": content,
                "format": "text"
            }
    
    def generate_report(self, issues: List[QualityIssue], reasoning: Dict[str, Any], 
                       investigation_results: List[Dict]) -> str:
        """
        Generate a human-readable data quality report.
        
        Args:
            issues: List of quality issues
            reasoning: LLM reasoning results
            investigation_results: Results from agent investigations
            
        Returns:
            Markdown-formatted report
        """
        prompt = f"""Generate a comprehensive data quality report in Markdown format.

Data Quality Issues Found: {len(issues)}
Critical: {sum(1 for i in issues if i.severity == QualitySeverity.CRITICAL)}
Errors: {sum(1 for i in issues if i.severity == QualitySeverity.ERROR)}
Warnings: {sum(1 for i in issues if i.severity == QualitySeverity.WARNING)}

Issues Summary:
{json.dumps([self._issue_to_dict(i) for i in issues[:10]], indent=2)}

LLM Analysis:
{json.dumps(reasoning, indent=2)}

Investigation Results:
{json.dumps(investigation_results[:5], indent=2)}

Generate a professional markdown report with:
- Executive Summary
- Issue Breakdown by Severity
- Root Cause Analysis
- Impact Assessment
- Recommendations
- Action Items
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
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a data quality analyst. Generate professional markdown reports."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            return response.choices[0].message.content
    
    def _issue_to_dict(self, issue: QualityIssue) -> Dict[str, Any]:
        """Convert issue to dictionary."""
        return {
            "table": issue.table,
            "column": issue.column,
            "type": issue.issue_type,
            "severity": issue.severity.value,
            "message": issue.message,
            "affected_rows": issue.affected_rows
        }


class DataQualityAgent:
    """
    Intelligent agent that monitors data quality, investigates issues,
    and generates reports using LLM reasoning.
    """
    
    def __init__(self):
        """Initialize the data quality agent."""
        self.db = get_db_manager()
        self.quality_checker = DataQualityChecker(self.db)
        self.agent_tools = AgentTools()
        self.llm_client = LLMClient() if os.getenv("LLM_API_KEY") else None
    
    def run_quality_check(self) -> Dict[str, Any]:
        """
        Run comprehensive data quality check.
        
        Returns:
            Dictionary with check results
        """
        print("🔍 Running data quality checks...")
        issues = self.quality_checker.run_all_checks()
        
        # Group issues by severity
        issues_by_severity = {
            "critical": [i for i in issues if i.severity == QualitySeverity.CRITICAL],
            "error": [i for i in issues if i.severity == QualitySeverity.ERROR],
            "warning": [i for i in issues if i.severity == QualitySeverity.WARNING],
            "info": [i for i in issues if i.severity == QualitySeverity.INFO]
        }
        
        return {
            "timestamp": datetime.now().isoformat(),
            "total_issues": len(issues),
            "issues_by_severity": {
                k: len(v) for k, v in issues_by_severity.items()
            },
            "issues": [self._issue_to_dict(i) for i in issues]
        }
    
    def investigate_issues(self, issues: List[QualityIssue]) -> List[Dict[str, Any]]:
        """
        Use agent tools to investigate specific issues.
        
        Args:
            issues: List of issues to investigate
            
        Returns:
            List of investigation results
        """
        investigation_results = []
        
        # Group issues by table
        issues_by_table = {}
        for issue in issues:
            if issue.table not in issues_by_table:
                issues_by_table[issue.table] = []
            issues_by_table[issue.table].append(issue)
        
        # Investigate each table
        for table, table_issues in issues_by_table.items():
            print(f"🔍 Investigating {table}...")
            result = self.agent_tools.investigate_table(table)
            investigation_results.append(result)
            
            # For column-specific issues, investigate columns
            for issue in table_issues:
                if issue.column:
                    col_result = self.agent_tools.investigate_column(table, issue.column)
                    investigation_results.append(col_result)
        
        return investigation_results
    
    def analyze_and_report(self, include_llm_reasoning: bool = True) -> Dict[str, Any]:
        """
        Run full data quality analysis with LLM reasoning and report generation.
        
        Args:
            include_llm_reasoning: Whether to use LLM for reasoning (requires API key)
            
        Returns:
            Complete analysis results
        """
        # Step 1: Run quality checks
        check_results = self.run_quality_check()
        issues = [QualityIssue(**issue) for issue in check_results["issues"]]
        
        # Step 2: Investigate issues using agent tools
        investigation_results = self.investigate_issues(issues)
        
        # Step 3: LLM reasoning (if available)
        reasoning = None
        report = None
        
        if include_llm_reasoning and self.llm_client:
            print("🤖 Using LLM to analyze issues...")
            context = {
                "tables": self.db.get_all_tables(),
                "total_issues": len(issues)
            }
            reasoning = self.llm_client.reason_about_issues(issues, context)
            
            print("📝 Generating report...")
            report = self.llm_client.generate_report(issues, reasoning, investigation_results)
        else:
            # Generate simple report without LLM
            report = self._generate_simple_report(issues, investigation_results)
        
        return {
            "check_results": check_results,
            "investigation_results": investigation_results,
            "reasoning": reasoning,
            "report": report,
            "timestamp": datetime.now().isoformat()
        }
    
    def _generate_simple_report(self, issues: List[QualityIssue], 
                               investigations: List[Dict]) -> str:
        """Generate a simple report without LLM."""
        report_lines = [
            "# Data Quality Report",
            f"Generated: {datetime.now().isoformat()}",
            "",
            "## Summary",
            f"- Total Issues: {len(issues)}",
            f"- Critical: {sum(1 for i in issues if i.severity == QualitySeverity.CRITICAL)}",
            f"- Errors: {sum(1 for i in issues if i.severity == QualitySeverity.ERROR)}",
            f"- Warnings: {sum(1 for i in issues if i.severity == QualitySeverity.WARNING)}",
            "",
            "## Issues",
            ""
        ]
        
        for issue in issues[:20]:  # Limit to first 20
            report_lines.append(f"### {issue.table}.{issue.column or 'N/A'}")
            report_lines.append(f"- **Type**: {issue.issue_type}")
            report_lines.append(f"- **Severity**: {issue.severity.value}")
            report_lines.append(f"- **Message**: {issue.message}")
            if issue.recommendation:
                report_lines.append(f"- **Recommendation**: {issue.recommendation}")
            report_lines.append("")
        
        return "\n".join(report_lines)
    
    def _issue_to_dict(self, issue: QualityIssue) -> Dict[str, Any]:
        """Convert issue to dictionary."""
        return {
            "table": issue.table,
            "column": issue.column,
            "issue_type": issue.issue_type,
            "severity": issue.severity.value,
            "message": issue.message,
            "affected_rows": issue.affected_rows,
            "recommendation": issue.recommendation
        }
