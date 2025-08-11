"""Chat agent for handling natural language database queries"""

import asyncio
import aiohttp
import json
from typing import List, Dict, Any, Optional
from .model_utils import get_model
from .validation import validate_dashboard_json

class ChatAgent:
    """Agent for handling chat-based database queries"""
    
    def __init__(self):
        self.model_manager = get_model()
        self.mcp_base_url = "http://localhost:8000/mcp"
        self.conversation_history = []
    
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
    
    async def get_database_schema(self) -> str:
        """Get database schema for context"""
        try:
            result = await self._call_mcp_tool("get_schema")
            schema_text = result.get("content", [{}])[0].get("text", "{}")
            return schema_text
        except Exception as e:
            return f"Error getting schema: {str(e)}"
    
    async def execute_sql_query(self, query: str) -> Dict[str, Any]:
        """Execute SQL query via MCP server"""
        try:
            result = await self._call_mcp_tool("read_query", {"query": query})
            query_result = result.get("content", [{}])[0].get("text", "{}")
            return json.loads(query_result)
        except Exception as e:
            raise Exception(f"Error executing query: {str(e)}")
    
    async def generate_sql_from_natural_language(self, question: str, schema: str) -> str:
        """Generate SQL query from natural language question"""
        system_prompt = f"""You are a SQL expert. Given a database schema and a natural language question, generate a SQL SELECT query.

Database Schema:
{schema}

Rules:
1. Only generate SELECT queries
2. Use proper table and column names from the schema
3. Include appropriate WHERE clauses, JOINs, and ORDER BY as needed
4. Limit results to reasonable numbers (use LIMIT clause)
5. Return only the SQL query, no explanation

Question: {question}
SQL Query:"""
        
        messages = [{"role": "user", "content": question}]
        
        try:
            response = await self.model_manager.generate_response(
                messages=messages,
                system_prompt=system_prompt,
                max_tokens=500,
                temperature=0.1
            )
            
            # Extract SQL query from response
            sql_query = response.strip()
            if sql_query.lower().startswith('select'):
                return sql_query
            else:
                # Try to extract SQL from response
                lines = response.split('\n')
                for line in lines:
                    if line.strip().lower().startswith('select'):
                        return line.strip()
                
                raise Exception("No valid SQL query generated")
                
        except Exception as e:
            raise Exception(f"Error generating SQL: {str(e)}")
    
    async def format_query_response(self, question: str, sql_query: str, result: Dict[str, Any]) -> str:
        """Format query response for display"""
        if result.get("row_count", 0) == 0:
            return f"**Query:** `{sql_query}`\n\n**Result:** No data found for your question: '{question}'"
        
        # Format as markdown table
        columns = result.get("columns", [])
        data = result.get("data", [])
        
        if not columns or not data:
            return f"**Query:** `{sql_query}`\n\n**Result:** No data returned."
        
        # Create markdown table
        table_md = f"**Query:** `{sql_query}`\n\n**Results for:** {question}\n\n"
        
        # Header row
        table_md += "| " + " | ".join(columns) + " |\n"
        table_md += "|" + "---|" * len(columns) + "\n"
        
        # Data rows (limit to first 10 for display)
        display_rows = data[:10]
        for row in display_rows:
            formatted_row = []
            for value in row:
                if value is None:
                    formatted_row.append("")
                else:
                    formatted_row.append(str(value))
            table_md += "| " + " | ".join(formatted_row) + " |\n"
        
        if len(data) > 10:
            table_md += f"\n*Showing first 10 of {len(data)} total rows.*"
        
        return table_md

async def run_agent(question: str) -> str:
    """
    Main function to run chat agent
    
    Args:
        question: Natural language question about the database
        
    Returns:
        Formatted response with query results
    """
    agent = ChatAgent()
    
    try:
        # Get database schema
        schema = await agent.get_database_schema()
        
        # Generate SQL from natural language
        sql_query = await agent.generate_sql_from_natural_language(question, schema)
        
        # Execute the query
        result = await agent.execute_sql_query(sql_query)
        
        # Format and return response
        return await agent.format_query_response(question, sql_query, result)
        
    except Exception as e:
        return f"Error processing your question: {str(e)}"
