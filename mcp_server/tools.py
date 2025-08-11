"""Database tool handlers for MCP server"""

import asyncio
import asyncpg
from typing import Dict, List, Any, Optional
import re
import os
from utils.env_utils import get_db_config

class DatabaseTools:
    """Database tool handlers for schema and query operations"""
    
    def __init__(self):
        self.connection_pool: Optional[asyncpg.Pool] = None
    
    async def initialize(self):
        """Initialize database connection pool"""
        try:
            db_config = get_db_config()
            self.connection_pool = await asyncpg.create_pool(
                host=db_config['DB_HOST'],
                port=int(db_config['DB_PORT']),
                user=db_config['DB_USERNAME'],
                password=db_config['DB_PASSWORD'],
                database=db_config['DB_NAME'],
                min_size=1,
                max_size=10
            )
            print("Database connection pool initialized")
        except Exception as e:
            print(f"Failed to initialize database: {e}")
            raise
    
    async def close(self):
        """Close database connection pool"""
        if self.connection_pool:
            await self.connection_pool.close()
    
    async def get_schema(self) -> Dict[str, Any]:
        """
        Get database schema information for LLM context
        
        Returns:
            Dictionary containing schema information
        """
        if not self.connection_pool:
            await self.initialize()
        
        try:
            async with self.connection_pool.acquire() as conn:
                # Get all tables
                tables_query = """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                ORDER BY table_name;
                """
                
                tables = await conn.fetch(tables_query)
                schema_info = {"tables": {}}
                
                for table_row in tables:
                    table_name = table_row['table_name']
                    
                    # Get columns for each table
                    columns_query = """
                    SELECT 
                        column_name,
                        data_type,
                        is_nullable,
                        column_default
                    FROM information_schema.columns 
                    WHERE table_name = $1 
                    AND table_schema = 'public'
                    ORDER BY ordinal_position;
                    """
                    
                    columns = await conn.fetch(columns_query, table_name)
                    
                    # Get foreign keys
                    fk_query = """
                    SELECT
                        kcu.column_name,
                        ccu.table_name AS foreign_table_name,
                        ccu.column_name AS foreign_column_name
                    FROM information_schema.table_constraints AS tc
                    JOIN information_schema.key_column_usage AS kcu
                        ON tc.constraint_name = kcu.constraint_name
                    JOIN information_schema.constraint_column_usage AS ccu
                        ON ccu.constraint_name = tc.constraint_name
                    WHERE tc.constraint_type = 'FOREIGN KEY'
                    AND tc.table_name = $1;
                    """
                    
                    foreign_keys = await conn.fetch(fk_query, table_name)
                    
                    schema_info["tables"][table_name] = {
                        "columns": [
                            {
                                "name": col['column_name'],
                                "type": col['data_type'],
                                "nullable": col['is_nullable'] == 'YES',
                                "default": col['column_default']
                            } for col in columns
                        ],
                        "foreign_keys": [
                            {
                                "column": fk['column_name'],
                                "references_table": fk['foreign_table_name'],
                                "references_column": fk['foreign_column_name']
                            } for fk in foreign_keys
                        ]
                    }
                
                return schema_info
                
        except Exception as e:
            print(f"Error getting schema: {e}")
            raise
    
    def _validate_query(self, query: str) -> bool:
        """
        Validate that query is safe (SELECT only, no modifications)
        
        Args:
            query: SQL query to validate
            
        Returns:
            True if query is safe, False otherwise
        """
        # Remove comments and normalize whitespace
        query_clean = re.sub(r'--.*$', '', query, flags=re.MULTILINE)
        query_clean = re.sub(r'/\*.*?\*/', '', query_clean, flags=re.DOTALL)
        query_clean = ' '.join(query_clean.split()).strip().lower()
        
        # Must start with SELECT
        if not query_clean.startswith('select'):
            return False
        
        # Forbidden keywords
        forbidden = [
            'insert', 'update', 'delete', 'drop', 'create', 'alter',
            'truncate', 'replace', 'merge', 'grant', 'revoke',
            'exec', 'execute', 'call', 'declare'
        ]
        
        for keyword in forbidden:
            if keyword in query_clean:
                return False
        
        return True
    
    async def execute_query(self, query: str) -> Dict[str, Any]:
        """
        Execute a read-only SQL query
        
        Args:
            query: SQL SELECT query to execute
            
        Returns:
            Dictionary with columns and data
        """
        if not self.connection_pool:
            await self.initialize()
        
        # Validate query safety
        if not self._validate_query(query):
            raise ValueError("Query validation failed. Only SELECT queries are allowed.")
        
        try:
            async with self.connection_pool.acquire() as conn:
                # Execute query with timeout
                result = await asyncio.wait_for(
                    conn.fetch(query),
                    timeout=30.0  # 30 second timeout
                )
                
                if not result:
                    return {"columns": [], "data": []}
                
                # Get column names
                columns = list(result[0].keys()) if result else []
                
                # Convert rows to list of lists
                data = [list(row.values()) for row in result]
                
                return {
                    "columns": columns,
                    "data": data,
                    "row_count": len(data)
                }
                
        except asyncio.TimeoutError:
            raise Exception("Query timeout - query took longer than 30 seconds")
        except Exception as e:
            print(f"Error executing query: {e}")
            raise

