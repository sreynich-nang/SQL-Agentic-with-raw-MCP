"""Dashboard agent for generating HTML dashboards"""

import asyncio
import aiohttp
import json
from typing import Dict, Any, List
from .model_utils import get_model
from .validation import validate_dashboard_json, create_default_dashboard_structure

class DashboardAgent:
    """Agent for generating database dashboards"""
    
    def __init__(self):
        self.model_manager = get_model()
        self.mcp_base_url = "http://localhost:8000/mcp"
    
    async def _call_mcp_tool(self, tool_name: str, arguments: Dict[str, Any] = None) -> Dict[str, Any]:
        """Call MCP server tool"""
        if arguments is None:
            arguments = {}
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.mcp_base_url}/tools/call",
                json={
                    "name": tool_name,
                    "arguments": arguments
                }
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"MCP tool call failed: {error_text}")
                
                result = await response.json()
                return result
    
    async def analyze_database(self) -> Dict[str, Any]:
        """Analyze database structure and suggest dashboard components"""
        try:
            # Get schema
            result = await self._call_mcp_tool("get_schema")
            schema_text = result.get("content", [{}])[0].get("text", "{}")
            schema = json.loads(schema_text)
            
            system_prompt = """You are a database analyst. Given a database schema, analyze it and suggest key metrics and insights for a dashboard.

Return your analysis as JSON with this structure:
{
    "key_metrics": [
        {"name": "metric_name", "description": "what this metric shows", "query": "SQL to calculate it"}
    ],
    "interesting_tables": ["table1", "table2"],
    "suggested_charts": [
        {"type": "bar|line|pie", "title": "Chart Title", "description": "What it shows"}
    ],
    "insights": ["insight1", "insight2"]
}

Focus on practical business metrics like counts, sums, averages, and trends."""
            
            messages = [
                {"role": "user", "content": f"Analyze this database schema and suggest dashboard components:\n\n{schema_text}"}
            ]
            
            response = await self.model_manager.generate_response(
                messages=messages,
                system_prompt=system_prompt,
                max_tokens=1000,
                temperature=0.3
            )
            
            # Parse the JSON response
            analysis = validate_dashboard_json(response)
            if not analysis:
                # Return default analysis if parsing fails
                return {
                    "key_metrics": [
                        {"name": "Total Records", "description": "Count of all records in main tables", "query": "SELECT 'Analysis Error' as metric"}
                    ],
                    "interesting_tables": list(schema.get("tables", {}).keys())[:3],
                    "suggested_charts": [{"type": "bar", "title": "Data Overview", "description": "Overview of database contents"}],
                    "insights": ["Database analysis completed"]
                }
            
            return analysis
            
        except Exception as e:
            print(f"Error analyzing database: {e}")
            return {
                "key_metrics": [{"name": "Error", "description": "Analysis failed", "query": "SELECT 'Error' as status"}],
                "interesting_tables": [],
                "suggested_charts": [],
                "insights": [f"Analysis error: {str(e)}"]
            }
    
    async def get_data_from_database(self, queries: List[str]) -> List[Dict[str, Any]]:
        """Execute multiple queries to get dashboard data"""
        results = []
        
        for query in queries:
            try:
                result = await self._call_mcp_tool("read_query", {"query": query})
                query_result = result.get("content", [{}])[0].get("text", "{}")
                parsed_result = json.loads(query_result)
                results.append({
                    "query": query,
                    "success": True,
                    "data": parsed_result
                })
            except Exception as e:
                results.append({
                    "query": query,
                    "success": False,
                    "error": str(e),
                    "data": {"columns": [], "data": [], "row_count": 0}
                })
        
        return results
    
    async def generate_html_dashboard(self, analysis: Dict[str, Any], data_results: List[Dict[str, Any]]) -> str:
        """Generate HTML dashboard from analysis and data"""
        system_prompt = """You are an expert web developer creating HTML dashboards. Create a beautiful, responsive HTML dashboard with the following requirements:

1. Use modern CSS with flexbox/grid layouts
2. Include interactive elements where possible
3. Make it visually appealing with proper colors and typography
4. Include the provided data in tables, charts, or metrics cards
5. Make it fully self-contained (no external dependencies except basic CSS)
6. Use Chart.js or similar for any charts if needed

Return only the complete HTML code."""
        
        # Prepare context for the LLM
        context = f"""
Database Analysis:
{json.dumps(analysis, indent=2)}

Query Results:
{json.dumps(data_results, indent=2, default=str)}

Create a comprehensive dashboard HTML page that displays this information in an organized, visually appealing way.
"""
        
        messages = [{"role": "user", "content": context}]
        
        try:
            response = await self.model_manager.generate_response(
                messages=messages,
                system_prompt=system_prompt,
                max_tokens=2000,
                temperature=0.4
            )
            
            return response
            
        except Exception as e:
            # Return a basic error dashboard
            return f"""
            <html>
            <head>
                <title>Dashboard Error</title>
                <style>
                    body {{ font-family: Arial, sans-serif; padding: 20px; }}
                    .error {{ color: red; padding: 20px; border: 1px solid red; border-radius: 5px; }}
                </style>
            </head>
            <body>
                <h1>Dashboard Generation Error</h1>
                <div class="error">
                    <p>Failed to generate dashboard: {str(e)}</p>
                </div>
            </body>
            </html>
            """

async def run_dashboard_agent() -> str:
    """
    Main function to run dashboard generation
    
    Returns:
        Generated HTML dashboard
    """
    agent = DashboardAgent()
    
    try:
        # Step 1: Analyze database
        print("Analyzing database...")
        analysis = await agent.analyze_database()
        
        # Step 2: Get data for metrics
        print("Gathering data...")
        queries = []
        for metric in analysis.get("key_metrics", [])[:5]:  # Limit to 5 metrics
            queries.append(metric.get("query", "SELECT 'No query' as result"))
        
        # Add some general overview queries
        queries.extend([
            "SELECT COUNT(*) as total_customers FROM customers",
            "SELECT COUNT(*) as total_orders FROM orders", 
            "SELECT SUM(price * quantity) as total_revenue FROM orders"
        ])
        
        data_results = await agent.get_data_from_database(queries)
        
        # Step 3: Generate HTML dashboard
        print("Generating dashboard...")
        html_dashboard = await agent.generate_html_dashboard(analysis, data_results)
        
        return html_dashboard
        
    except Exception as e:
        return f"""
        <html>
        <head><title>Error</title></head>
        <body>
            <h1>Dashboard Generation Failed</h1>
            <p>Error: {str(e)}</p>
        </body>
        </html>
        """