import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def create_sample_data():
    """Create sample tables and data for testing"""
    
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USERNAME'),
        password=os.getenv('DB_PASSWORD')
    )
    
    cursor = conn.cursor()
    
    # Create customers table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS customers (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        email VARCHAR(100) UNIQUE NOT NULL,
        city VARCHAR(50),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    # Create products table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        category VARCHAR(50) NOT NULL,
        price DECIMAL(10,2) NOT NULL
    );
    """)
    
    # Create orders table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id SERIAL PRIMARY KEY,
        customer_id INTEGER REFERENCES customers(id),
        product_name VARCHAR(100) NOT NULL,
        quantity INTEGER NOT NULL,
        price DECIMAL(10,2) NOT NULL,
        order_date DATE DEFAULT CURRENT_DATE
    );
    """)
    
    # Insert sample customers
    cursor.execute("""
    INSERT INTO customers (name, email, city) VALUES
    ('John Doe', 'john@example.com', 'New York'),
    ('Jane Smith', 'jane@example.com', 'Los Angeles'),
    ('Bob Johnson', 'bob@example.com', 'Chicago'),
    ('Alice Brown', 'alice@example.com', 'Houston')
    ON CONFLICT (email) DO NOTHING;
    """)
    
    # Insert sample products
    cursor.execute("""
    INSERT INTO products (name, category, price) VALUES
    ('Laptop', 'Electronics', 999.99),
    ('Mouse', 'Electronics', 25.50),
    ('Keyboard', 'Electronics', 75.00),
    ('Monitor', 'Electronics', 299.99),
    ('Headphones', 'Electronics', 149.99),
    ('Tablet', 'Electronics', 399.99)
    ON CONFLICT DO NOTHING;
    """)
    
    # Insert sample orders
    cursor.execute("""
    INSERT INTO orders (customer_id, product_name, quantity, price) VALUES
    (1, 'Laptop', 1, 999.99),
    (1, 'Mouse', 2, 25.50),
    (2, 'Keyboard', 1, 75.00),
    (3, 'Monitor', 1, 299.99),
    (2, 'Headphones', 1, 149.99),
    (4, 'Tablet', 1, 399.99)
    ON CONFLICT DO NOTHING;
    """)
    
    conn.commit()
    cursor.close()
    conn.close()
    print("Sample data created successfully!")

if __name__ == "__main__":
    create_sample_data()