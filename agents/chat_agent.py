"""Chat agent for handling natural language database queries"""

import asyncio
import aiohttp
import json
import re
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
            content = result.get("content")
            if not isinstance(content, list) or not content:
                raise Exception(f"Invalid MCP schema response: {result}")

            schema_text = content[0].get("text")
            if not schema_text:
                raise Exception("Schema text not found in MCP response")

            # DEBUG: Print schema to understand what's available
            print("=== DATABASE SCHEMA DEBUG ===")
            print(schema_text)
            print("=== END SCHEMA DEBUG ===")
            
            return schema_text
        except Exception as e:
            print(f"Error getting schema: {str(e)}")
            return f"Error getting schema: {str(e)}"
    
    async def execute_sql_query(self, query: str) -> Dict[str, Any]:
        """Execute SQL query via MCP server"""
        try:
            # Clean and validate the query before sending
            clean_query = self._clean_sql_query(query)
            print(f"=== SENDING TO MCP ===")
            print(f"Original: {query}")
            print(f"Cleaned: {clean_query}")
            print("=== END MCP SEND ===")
            
            result = await self._call_mcp_tool("read_query", {"query": clean_query})

            content = result.get("content")
            if not isinstance(content, list) or not content:
                raise Exception(f"Invalid MCP query response: {result}")

            query_result = content[0].get("text")
            if not query_result:
                raise Exception("No SQL result text returned from MCP")

            try:
                return json.loads(query_result)
            except json.JSONDecodeError:
                raise Exception(f"Invalid JSON in MCP query result: {query_result}")

        except Exception as e:
            raise Exception(f"Error executing query: {str(e)}")

    def _clean_sql_query(self, query: str) -> str:
        """Clean and validate SQL query"""
        # Remove extra whitespace and normalize
        clean_query = ' '.join(query.split())
        
        # Ensure it starts with SELECT (case insensitive)
        if not clean_query.upper().startswith('SELECT'):
            raise Exception(f"Query must start with SELECT. Got: {clean_query[:50]}...")
        
        # Remove trailing semicolon if present
        clean_query = clean_query.rstrip(';')
        
        return clean_query

    def _extract_sql_from_text(self, text: str) -> str:
        """Extract SQL query from AI response text - FIXED VERSION"""
        print(f"=== EXTRACTING SQL FROM ===")
        print(f"Raw AI Response: {text}")
        print("=== END RAW RESPONSE ===")
        
        # Method 1: Look for SQL in code blocks
        code_block_pattern = r'```(?:sql)?\s*(SELECT.*?)```'
        code_match = re.search(code_block_pattern, text, re.DOTALL | re.IGNORECASE)
        if code_match:
            sql = code_match.group(1).strip()
            print(f"Found SQL in code block: {sql}")
            return self._clean_extracted_sql(sql)
        
        # Method 2: Look for SELECT statement anywhere in text
        select_pattern = r'(SELECT\s+.*?)(?:\n\n|\n$|$)'
        select_match = re.search(select_pattern, text, re.DOTALL | re.IGNORECASE)
        if select_match:
            sql = select_match.group(1).strip()
            print(f"Found SELECT statement: {sql}")
            return self._clean_extracted_sql(sql)
        
        # Method 3: Line-by-line extraction for multiline queries
        lines = text.split('\n')
        sql_lines = []
        found_select = False
        
        for line in lines:
            line = line.strip()
            if line.upper().startswith('SELECT'):
                found_select = True
                sql_lines.append(line)
            elif found_select and line and not line.startswith('```'):
                # Continue collecting SQL lines
                if any(keyword in line.upper() for keyword in ['FROM', 'WHERE', 'JOIN', 'GROUP BY', 'ORDER BY', 'LIMIT', 'HAVING']):
                    sql_lines.append(line)
                elif line.endswith(';') or line.endswith(','):
                    sql_lines.append(line)
                    break
                else:
                    # Stop if we hit a non-SQL line
                    break
        
        if sql_lines:
            sql = ' '.join(sql_lines)
            print(f"Found multiline SQL: {sql}")
            return self._clean_extracted_sql(sql)
        
        # If nothing found, return the original text and let validation catch it
        print(f"No SQL pattern found, returning original: {text}")
        return text.strip()

    def _clean_extracted_sql(self, sql: str) -> str:
        """Clean extracted SQL and ensure it's valid"""
        # Remove code block markers if any remain
        sql = re.sub(r'```(?:sql)?', '', sql)
        
        # Normalize whitespace
        sql = ' '.join(sql.split())
        
        # Remove trailing semicolon
        sql = sql.rstrip(';')
        
        # Ensure it starts with SELECT
        if not sql.upper().startswith('SELECT'):
            # Try to find SELECT within the string
            select_match = re.search(r'SELECT\s+.*', sql, re.IGNORECASE)
            if select_match:
                sql = select_match.group(0)
            else:
                raise Exception(f"No valid SELECT statement found in: {sql}")
        
        return sql

    async def generate_sql_from_natural_language(self, question: str, schema: str) -> str:
        """Generate SQL query from natural language question"""

        system_prompt = f"""You are a SQL expert. Generate ONLY a clean SQL SELECT query.

Database Schema:
{schema}

CRITICAL RULES:
1. Return ONLY the SQL query - no explanations, no markdown, no code blocks
2. Use exact table and column names from the schema
3. Start with SELECT (case insensitive is fine)
4. End WITHOUT semicolon
5. Use JOINs, WHERE, ORDER BY, and LIMIT as needed
6. For "best selling" queries: use SUM() or COUNT() with proper GROUP BY

Example format:
SELECT column1, column2 FROM table1 WHERE condition ORDER BY column1 LIMIT 10

Question: {question}"""
        
        messages = [{"role": "user", "content": system_prompt}]
        
        try:
            response = await self.model_manager.generate_response(
                messages=messages,
                system_prompt="",
                max_tokens=200,
                temperature=0.1
            )
            
            # Extract SQL query from response
            sql_query = self._extract_sql_from_text(response)
            
            # DEBUG: Print generated SQL
            print(f"=== GENERATED SQL DEBUG ===")
            print(f"Question: {question}")
            print(f"Generated SQL: {sql_query}")
            print("=== END SQL DEBUG ===")
            
            # Validate that it's a SELECT query
            if not sql_query.upper().startswith('SELECT'):
                raise Exception(f"Generated query is not a SELECT statement: {sql_query}")
            
            return sql_query
                
        except Exception as e:
            print(f"Error in generate_sql_from_natural_language: {str(e)}")
            raise Exception(f"Error generating SQL: {str(e)}")
    
    async def generate_sql_with_retry(self, question: str, schema: str, previous_error: str = None) -> str:
        """Generate SQL with retry logic for column errors"""
        
        retry_prompt = f"""Generate ONLY a clean SQL SELECT query. No explanations.

Database Schema:
{schema}"""
        
        if previous_error:
            retry_prompt += f"""

PREVIOUS ERROR: {previous_error}
Fix the column names using ONLY what exists in the schema above.
"""
        
        retry_prompt += f"""

Rules:
- Return only SQL query
- No markdown, no code blocks
- Use exact column names from schema
- Start with SELECT
- No trailing semicolon

Question: {question}"""
        
        messages = [{"role": "user", "content": retry_prompt}]
        
        try:
            response = await self.model_manager.generate_response(
                messages=messages,
                system_prompt="",
                max_tokens=200,
                temperature=0.05
            )
            
            sql_query = self._extract_sql_from_text(response)
            
            print(f"=== RETRY GENERATED SQL ===")
            print(f"Retry SQL: {sql_query}")
            print("=== END RETRY SQL ===")
            
            if not sql_query.upper().startswith('SELECT'):
                raise Exception(f"Retry query is not a SELECT statement: {sql_query}")
            
            return sql_query
                
        except Exception as e:
            raise Exception(f"Error in retry SQL generation: {str(e)}")
    
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
    Main function to run chat agent with retry logic
    
    Args:
        question: Natural language question about the database
        
    Returns:
        Formatted response with query results
    """
    agent = ChatAgent()
    
    try:
        # Get database schema
        schema = await agent.get_database_schema()
        
        # Check if schema retrieval failed
        if schema.startswith("Error getting schema"):
            return f"Database connection error: {schema}"
        
        # Generate SQL from natural language
        sql_query = await agent.generate_sql_from_natural_language(question, schema)
        
        # Execute the query
        try:
            result = await agent.execute_sql_query(sql_query)
        except Exception as execute_error:
            error_msg = str(execute_error)
            print(f"First attempt failed: {error_msg}")
            
            # Check if it's a column not found error
            if "does not exist" in error_msg or "column" in error_msg.lower():
                print("Attempting retry with error context...")
                try:
                    # Retry with error context
                    retry_sql = await agent.generate_sql_with_retry(question, schema, error_msg)
                    result = await agent.execute_sql_query(retry_sql)
                    sql_query = retry_sql  # Update for display
                except Exception as retry_error:
                    return f"Error processing your question: {str(retry_error)}\n\nOriginal error: {error_msg}\n\nGenerated SQL: `{sql_query}`\n\nPlease check the database schema and try rephrasing your question."
            else:
                # Return error to UI instead of raising
                return f"Error executing query: {error_msg}\n\nGenerated SQL: `{sql_query}`\n\nPlease try rephrasing your question."
        
        # Format and return response
        return await agent.format_query_response(question, sql_query, result)
        
    except Exception as e:
        error_msg = str(e)
        print(f"Final error in run_agent: {error_msg}")
        # Return error message to UI instead of raising
        return f"Error processing your question: {error_msg}\n\nPlease try rephrasing your question or check the database connection."