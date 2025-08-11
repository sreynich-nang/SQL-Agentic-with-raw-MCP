"""MCP SQL Server implementation for secure database access"""

import asyncio
import json
from typing import Dict, Any
from aiohttp import web, web_request
from .tools import DatabaseTools

class SqlReadOnlyServer:
    """
    MCP-compatible SQL server that provides read-only access to database
    """
    
    def __init__(self, host: str = "localhost", port: int = 8000):
        self.host = host
        self.port = port
        self.app = web.Application()
        self.db_tools = DatabaseTools()
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup HTTP routes for MCP protocol"""
        self.app.router.add_post('/mcp/tools/list', self.list_tools)
        self.app.router.add_post('/mcp/tools/call', self.call_tool)
        self.app.router.add_get('/health', self.health_check)
    
    async def health_check(self, request: web_request.Request) -> web.Response:
        """Health check endpoint"""
        return web.json_response({"status": "healthy"})
    
    async def list_tools(self, request: web_request.Request) -> web.Response:
        """List available tools"""
        tools = [
            {
                "name": "get_schema",
                "description": "Get database schema information including tables, columns, and relationships",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "read_query",
                "description": "Execute a read-only SQL SELECT query on the database",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "SQL SELECT query to execute"
                        }
                    },
                    "required": ["query"]
                }
            }
        ]
        
        return web.json_response({"tools": tools})
    
    async def call_tool(self, request: web_request.Request) -> web.Response:
        """Call a specific tool"""
        try:
            data = await request.json()
            tool_name = data.get("name")
            arguments = data.get("arguments", {})
            
            if tool_name == "get_schema":
                result = await self.db_tools.get_schema()
                return web.json_response({
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, indent=2)
                        }
                    ]
                })
            
            elif tool_name == "read_query":
                query = arguments.get("query")
                if not query:
                    return web.json_response(
                        {"error": "Query parameter is required"},
                        status=400
                    )
                
                result = await self.db_tools.execute_query(query)
                return web.json_response({
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, indent=2, default=str)
                        }
                    ]
                })
            
            else:
                return web.json_response(
                    {"error": f"Unknown tool: {tool_name}"},
                    status=400
                )
                
        except Exception as e:
            return web.json_response(
                {"error": str(e)},
                status=500
            )
    
    async def start(self):
        """Start the MCP server"""
        await self.db_tools.initialize()
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        print(f"MCP SQL Server started on http://{self.host}:{self.port}")
    
    async def stop(self):
        """Stop the MCP server"""
        await self.db_tools.close()

async def run_server():
    """Run the MCP server"""
    from utils.env_utils import load_env
    load_env()
    
    server = SqlReadOnlyServer()
    await server.start()
    
    try:
        # Keep the server running
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down MCP server...")
        await server.stop()

if __name__ == "__main__":
    asyncio.run(run_server())