"""JSON validation utilities for dashboard data"""

import json
import re
from typing import Dict, Any, Optional

def clean_json(json_str: str) -> str:
    """
    Clean JSON string by removing markdown formatting and extra characters
    
    Args:
        json_str: Raw JSON string that may contain markdown
        
    Returns:
        Cleaned JSON string
    """
    # Remove markdown code blocks
    json_str = re.sub(r'```json\s*', '', json_str)
    json_str = re.sub(r'```\s*$', '', json_str)
    
    # Remove any trailing/leading whitespace
    json_str = json_str.strip()
    
    # Try to find JSON object boundaries
    start_idx = json_str.find('{')
    end_idx = json_str.rfind('}')
    
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        json_str = json_str[start_idx:end_idx + 1]
    
    return json_str

def validate_dashboard_json(json_str: str) -> Optional[Dict[str, Any]]:
    """
    Validate and parse dashboard JSON
    
    Args:
        json_str: JSON string to validate
        
    Returns:
        Parsed JSON object if valid, None otherwise
    """
    try:
        # Clean the JSON first
        cleaned_json = clean_json(json_str)
        
        # Parse JSON
        data = json.loads(cleaned_json)
        
        # Basic validation - ensure required fields exist
        required_fields = ['title', 'sections']
        for field in required_fields:
            if field not in data:
                print(f"Missing required field: {field}")
                return None
        
        # Validate sections
        if not isinstance(data['sections'], list):
            print("Sections must be a list")
            return None
        
        for i, section in enumerate(data['sections']):
            if not isinstance(section, dict):
                print(f"Section {i} must be an object")
                return None
            
            if 'title' not in section:
                print(f"Section {i} missing title")
                return None
        
        return data
        
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        return None
    except Exception as e:
        print(f"Validation error: {e}")
        return None

def create_default_dashboard_structure() -> Dict[str, Any]:
    """Create a default dashboard structure"""
    return {
        "title": "Database Dashboard",
        "description": "Overview of database metrics and data",
        "sections": [
            {
                "title": "Key Metrics",
                "type": "metrics",
                "content": []
            },
            {
                "title": "Data Tables",
                "type": "table",
                "content": []
            }
        ]
    }
