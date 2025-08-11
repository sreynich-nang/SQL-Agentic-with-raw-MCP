# utils/display.py
"""Display utilities for HTML dashboards"""

import streamlit as st
import streamlit.components.v1 as components
from typing import Optional

def display_html_dashboard(html_content: str, height: int = 600) -> None:
    """
    Display HTML dashboard in Streamlit
    
    Args:
        html_content: HTML content to display
        height: Height of the display area in pixels
    """
    try:
        # Clean up the HTML content
        if html_content.strip().startswith('```html'):
            html_content = html_content.replace('```html', '').replace('```', '').strip()
        
        # Add basic styling if not present
        if '<style>' not in html_content and '<link' not in html_content:
            html_content = f"""
            <style>
                body {{ 
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                    margin: 20px;
                    background-color: #f8f9fa;
                }}
                .dashboard-container {{ 
                    background: white; 
                    padding: 20px; 
                    border-radius: 8px; 
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                h1, h2, h3 {{ color: #333; }}
                table {{ 
                    width: 100%; 
                    border-collapse: collapse; 
                    margin: 20px 0;
                }}
                th, td {{ 
                    padding: 12px; 
                    text-align: left; 
                    border-bottom: 1px solid #ddd;
                }}
                th {{ 
                    background-color: #f8f9fa; 
                    font-weight: bold;
                }}
                .metric {{ 
                    display: inline-block; 
                    margin: 10px; 
                    padding: 15px; 
                    background: #e3f2fd; 
                    border-radius: 5px;
                    text-align: center;
                }}
                .metric-value {{ 
                    font-size: 24px; 
                    font-weight: bold; 
                    color: #1976d2;
                }}
                .metric-label {{ 
                    font-size: 14px; 
                    color: #666; 
                    margin-top: 5px;
                }}
            </style>
            <div class="dashboard-container">
            {html_content}
            </div>
            """
        
        # Display the HTML
        components.html(html_content, height=height, scrolling=True)
        
    except Exception as e:
        st.error(f"Error displaying dashboard: {str(e)}")
        st.code(html_content, language='html')

def format_sql_result(data: list, columns: list) -> str:
    """
    Format SQL query results as HTML table
    
    Args:
        data: List of rows from SQL query
        columns: List of column names
        
    Returns:
        HTML formatted table
    """
    if not data:
        return "<p>No data found.</p>"
    
    html = "<table class='sql-results'>"
    html += "<thead><tr>"
    for col in columns:
        html += f"<th>{col}</th>"
    html += "</tr></thead>"
    
    html += "<tbody>"
    for row in data:
        html += "<tr>"
        for value in row:
            html += f"<td>{value if value is not None else ''}</td>"
        html += "</tr>"
    html += "</tbody></table>"
    
    return html

def create_metric_card(title: str, value: str, description: Optional[str] = None) -> str:
    """
    Create a metric card HTML element
    
    Args:
        title: Metric title
        value: Metric value
        description: Optional description
        
    Returns:
        HTML metric card
    """
    desc_html = f"<div class='metric-label'>{description}</div>" if description else ""
    
    return f"""
    <div class="metric">
        <div class="metric-value">{value}</div>
        <div class="metric-label">{title}</div>
        {desc_html}
    </div>
    """