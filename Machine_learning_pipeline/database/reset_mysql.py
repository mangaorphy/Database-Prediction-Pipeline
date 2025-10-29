"""
Reset MySQL database by dropping and recreating it.
"""
import pymysql
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from config.database import MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD

def reset_database():
    """Drop and recreate the agriculture_db database."""
    print("Connecting to MySQL...")
    
    # Connect without specifying database
    connection = pymysql.connect(
        host=MYSQL_HOST,
        port=int(MYSQL_PORT),
        user=MYSQL_USER,
        password=MYSQL_PASSWORD
    )
    
    cursor = connection.cursor()
    
    print("Dropping existing database...")
    cursor.execute("DROP DATABASE IF EXISTS agriculture_db")
    
    print("Creating new database...")
    cursor.execute("CREATE DATABASE agriculture_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    
    print("Switching to agriculture_db...")
    cursor.execute("USE agriculture_db")
    
    # Read and execute the schema file
    schema_file = Path(__file__).parent / 'mysql_schema.sql'
    
    print(f"Reading schema from {schema_file}...")
    with open(schema_file, 'r') as f:
        schema_sql = f.read()
    
    # Split by semicolon and execute each statement
    statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip()]
    
    print("Executing schema statements...")
    for i, statement in enumerate(statements):
        # Skip DROP DATABASE and CREATE DATABASE as we already did that
        if 'DROP DATABASE' in statement or 'CREATE DATABASE' in statement or statement.startswith('USE '):
            continue
        
        try:
            cursor.execute(statement)
            print(f"  ✓ Statement {i+1}/{len(statements)}")
        except Exception as e:
            print(f"  ✗ Error in statement {i+1}: {e}")
    
    connection.commit()
    cursor.close()
    connection.close()
    
    print("\n✓ Database reset complete!\n")

if __name__ == '__main__':
    reset_database()
