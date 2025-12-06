"""Script to create the database if it doesn't exist."""
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os
from dotenv import load_dotenv

load_dotenv()

# Get connection string from .env or use default
database_url = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/postgres"
)

# Parse the connection string to get components
# Format: postgresql://user:password@host:port/database
try:
    # Extract database name and create connection to 'postgres' database
    if "@" in database_url:
        parts = database_url.split("@")
        auth_part = parts[0].replace("postgresql://", "")
        user_pass = auth_part.split(":")
        user = user_pass[0]
        password = user_pass[1] if len(user_pass) > 1 else ""
        
        server_part = parts[1]
        if "/" in server_part:
            server_db = server_part.split("/")
            server = server_db[0]
            db_name = server_db[1] if len(server_db) > 1 else "postgres"
        else:
            server = server_part
            db_name = "postgres"
        
        if ":" in server:
            host_port = server.split(":")
            host = host_port[0]
            port = host_port[1] if len(host_port) > 1 else "5432"
        else:
            host = server
            port = "5432"
    else:
        raise ValueError("Invalid database URL format")
    
    # Connect to PostgreSQL server (using 'postgres' database)
    conn = psycopg2.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database="postgres"  # Connect to default postgres database
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    
    cursor = conn.cursor()
    
    # Check if database exists
    cursor.execute(
        "SELECT 1 FROM pg_database WHERE datname = 'university_scraper_db'"
    )
    exists = cursor.fetchone()
    
    if not exists:
        # Create database
        cursor.execute('CREATE DATABASE university_scraper_db')
        print("✓ Database 'university_scraper_db' created successfully!")
    else:
        print("✓ Database 'university_scraper_db' already exists!")
    
    cursor.close()
    conn.close()
    
    print("\nNow you can run:")
    print("  python -c \"from app.database import init_db; init_db()\"")
    print("  uvicorn app.main:app --reload")
    
except Exception as e:
    print(f"Error: {e}")
    print("\nPlease create the database manually:")
    print("1. Open pgAdmin or psql")
    print("2. Run: CREATE DATABASE university_scraper_db;")
    print("\nOr update the .env file with correct PostgreSQL credentials.")

