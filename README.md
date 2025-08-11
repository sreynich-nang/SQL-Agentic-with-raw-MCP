# AI SQL Dashboard Agent

A complete AI-powered SQL dashboard system that converts natural language questions into SQL queries and generates interactive dashboards. Built with Streamlit, PostgreSQL, and MCP (Model Context Protocol).

## Video Demonstration
[Watch the Video](https://)

## 🚀 Features

- **Natural Language Queries**: Ask questions in plain English, get SQL results
- **Auto Dashboard Generation**: AI analyzes your database structure and creates visualizations
- **Secure Database Access**: Read-only access through MCP server layer
- **Multi-Model Support**: OpenAI GPT, Anthropic Claude, or Groq models
- **Interactive UI**: Modern Streamlit interface with chat and dashboard tabs

## 📁 Project Structure

```
ai_sql_dashboard/
├── app.py                   # Streamlit main application
├── agents/
│   ├── __init__.py
│   ├── chat_agent.py        # Natural language to SQL conversion
│   ├── dashboard_agent.py   # Dashboard generation logic
│   ├── model_utils.py       # LLM model management
│   └── validation.py        # JSON validation utilities
├── mcp_server/
│   ├── __init__.py
│   ├── sql_read_only.py     # MCP SQL server implementation
│   └── tools.py             # Database tool handlers
├── utils/
│   ├── __init__.py
│   ├── display.py           # HTML display utilities
│   └── env_utils.py         # Environment management
├── requirements.txt
├── .env.example
├── setup_db.py             # Database setup script
├── LICENSE 
└── README.md
```

## 🛠️ Installation & Setup

### 1. Clone and Setup Environment

```bash
# Clone the repository (or create the directory structure)
mkdir ai_sql_dashboard
cd ai_sql_dashboard

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. PostgreSQL Database Setup

#### Option A: Local PostgreSQL Installation

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib

# macOS with Homebrew
brew install postgresql
brew services start postgresql

# Windows
# Download and install from: https://www.postgresql.org/download/windows/
```

#### Option B: Docker PostgreSQL (Recommended for testing)

```bash
# Run PostgreSQL in Docker
docker run --name ai-dashboard-postgres \
  -e POSTGRES_DB=ai_dashboard_db \
  -e POSTGRES_USER=dashboard_user \
  -e POSTGRES_PASSWORD=your_password_here \
  -p 5432:5432 \
  -d postgres:15

# Wait a few seconds for container to start
docker ps
```

#### Create Database and User (if using local installation)

```bash
# Connect to PostgreSQL as superuser
sudo -u postgres psql

# Create database and user
CREATE DATABASE ai_dashboard_db;
CREATE USER dashboard_user WITH PASSWORD 'your_password_here';
GRANT ALL PRIVILEGES ON DATABASE ai_dashboard_db TO dashboard_user;
\q
```

### 3. Environment Configuration

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your configuration
nano .env
```

#### .env Configuration

```bash
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_USERNAME=dashboard_user
DB_PASSWORD=your_password_here
DB_NAME=ai_dashboard_db

# LLM Configuration

MODEL_ID=gemini-1.5-flash
MODEL_API_KEY=api_key_here_from_gemini

# MCP Server Configuration
MCP_SERVER_HOST=localhost
MCP_SERVER_PORT=8000
```

### 4. Database Initialization

```bash
# Run the database setup script to create sample data
python setup_db.py
```

This creates sample `customers` and `orders` tables with test data.

### 5. API Keys Setup

#### Google Gemini 
1. Go to https://aistudio.google.com/app/apikey
2. Create a new API key
3. Add to .env as `MODEL_API_KEY`

## 🚀 Running the Application

### Step 1: Start MCP Server

In terminal 1:
```bash
cd ai_sql_dashboard
source venv/bin/activate
python -m mcp_server.sql_read_only
```

You should see:
```
Database connection pool initialized
MCP SQL Server started on http://localhost:8000
```

### Step 2: Start Streamlit App

In terminal 2:
```bash
cd ai_sql_dashboard
source venv/bin/activate
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## 📋 Testing

### Test 1: MCP Server Health Check

```bash
curl http://localhost:8000/health
# Should return: {"status": "healthy"}
```

### Test 2: Chat Agent (Command Line)

```bash
python -c "
import asyncio
from agents.chat_agent import run_agent
result = asyncio.run(run_agent('How many customers do we have?'))
print(result)
"
```

### Test 3: Dashboard Generation

```bash
python -c "
import asyncio
from agents.dashboard_agent import run_dashboard_agent
html = asyncio.run(run_dashboard_agent())
print('Dashboard generated successfully!' if '<html>' in html else 'Error')
"
```

## 💬 Usage Examples

### Chat Queries
- "How many customers do we have?"
- "What's our total revenue?"
- "Show me the top 2 customers by order value"
- "Which products are selling the best?"
- "What's the average order value?"

### Dashboard Features
- Click "Generate Dashboard" to auto-create visualizations
- AI analyzes your database schema automatically
- Generates metrics, tables, and charts
- Download HTML for sharing

## 🔧 Troubleshooting

### Common Issues

#### 1. "Connection refused" to database
```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql  # Linux
brew services list | grep postgres  # macOS
docker ps  # Docker

# Test connection manually
psql -h localhost -p 5432 -U dashboard_user -d ai_dashboard_db
```

#### 2. "MCP tool call failed"
```bash
# Ensure MCP server is running
python -m mcp_server.sql_read_only

# Check if port 8000 is available
netstat -an | grep 8000
```

#### 3. "No module named 'agents'"
```bash
# Ensure you're in the correct directory
pwd  # Should end with /ai_sql_dashboard

# Check Python path
python -c "import sys; print(sys.path)"
```

#### 4. API Key Issues
```bash
# Verify .env file is loaded
python -c "
from dotenv import load_dotenv
import os
load_dotenv()
print('API Key:', os.getenv('MODEL_API_KEY')[:10] + '...' if os.getenv('MODEL_API_KEY') else 'Not found')
"
```

#### 5. Streamlit Issues
```bash
# Clear Streamlit cache
streamlit cache clear

# Run with debug mode
streamlit run app.py --logger.level=debug
```

## 🔒 Security Features

- **Read-Only Database Access**: Only SELECT queries allowed
- **SQL Injection Prevention**: Query validation and parameterization
- **Timeout Protection**: 30-second query timeout
- **Schema Validation**: All queries validated against schema
- **No Data Modification**: CREATE, UPDATE, DELETE, DROP blocked

## 🏗️ Architecture Details

### MCP (Model Context Protocol) Server
- Provides secure database abstraction layer
- Validates all SQL queries for safety
- Manages connection pooling
- Exposes REST API for tool calls

### AI Agents
- **Chat Agent**: Converts natural language to SQL using LLM
- **Dashboard Agent**: Analyzes database schema and generates HTML dashboards
- **Model Manager**: Abstracts different LLM providers (OpenAI, Anthropic, Groq)

### Database Layer
- PostgreSQL with asyncpg for async operations
- Connection pooling for performance
- Schema introspection for AI context

## 📊 Sample Queries Generated

The system can handle complex queries like:

```sql
-- Customer analysis
SELECT c.city, COUNT(*) as customer_count, 
       AVG(o.price * o.quantity) as avg_order_value
FROM customers c 
JOIN orders o ON c.id = o.customer_id 
GROUP BY c.city 
ORDER BY avg_order_value DESC;

-- Revenue trends
SELECT DATE_TRUNC('month', order_date) as month,
       SUM(price * quantity) as monthly_revenue,
       COUNT(*) as order_count
FROM orders 
GROUP BY month 
ORDER BY month;
```

## 🎨 Customization

### Adding New Database Tables
1. Add tables to your PostgreSQL database
2. The schema will be auto-detected
3. AI will automatically include new tables in analysis

### Custom Dashboard Templates
Modify `agents/dashboard_agent.py`:
```python
# Add custom chart types
def generate_custom_chart(self, data):
    # Your custom visualization logic
    pass
```

### Different LLM Models
Update `.env` file:
```bash
# For different OpenAI models
MODEL_ID=gpt-3.5-turbo  # Faster, cheaper
MODEL_ID=gpt-4          # More accurate

# For different Claude models  
MODEL_ID=claude-3-haiku-20240307    # Fastest
MODEL_ID=claude-3-sonnet-20240229   # Balanced
MODEL_ID=claude-3-opus-20240229     # Most capable
```

## 📈 Performance Tips

### Database Optimization
```sql
-- Add indexes for better performance
CREATE INDEX idx_orders_customer_id ON orders(customer_id);
CREATE INDEX idx_orders_date ON orders(order_date);
CREATE INDEX idx_customers_city ON customers(city);
```

### MCP Server Tuning
```python
# In mcp_server/tools.py, adjust connection pool
self.connection_pool = await asyncpg.create_pool(
    min_size=2,     # Minimum connections
    max_size=20,    # Maximum connections  
    command_timeout=60  # Query timeout
)
```

## 🧪 Development

### Adding New Features

1. **New Chat Commands**: Modify `agents/chat_agent.py`
2. **Dashboard Widgets**: Update `agents/dashboard_agent.py`
3. **Database Tools**: Extend `mcp_server/tools.py`

### Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/new-feature`
3. Commit changes: `git commit -am 'Add new feature'`
4. Push to branch: `git push origin feature/new-feature`
5. Submit pull request

## 📄 License

MIT License - see LICENSE file for details.

## 🆘 Support

### Get Help
- Check troubleshooting section above
- Review logs in terminal output
- Test each component individually

### Common Support Questions

**Q: Can I use with MySQL instead of PostgreSQL?**
A: Yes, modify `mcp_server/tools.py` to use `aiomysql` instead of `asyncpg`

**Q: How do I add more sample data?**
A: Modify `setup_db.py` and run it again

**Q: Can I deploy this to production?**
A: Yes, but add proper authentication, rate limiting, and security headers

**Q: How do I backup my data?**
A: Use `pg_dump` for PostgreSQL backups:
```bash
pg_dump -h localhost -U dashboard_user ai_dashboard_db > backup.sql
```

---

## 🎯 Quick Start Summary

1. **Install**: `pip install -r requirements.txt`
2. **Database**: Setup PostgreSQL and run `python setup_db.py` 
3. **Config**: Copy `.env.example` to `.env` and add API keys
4. **Run**: `python -m mcp_server.sql_read_only` then `streamlit run app.py`
5. **Test**: Ask "How many customers do we have?" in the chat

---

**Created with using Streamlit, PostgreSQL, and MCP Protocol**